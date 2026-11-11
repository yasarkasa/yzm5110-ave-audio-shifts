"""Read three AVE validation clips and run Tian et al.'s published A+V-att weights."""

import argparse
from collections import OrderedDict, defaultdict
import hashlib
import io
import json
import pickle
from pathlib import Path
from types import ModuleType, SimpleNamespace
from urllib.request import Request, urlopen
import warnings

import h5py
import numpy as np


LOCAL = Path(__file__).resolve().parents[1] / ".ave-local"
UPSTREAM = LOCAL / "upstream"
SAMPLE = LOCAL / "validation_sample.npz"
FEATURES = {
    "audio": ("1F6p4BAOY-i0fDXUOhG7xHuw_fnO5exBS", 42426464, (4143, 10, 128)),
    "visual": ("1hQwbhutA3fQturduRnHMyfRqdrRHgmC9", 8315168864, (4143, 10, 7, 7, 512)),
}
CHECKPOINT_SHA256 = "35a1dc17abf03652e686ae354424539e6fdf5ee463b6f27c91d7e0b35ab3865c"
MODEL_SOURCE_SHA256 = "6a0763a4c8fbd6612ce5053159e18071bccef05d31c45557cd9f53e5a0b3f718"


def read_annotations():
    path = UPSTREAM / "data/Annotations.txt"
    return [line.split("&") for line in path.read_text().splitlines()]


def split_indices(split):
    with h5py.File(UPSTREAM / f"data/{split}_order.h5", "r") as file:
        return file["order"][:].reshape(-1)


def validation_rows(annotations):
    selected = {}
    for row in split_indices("val"):
        category, _, _, start, end = annotations[row]
        start, end = int(start), int(end)
        if 0 < end - start < 10:
            selected.setdefault(category, row)
        if len(selected) == 3:
            return np.array(list(selected.values()))
    raise ValueError("Expected three validation categories with an event and background")


def fetch_sample():
    rows = validation_rows(read_annotations())
    samples = {"rows": rows}
    for name, (file_id, size, shape) in FEATURES.items():
        url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
        local_file = LOCAL / f"{name}_feature.h5"
        with local_file.open("rb") if local_file.is_file() else RangeFile(url, size) as stream:
            with h5py.File(stream, "r") as file:
                dataset = file["avadataset"]
                if dataset.shape != shape:
                    raise ValueError(f"Unexpected {name} dataset shape: {dataset.shape}")
                samples[name] = np.stack([dataset[int(row)] for row in rows])
    partial = SAMPLE.with_suffix(".part.npz")
    np.savez(partial, **samples)
    partial.replace(SAMPLE)
    print(f"Saved AVE feature rows {rows.tolist()} to {SAMPLE}")


class RangeFile(io.RawIOBase):
    """A small seekable reader that rejects a mismatched HTTP byte range."""

    def __init__(self, url, size):
        self.url = url
        self.size = size
        self.position = 0
        self.header = self.fetch(0, 4095)

    def fetch(self, start, end):
        request = Request(
            f"{self.url}&ave_range={start}-{end}",
            headers={"Range": f"bytes={start}-{end}", "Accept-Encoding": "identity"},
        )
        with urlopen(request, timeout=30) as response:
            expected = f"bytes {start}-{end}/{self.size}"
            if response.status != 206 or response.headers.get("Content-Range") != expected:
                raise OSError(f"Expected HTTP 206 with Content-Range: {expected}")
            data = response.read(end - start + 2)
        if len(data) != end - start + 1:
            raise OSError("Unexpected HTTP range length")
        return data

    def readable(self):
        return True

    def seekable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=io.SEEK_SET):
        base = {io.SEEK_SET: 0, io.SEEK_CUR: self.position, io.SEEK_END: self.size}
        self.position = base[whence] + offset
        return self.position

    def readinto(self, buffer):
        start, end = self.position, min(self.size, self.position + len(buffer))
        if start >= end:
            return 0
        data = self.header[start:end] if end <= len(self.header) else self.fetch(start, end - 1)
        buffer[:len(data)] = data
        self.position = end
        return len(data)


class LegacyRecord:
    """Hold checkpoint attributes without instantiating legacy PyTorch modules."""

    dump_patches = False

    def __setstate__(self, state):
        if isinstance(state, dict):
            self.__dict__.update(state)


def obsolete_backend():
    return None


def checkpoint_parameters(record, prefix=""):
    for name, tensor in record._parameters.items():
        if tensor is not None:
            yield prefix + name, tensor
    for name, child in record._modules.items():
        yield from checkpoint_parameters(child, prefix + name + ".")


