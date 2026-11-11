"""Evaluate local audio averaging and its norm-matched control on AVE validation."""

import csv
import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter_ns

import h5py
import numpy as np
import torch

from ave_shift import (
    CLASSES,
    LABELS_PATH,
    OFFSETS,
    SCORED,
    SEGMENTS,
    VISUAL_DIR,
    load_audio_and_targets,
    sha256,
    shift_and_control,
    validation_rows,
    visual_batches,
)
from ave_smoke import CHECKPOINT_SHA256, LOCAL, MODEL_SOURCE_SHA256, UPSTREAM, load_model


CONFIG_PATH = LOCAL.parent / "configs/ave_improvement.json"
METHODS = ("reference", "local_average", "norm_matched")
CONDITIONS = ("shifted", "aligned")


def prepare_audio(audio, kept, method, radius, neighbor_weight):
    if method == "reference":
        return audio

    seconds = np.arange(audio.shape[1])
    distances = np.abs(seconds[:, None] - seconds[None, :])
    weights = ((distances > 0) & (distances <= radius) & kept[None, :]).astype(audio.dtype)
    counts = weights.sum(axis=1, keepdims=True)
    weights /= np.maximum(counts, 1)
    average = weights @ audio
    # Keep the center when the window has no available neighbors.
    average = np.where(counts > 0, average, audio)
    mixed = (1 - neighbor_weight) * audio + neighbor_weight * average
    original_norm = np.linalg.norm(audio, axis=-1, keepdims=True)
    active = kept[None, :, None] & (original_norm > 0)
    mixed = np.where(active, mixed, 0)
    if method == "local_average":
        return mixed
    if method != "norm_matched":
        raise ValueError(f"Unknown method {method!r}")

    mixed_norm = np.linalg.norm(mixed, axis=-1, keepdims=True)
    scale = np.divide(mixed_norm, original_norm, out=np.zeros_like(mixed_norm), where=active)
    return audio * scale


def predict(model, audio, visual, kept, method, settings):
    prepared = prepare_audio(audio, kept, method, settings["radius_seconds"], settings["neighbor_weight"])
    scores = model(torch.from_numpy(prepared), visual)
    return scores, scores.argmax(dim=-1).numpy()


def collect_predictions(model, rows, conditions, settings, directory):
    predictions = {
        (method, offset, condition): np.empty((len(rows), SEGMENTS), dtype=int)
        for method in METHODS for offset in OFFSETS for condition in CONDITIONS
    }
    visual_digest = hashlib.sha256()
    for batch, visual in visual_batches(rows, settings["accuracy_batch_size"], directory, visual_digest):
        video_tensor = torch.from_numpy(visual)
        for offset, (shifted, aligned, kept) in conditions.items():
            for condition, audio in zip(CONDITIONS, (shifted, aligned)):
                for method in METHODS:
                    scores, classes = predict(model, audio[batch], video_tensor, kept, method, settings)
                    if tuple(scores.shape) != (len(visual), SEGMENTS, CLASSES) or not torch.isfinite(scores).all():
                        raise ValueError(f"Invalid output for {method}, {offset:+d}, {condition}")
                    predictions[method, offset, condition][batch] = classes
    for method in METHODS:
        if not np.array_equal(predictions[method, 0, "shifted"], predictions[method, 0, "aligned"]):
            raise ValueError(f"Zero-shift predictions diverged for {method}")
    return predictions, visual_digest.hexdigest()


def benchmark(model, rows, conditions, settings, directory):
    latency = settings["latency"]
    count = latency["first_clips_per_offset"]
    batch_size = latency["batch_size"]
    if batch_size != 1 or not 0 < count <= len(rows):
        raise ValueError("The latency benchmark requires a valid set of single-clip inputs")
    videos = [torch.from_numpy(visual) for _, visual in visual_batches(rows[:count], batch_size, directory)]
    times = {method: [] for method in METHODS}
    audio, _, kept = conditions[0]
    for _ in range(latency["warmup_calls_per_method"]):
        for method in METHODS:
            predict(model, audio[:1], videos[0], kept, method, settings)

    for offset_index, (audio, _, kept) in enumerate(conditions.values()):
        for clip_index, video in enumerate(videos):
            clip_audio = audio[clip_index:clip_index + 1]
            # Rotate the order across inputs so each arm runs first equally often.
            start = (offset_index * count + clip_index) % len(METHODS)
            for method in METHODS[start:] + METHODS[:start]:
                before = perf_counter_ns()
                predict(model, clip_audio, video, kept, method, settings)
                times[method].append((perf_counter_ns() - before) / 1_000_000)
    return {
        method: {"samples": len(samples), "median_ms": float(np.median(samples)),
                 "p95_ms": float(np.percentile(samples, 95))}
        for method, samples in times.items()
    }


