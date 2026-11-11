"""Check paired audio shifts with the published A+V-att model on AVE validation."""

import argparse
import csv
import hashlib
import json
import platform

import h5py
import numpy as np

from ave_reference import (
    UPSTREAM_REVISION,
    VISUAL_DTYPE,
    VISUAL_SHAPE,
    cached_visual,
    fetch_visual,
)
from ave_smoke import (
    CHECKPOINT_SHA256,
    FEATURES,
    LOCAL,
    MODEL_SOURCE_SHA256,
    UPSTREAM,
    load_model,
    split_indices,
)


VISUAL_DIR = LOCAL / "visual_validation"
OFFSETS = (-2, -1, 0, 1, 2)
SCORED = slice(2, 8)
SEGMENTS = FEATURES["audio"][2][1]
CLASSES = 29
LABELS_PATH = UPSTREAM / "data/labels.h5"


def shift_and_control(audio, offset):
    """Return delayed audio, unshifted audio with the same zeros, and the kept bins."""
    segments = audio.shape[1]
    if abs(offset) >= segments:
        raise ValueError("The shift must leave at least one audio segment")
    start, stop = max(0, offset), min(segments, segments + offset)
    shifted = np.zeros_like(audio)
    control = np.zeros_like(audio)
    kept = np.zeros(segments, dtype=bool)
    shifted[:, start:stop] = audio[:, start - offset:stop - offset]
    control[:, start:stop] = audio[:, start:stop]
    kept[start:stop] = True
    return shifted, control, kept


def validation_rows():
    rows = split_indices("val")
    if rows.shape != (402,) or np.unique(rows).size != 402 or not (
        (rows >= 0) & (rows < VISUAL_SHAPE[0])
    ).all():
        raise ValueError("Expected 402 distinct rows in the official validation order")
    return rows


