"""Evaluate the published A+V-att checkpoint on the original, unshifted AVE test split."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import hashlib
import json
from pathlib import Path
import platform
from tempfile import NamedTemporaryFile

import h5py
import numpy as np

from ave_smoke import (
    CHECKPOINT_SHA256,
    FEATURES,
    LOCAL,
    MODEL_SOURCE_SHA256,
    UPSTREAM,
    RangeFile,
    load_model,
    split_indices,
)


VISUAL_DIR = LOCAL / "visual_test"
VISUAL_DTYPE = np.dtype("<f8")
VISUAL_SHAPE = FEATURES["visual"][2]
ROW_BYTES = int(np.prod(VISUAL_SHAPE[1:])) * VISUAL_DTYPE.itemsize
PUBLISHED_ACCURACY = 72.7
UPSTREAM_REVISION = "93f843fed72fb17394df76330df958b0c2dbde76"


def test_rows():
    rows = split_indices("test")
    if rows.shape != (402,) or np.unique(rows).size != 402 or not (
        (rows >= 0) & (rows < VISUAL_SHAPE[0])
    ).all():
        raise ValueError("Expected the 402 distinct rows of the official AVE test split")
    return rows


def cached_visual(row, directory=VISUAL_DIR):
    path = directory / f"{row}.official"
    return path if path.is_file() and path.stat().st_size == ROW_BYTES else None


def fetch_visual(rows, directory=VISUAL_DIR):
    directory.mkdir(parents=True, exist_ok=True)
    pending = [int(row) for row in rows if cached_visual(row, directory) is None]
    if not pending:
        print(f"All {len(rows)} visual rows are cached.")
        return

    file_id, size, _ = FEATURES["visual"]
    official_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
    with RangeFile(official_url, size) as remote:
        with h5py.File(remote, "r") as file:
            dataset = file["avadataset"]
            offset = dataset.id.get_offset()
            if dataset.shape != VISUAL_SHAPE or dataset.dtype != VISUAL_DTYPE or (
                offset is None or dataset.id.get_storage_size() != VISUAL_SHAPE[0] * ROW_BYTES
                or offset + VISUAL_SHAPE[0] * ROW_BYTES != size
            ):
                raise ValueError("Unexpected visual HDF5 shape, type or layout")
        def download(row):
            start = offset + row * ROW_BYTES
            data = remote.fetch(start, start + ROW_BYTES - 1)
            with NamedTemporaryFile(dir=directory, delete=False) as temp:
                temp.write(data)
            Path(temp.name).replace(directory / f"{row}.official")

        print(f"Fetching {len(pending)} official visual rows.", flush=True)
        with ThreadPoolExecutor(max_workers=12) as pool:
            futures = [pool.submit(download, row) for row in pending]
            try:
                for completed, future in enumerate(as_completed(futures), 1):
                    future.result()
                    if completed % 25 == 0 or completed == len(pending):
                        print(f"Fetched {completed}/{len(pending)} rows.", flush=True)
            finally:
                for future in futures:
                    future.cancel()


def evaluate(rows, batch_size):
    import torch

    audio_official = LOCAL / "audio_feature_official.h5"
    audio_path = audio_official if audio_official.is_file() else LOCAL / "audio_feature.h5"
    audio_origin = "official" if audio_path == audio_official else "LECOO/AVE mirror"
    with h5py.File(audio_path, "r") as file:
        dataset = file["avadataset"]
        if dataset.shape != FEATURES["audio"][2]:
            raise ValueError(f"Unexpected audio HDF5 shape: {dataset.shape}")
        audio = np.stack([dataset[int(row)] for row in rows]).astype(np.float32)
    with h5py.File(UPSTREAM / "data/labels.h5", "r") as file:
        labels = np.stack([file["avadataset"][int(row)] for row in rows])
    if labels.shape != (len(rows), 10, 29) or not np.isin(labels, (0, 1)).all() or (
        labels.sum(axis=-1) != 1
    ).any():
        raise ValueError("Expected one target per segment and 29 classes")
    target = labels.argmax(axis=-1)
    if not np.isfinite(audio).all() or not audio.reshape(len(rows), -1).any(axis=1).all():
        raise ValueError("Invalid or empty audio features")

    torch.set_num_threads(4)
    model = load_model(torch)
    predicted = np.empty_like(target)
    visual_digest = hashlib.sha256()
    with torch.inference_mode():
        for start in range(0, len(rows), batch_size):
            stop = min(start + batch_size, len(rows))
            batch = []
            for row in rows[start:stop]:
                path = cached_visual(row)
                if path is None:
                    raise FileNotFoundError(f"Visual row {row} is missing. Run with --fetch.")
                data = path.read_bytes()
                visual_digest.update(data)
                batch.append(np.frombuffer(data, dtype=VISUAL_DTYPE).reshape(VISUAL_SHAPE[1:]))
            visual = np.stack(batch).astype(np.float32)
            if not np.isfinite(visual).all() or not visual.reshape(len(batch), -1).any(axis=1).all():
                raise ValueError(f"Invalid or empty visual features in rows {rows[start:stop]}")
            scores = model(torch.from_numpy(audio[start:stop]), torch.from_numpy(visual))
            if tuple(scores.shape) != (len(batch), 10, 29) or not torch.isfinite(scores).all():
                raise ValueError(f"Invalid model scores in rows {rows[start:stop]}")
            predicted[start:stop] = scores.argmax(dim=-1).numpy()

    correct = int(np.count_nonzero(predicted == target))
    accuracy = 100 * correct / target.size
    with audio_path.open("rb") as file:
        audio_digest = hashlib.file_digest(file, "sha256").hexdigest()
    result = {
        "model": "A+V-att",
        "split": "official AVE test",
        "audio_shift_seconds": 0,
        "boundary_mask": False,
        "clips": len(rows),
        "segments_per_clip": target.shape[1],
        "segments": target.size,
        "correct_segments": correct,
        "accuracy_percent": accuracy,
        "published_accuracy_percent": PUBLISHED_ACCURACY,
        "difference_percentage_points": accuracy - PUBLISHED_ACCURACY,
        "upstream_revision": UPSTREAM_REVISION,
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "model_source_sha256": MODEL_SOURCE_SHA256,
        "audio_origin": audio_origin,
        "audio_sha256": audio_digest,
        "official_visual_rows": len(rows),
        "visual_sha256_in_test_order": visual_digest.hexdigest(),
        "test_order_sha256": hashlib.sha256((UPSTREAM / "data/test_order.h5").read_bytes()).hexdigest(),
        "labels_sha256": hashlib.sha256((UPSTREAM / "data/labels.h5").read_bytes()).hexdigest(),
        "device": "cpu",
        "batch_size": batch_size,
        "pytorch": torch.__version__,
        "python": platform.python_version(),
        "h5py": h5py.__version__,
        "numpy": np.__version__,
    }

    output = LOCAL.parent / "results"
    output.mkdir(exist_ok=True)
    with (output / "ave_reference_predictions.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ave_row", "second", "target_class_id", "predicted_class_id"])
        for row, expected, actual in zip(rows, target, predicted):
            for second, (label, prediction) in enumerate(zip(expected, actual)):
                writer.writerow([row, second, label, prediction])
    report = json.dumps(result, indent=2) + "\n"
    (output / "ave_reference.json").write_text(report)
    print(report, end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Cache only the official test visual rows")
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    rows = test_rows()
    if args.fetch:
        fetch_visual(rows)
    else:
        evaluate(rows, args.batch_size)