def summarize(predictions, target, conditions, settings):
    scored = target[:, SCORED]
    measurements = []
    for offset, (_, _, kept) in conditions.items():
        methods = {}
        for method in METHODS:
            correct = {
                condition: int(np.count_nonzero(predictions[method, offset, condition][:, SCORED] == scored))
                for condition in CONDITIONS
            }
            methods[method] = {
                "correct_segments": correct,
                "accuracy_percent": {condition: 100 * value / scored.size for condition, value in correct.items()},
                "aligned_minus_shifted_pp": 100 * (correct["aligned"] - correct["shifted"]) / scored.size,
            }
        measurements.append({"offset_seconds": offset, "masked_second_indices": np.flatnonzero(~kept).tolist(),
                             "methods": methods})

    primary = [item["methods"] for item in measurements if item["offset_seconds"] in settings["primary_offsets_seconds"]]
    averages = {
        method: {
            "shifted_accuracy_percent": float(np.mean([m[method]["accuracy_percent"]["shifted"] for m in primary])),
            "d2_pp": float(np.mean([m[method]["aligned_minus_shifted_pp"] for m in primary])),
        }
        for method in METHODS
    }
    average_accuracy = averages["local_average"]["shifted_accuracy_percent"]
    return measurements, {
        "two_second_shift_means": averages,
        "local_average_minus_reference_pp": average_accuracy - averages["reference"]["shifted_accuracy_percent"],
        "local_average_minus_norm_matched_pp": average_accuracy - averages["norm_matched"]["shifted_accuracy_percent"],
    }


def write_predictions(path, rows, target, predictions):
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ave_row", "second", "scored", "target_class_id", *(
            f"{method}_{condition}_{offset:+d}" for method, offset, condition in predictions
        )])
        for clip_index, row in enumerate(rows):
            for second in range(SEGMENTS):
                writer.writerow([row, second, int(SCORED.start <= second < SCORED.stop), target[clip_index, second], *(
                    predicted[clip_index, second] for predicted in predictions.values()
                )])


def main():
    settings = json.loads(CONFIG_PATH.read_text())
    if tuple(settings["offsets_seconds"]) != OFFSETS or settings["scored_second_indices"] != list(range(SEGMENTS))[SCORED]:
        raise ValueError("Improvement and reference must use the same offsets and scoring positions")
    rows = validation_rows()
    audio, target, audio_path, audio_origin = load_audio_and_targets(rows)
    conditions = {offset: shift_and_control(audio, offset) for offset in OFFSETS}
    torch.set_num_threads(settings["cpu_threads"])
    model = load_model(torch)
    with torch.inference_mode():
        predictions, visual_sha = collect_predictions(model, rows, conditions, settings, VISUAL_DIR)
        latency = benchmark(model, rows, conditions, settings, VISUAL_DIR)
    measurements, contrasts = summarize(predictions, target, conditions, settings)

    report = {
        "split": "official AVE validation",
        "model": "A+V-att",
        "settings": settings,
        "config_sha256": sha256(CONFIG_PATH),
        "script_sha256": sha256(Path(__file__)),
        "clips": len(rows),
        "scored_segments_per_condition": target[:, SCORED].size,
        "conditions": measurements,
        "contrasts": contrasts,
        "latency": {"unit": "ms per clip", "conditions": "shifted inputs at all five offsets", "methods": latency},
        "audio_origin": audio_origin,
        "audio_sha256": sha256(audio_path),
        "checkpoint_sha256": CHECKPOINT_SHA256,
        "model_source_sha256": MODEL_SOURCE_SHA256,
        "visual_sha256_in_validation_order": visual_sha,
        "validation_order_sha256": sha256(UPSTREAM / "data/val_order.h5"),
        "labels_sha256": sha256(LABELS_PATH),
        "device": "cpu",
        "machine": platform.machine(),
        "python": platform.python_version(),
        "pytorch": torch.__version__,
        "h5py": h5py.__version__,
        "numpy": np.__version__,
    }
    output = LOCAL.parent / "results"
    output.mkdir(exist_ok=True)
    write_predictions(output / "ave_improvement_validation_predictions.csv", rows, target, predictions)
    (output / "ave_improvement_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"contrasts": contrasts, "latency": latency}, indent=2))


if __name__ == "__main__":
    main()