def sha256(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def load_audio_and_targets(rows):
    audio_official = LOCAL / "audio_feature_official.h5"
    audio_path = audio_official if audio_official.is_file() else LOCAL / "audio_feature.h5"
    audio_origin = "official" if audio_path == audio_official else "LECOO/AVE mirror"
    with h5py.File(audio_path, "r") as file:
        dataset = file["avadataset"]
        if dataset.shape != FEATURES["audio"][2]:
            raise ValueError(f"Unexpected audio HDF5 shape: {dataset.shape}")
        audio = np.stack([dataset[int(row)] for row in rows]).astype(np.float32)
    with h5py.File(LABELS_PATH, "r") as file:
        labels = np.stack([file["avadataset"][int(row)] for row in rows])
    if labels.shape != (len(rows), SEGMENTS, CLASSES) or not np.isin(labels, (0, 1)).all() or (
        labels.sum(axis=-1) != 1
    ).any():
        raise ValueError("Expected one target per segment and 29 classes")
    target = labels.argmax(axis=-1)
    if not np.isfinite(audio).all() or not audio.reshape(len(rows), -1).any(axis=1).all():
        raise ValueError("Invalid or empty audio features")
    return audio, target, audio_path, audio_origin


def visual_batches(rows, batch_size, directory, digest=None):
    for start in range(0, len(rows), batch_size):
        batch = slice(start, start + batch_size)
        batch_rows = rows[batch]
        frames = []
        for row in batch_rows:
            path = cached_visual(row, directory)
            if path is None:
                raise FileNotFoundError(f"Visual row {row} is missing. Run ave_shift.py --fetch for validation.")
            data = path.read_bytes()
            if digest is not None:
                digest.update(data)
            frames.append(np.frombuffer(data, dtype=VISUAL_DTYPE).reshape(VISUAL_SHAPE[1:]))
        visual = np.stack(frames).astype(np.float32)
        if not np.isfinite(visual).all() or not visual.reshape(len(batch_rows), -1).any(axis=1).all():
            raise ValueError(f"Invalid or empty visual features in rows {batch_rows}")
        yield batch, visual


def evaluate(rows, batch_size):
    import torch

    audio, target, audio_path, audio_origin = load_audio_and_targets(rows)

    conditions = {offset: shift_and_control(audio, offset) for offset in OFFSETS}
    for offset, (shifted, control, kept) in conditions.items():
        if not kept[SCORED].all() or shifted[:, ~kept].any() or control[:, ~kept].any():
            raise ValueError(f"Invalid mask for offset {offset:+d}")
    zero_shifted, zero_control, _ = conditions[0]
    if not np.array_equal(zero_shifted, audio) or not np.array_equal(zero_control, audio):
        raise ValueError("Offset zero must preserve both audio inputs")

    torch.set_num_threads(4)
    model = load_model(torch)
    predictions = {offset: (np.empty_like(target), np.empty_like(target)) for offset in OFFSETS}
    visual_digest = hashlib.sha256()
    with torch.inference_mode():
        for batch, visual in visual_batches(rows, batch_size, VISUAL_DIR, visual_digest):
            batch_rows = rows[batch]
            visual_tensor = torch.from_numpy(visual)
            for offset, (shifted, control, _) in conditions.items():
                for inputs, predicted in zip((shifted, control), predictions[offset]):
                    scores = model(torch.from_numpy(inputs[batch]), visual_tensor)
                    if tuple(scores.shape) != (len(batch_rows), SEGMENTS, CLASSES) or not (
                        torch.isfinite(scores).all()
                    ):
                        raise ValueError(f"Invalid scores for offset {offset:+d} in rows {batch_rows}")
                    predicted[batch] = scores.argmax(dim=-1).numpy()

    if not np.array_equal(*predictions[0]):
        raise ValueError("Shift and control must yield identical predictions at offset zero")

    scored_target = target[:, SCORED]
    total = scored_target.size
    measurements = {}
    for offset, (shifted, control) in predictions.items():
        shifted_correct = int(np.count_nonzero(shifted[:, SCORED] == scored_target))
        control_correct = int(np.count_nonzero(control[:, SCORED] == scored_target))
        measurements[offset] = {
            "offset_seconds": offset,
            "masked_second_indices": np.flatnonzero(~conditions[offset][2]).tolist(),
            "shifted_correct_segments": shifted_correct,
            "control_correct_segments": control_correct,
            "shifted_accuracy_percent": 100 * shifted_correct / total,
            "control_accuracy_percent": 100 * control_correct / total,
            "control_minus_shifted_percentage_points": 100 * (control_correct - shifted_correct) / total,
        }

    def mean_drop(seconds):
        key = "control_minus_shifted_percentage_points"
        return (measurements[-seconds][key] + measurements[seconds][key]) / 2

    result = {
        "model": "A+V-att",
        "split": "official AVE validation",
        "purpose": "protocol validation",
        "clips": len(rows),
        "input_segments_per_clip": SEGMENTS,
        "scored_second_indices": list(range(SEGMENTS))[SCORED],
        "scored_segments_per_condition": total,
        "positive_offset": "delay audio: input audio at t comes from t - offset",
        "boundary_handling": "zero pad without wraparound; zero the same positions in the unshifted control",
        "conditions": list(measurements.values()),
        "d1_mean_drop_percentage_points": mean_drop(1),
        "d2_mean_drop_percentage_points": mean_drop(2),
        "upstream_revision": UPSTREAM_REVISION,
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "model_source_sha256": MODEL_SOURCE_SHA256,
        "audio_origin": audio_origin,
        "audio_sha256": sha256(audio_path),
        "visual_sha256_in_validation_order": visual_digest.hexdigest(),
        "validation_order_sha256": sha256(UPSTREAM / "data/val_order.h5"),
        "labels_sha256": sha256(LABELS_PATH),
        "device": "cpu",
        "batch_size": batch_size,
        "pytorch": torch.__version__,
        "python": platform.python_version(),
        "h5py": h5py.__version__,
        "numpy": np.__version__,
    }

    output = LOCAL.parent / "results"
    output.mkdir(exist_ok=True)
    with (output / "ave_shift_validation_predictions.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ave_row", "second", "scored", "target_class_id", *(
            f"{condition}_{offset:+d}" for offset in OFFSETS for condition in ("shifted", "control")
        )])
        for index, row in enumerate(rows):
            for second in range(SEGMENTS):
                writer.writerow([row, second, int(SCORED.start <= second < SCORED.stop), target[index, second], *(
                    predicted[index, second] for offset in OFFSETS for predicted in predictions[offset]
                )])
    report = json.dumps(result, indent=2) + "\n"
    (output / "ave_shift_validation.json").write_text(report)
    print(report, end="")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="Cache only the official validation visual rows")
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    rows = validation_rows()
    if args.fetch:
        fetch_visual(rows, VISUAL_DIR)
    else:
        evaluate(rows, args.batch_size)