def load_model(torch):
    checkpoint = UPSTREAM / "model/AV_att.pt"
    if hashlib.sha256(checkpoint.read_bytes()).hexdigest() != CHECKPOINT_SHA256:
        raise ValueError("The checkpoint does not match the inspected upstream AV_att.pt")
    allowed = {
        ("models", "att_Net"): LegacyRecord,
        ("torch.nn.modules.rnn", "LSTM"): LegacyRecord,
        ("torch.nn.modules.linear", "Linear"): LegacyRecord,
        ("torch.nn.modules.activation", "ReLU"): LegacyRecord,
        ("torch.backends.cudnn.rnn", "Unserializable"): LegacyRecord,
        ("torch.nn.backends.thnn", "_get_thnn_function_backend"): obsolete_backend,
        ("collections", "OrderedDict"): OrderedDict,
        ("torch.nn.parameter", "Parameter"): torch.nn.Parameter,
        ("torch._utils", "_rebuild_tensor"): torch._utils._rebuild_tensor,
    }

    class CheckpointUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if (module, name) not in allowed:
                raise pickle.UnpicklingError(f"Unexpected checkpoint object: {module}.{name}")
            return allowed[module, name]

    reader = SimpleNamespace(
        __name__="ave_checkpoint",
        Unpickler=CheckpointUnpickler,
        load=lambda stream, **kwargs: CheckpointUnpickler(stream, **kwargs).load(),
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", torch.serialization.SourceChangeWarning)
        warnings.filterwarnings("ignore", message="Couldn't retrieve source code for container")
        record = torch.load(checkpoint, map_location="cpu", pickle_module=reader, weights_only=False)

    # Execute the pinned upstream implementation with device-aware zero states.
    source = UPSTREAM / "models.py"
    raw_code = source.read_bytes()
    if hashlib.sha256(raw_code).hexdigest() != MODEL_SOURCE_SHA256:
        raise ValueError("The source does not match the inspected upstream models.py")
    code = raw_code.decode()
    old = "torch.zeros(2, audio.size(0), self.hidden_dim).cuda()"
    if code.count(old) != 4:
        raise ValueError("Upstream models.py differs from the expected CPU patch")
    code = code.replace(old, "audio.new_zeros(2, audio.size(0), self.hidden_dim)")
    code = code.replace("init.xavier_uniform(", "init.xavier_uniform_(")
    module = ModuleType("ave_upstream_cpu")
    exec(compile(code, str(source), "exec"), module.__dict__)
    model = module.att_Net(128, 128, 512, 29).cpu().eval()
    model.load_state_dict(dict(checkpoint_parameters(record)), strict=True)
    return model


def run_smoke():
    import torch

    annotations = read_annotations()
    splits = {split: split_indices(split) for split in ("train", "val", "test")}
    np.testing.assert_array_equal(
        np.sort(np.concatenate(list(splits.values()))), np.arange(len(annotations))
    )
    source_splits = defaultdict(set)
    for split, indices in splits.items():
        for row in indices:
            source_splits[annotations[row][1]].add(split)
    with np.load(SAMPLE, allow_pickle=False) as sample:
        rows, audio, visual = (sample[key] for key in ("rows", "audio", "visual"))
    if rows.shape != (3,) or np.unique(rows).size != 3 or not np.isin(rows, splits["val"]).all():
        raise ValueError("Expected three distinct validation rows")
    for name, values in (("audio", audio), ("visual", visual)):
        if values.shape != (len(rows), *FEATURES[name][2][1:]) or not np.isfinite(values).all():
            raise ValueError(f"Invalid {name} sample")
        if not values.reshape(len(rows), -1).any(axis=1).all():
            raise ValueError(f"At least one {name} feature row is entirely zero")

    data = UPSTREAM / "data"
    categories = list(dict.fromkeys(annotation[0] for annotation in annotations))
    category_ids = {name: index for index, name in enumerate(categories)}
    background = len(categories)
    expected = np.full((len(annotations), 10), background)
    for row, (category, _, _, start, end) in enumerate(annotations):
        expected[row, int(start):int(end)] = category_ids[category]
    with h5py.File(data / "labels.h5", "r") as file:
        all_labels = file["avadataset"][:]
    np.testing.assert_array_equal(all_labels.argmax(axis=-1), expected)
    labels = all_labels[rows]
    if labels.shape != (len(rows), 10, 29):
        raise ValueError(f"Unexpected label shape: {labels.shape}")
    np.testing.assert_array_equal(labels.sum(axis=-1), np.ones((len(rows), 10)))
    if not np.isin(labels, (0, 1)).all():
        raise ValueError("Labels must be one-hot")
    target = labels.argmax(axis=-1)

    clips = []
    for row, classes in zip(rows, target):
        category, clip_id, _, start, end = annotations[int(row)]
        clips.append({"row": int(row), "clip_id": clip_id, "category": category,
                      "event_seconds": [int(start), int(end)], "target_class_ids": classes.tolist()})

    model = load_model(torch)
    with torch.inference_mode():
        scores = model(torch.from_numpy(audio).float(), torch.from_numpy(visual).float())
    if tuple(scores.shape) != labels.shape or not torch.isfinite(scores).all():
        raise ValueError("The model did not return a finite score for each segment and class")
    torch.testing.assert_close(scores.sum(dim=-1), torch.ones(scores.shape[:2]))
    for clip, prediction in zip(clips, scores.argmax(dim=-1).tolist()):
        clip["predicted_class_ids"] = prediction
    result = {
        "split": "validation",
        "split_counts": {name: len(indices) for name, indices in splits.items()},
        "source_ids_crossing_splits": sum(len(names) > 1 for names in source_splits.values()),
        "annotation_rows_checked": len(annotations),
        "pytorch": torch.__version__,
        "device": str(scores.device),
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "audio_shape": list(audio.shape),
        "visual_shape": list(visual.shape),
        "label_shape": list(labels.shape),
        "score_shape": list(scores.shape),
        "clips": clips,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Fetch only the three official feature rows")
    if parser.parse_args().fetch:
        fetch_sample()
    else:
        run_smoke()
