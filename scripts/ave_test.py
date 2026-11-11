"""Run the frozen audio-shift experiment on the official AVE test split."""

import csv
import json
import platform
from pathlib import Path

import h5py
import numpy as np
import torch

import ave_improvement
from ave_improvement import CONFIG_PATH, CONDITIONS, METHODS, benchmark, collect_predictions, summarize, write_predictions
from ave_reference import UPSTREAM_REVISION, VISUAL_DIR, test_rows as official_test_rows
from ave_shift import LABELS_PATH, OFFSETS, SCORED, load_audio_and_targets, sha256, shift_and_control
from ave_smoke import CHECKPOINT_SHA256, LOCAL, MODEL_SOURCE_SHA256, UPSTREAM, load_model, read_annotations, split_indices


def clip_metrics(predictions, targets, primary_offsets):
    # Keep differences in correct-segment counts until the final percentage conversion.
    accuracy = {key: (prediction[:, SCORED] == targets[:, SCORED]).sum(axis=1)
                for key, prediction in predictions.items()}
    metrics = {"accuracy": accuracy}
    metrics["shift_loss"] = {(method, offset): accuracy[method, offset, "aligned"] - accuracy[method, offset, "shifted"]
                             for method in METHODS for offset in OFFSETS}
    metrics["local_average_gain"] = {(other, offset): accuracy["local_average", offset, "shifted"]
                                     - accuracy[other, offset, "shifted"]
                                     for other in ("reference", "norm_matched") for offset in OFFSETS}
    metrics["overall"] = {}
    for method in METHODS:
        d1 = np.mean([metrics["shift_loss"][method, offset] for offset in (-1, 1)], axis=0)
        d2 = np.mean([metrics["shift_loss"][method, offset] for offset in primary_offsets], axis=0)
        metrics["overall"].update({(method, "d1_pp"): d1, (method, "d2_pp"): d2,
                                   (method, "d2_minus_d1_pp"): d2 - d1})
    for other in ("reference", "norm_matched"):
        gain = np.mean([metrics["local_average_gain"][other, offset] for offset in primary_offsets], axis=0)
        metrics["overall"][other, "local_average_gain_at_two_seconds_pp"] = gain
        metrics["overall"][other, "local_average_d2_reduction_pp"] = (
            metrics["overall"][other, "d2_pp"] - metrics["overall"]["local_average", "d2_pp"]
        )
    return metrics


def cluster_bootstrap(metrics, video_ids, settings):
    unique, groups = np.unique(video_ids, return_inverse=True)
    if settings["unit"] != "source_video_id" or len(unique) < 2:
        raise ValueError("Cluster bootstrap requires multiple source video IDs")
    flat = {(name, key): per_clip for name, values in metrics.items() for key, per_clip in values.items()}
    per_clip = np.column_stack(list(flat.values()))
    per_video = np.zeros((len(unique), per_clip.shape[1]))
    np.add.at(per_video, groups, per_clip)
    group_sizes = np.bincount(groups).astype(float)
    rng = np.random.default_rng(settings["seed"])
    draws = rng.multinomial(len(unique), np.full(len(unique), 1 / len(unique)), size=settings["replicates"])
    draws = draws.astype(float)
    # Draw videos jointly for all methods and offsets. Weight each draw by its number of clips.
    scale = 100 / (SCORED.stop - SCORED.start)
    samples = scale * (draws @ per_video) / (draws @ group_sizes)[:, None]
    tail = (1 - settings["confidence_level"]) / 2
    low, high = np.quantile(samples, [tail, 1 - tail], axis=0)
    out = {name: {} for name in metrics}
    for index, (name, key) in enumerate(flat):
        out[name][key] = {"estimate": float(scale * per_clip[:, index].mean()),
                          "ci95": [float(low[index]), float(high[index])]}
    return out


def summarize_overall(intervals):
    return {method: {name: measure for (other, name), measure in intervals["overall"].items() if other == method}
            for method in METHODS}


def analyze_errors(rows, targets, predictions, annotations):
    classes = list(dict.fromkeys(annotation[0] for annotation in annotations)) + ["Background"]
    background = len(classes) - 1
    timeline = np.arange(targets.shape[1])[SCORED]
    expected = targets[:, SCORED]
    event = targets != background

    def example(selector, mismatch, offset, reference, local):
        # Prefer a case where annotated event presence changes between the source and target seconds.
        matches = np.argwhere(selector & mismatch)
        if not len(matches):
            matches = np.argwhere(selector)
        if not len(matches):
            return None
        clip_index, scored_index = matches[0]
        row, second = int(rows[clip_index]), int(timeline[scored_index])
        category, video_id, _, start, end = annotations[row]
        return {"ave_row": row, "source_video_id": video_id, "second": second,
                "original_audio_source_second": second - offset, "event": category,
                "event_interval_seconds": [int(start), int(end)],
                "target": classes[expected[clip_index, scored_index]],
                "reference": classes[reference[clip_index, scored_index]],
                "local_average": classes[local[clip_index, scored_index]]}

    analysis = []
    for offset in OFFSETS:
        mismatch = event[:, timeline] != event[:, timeline - offset]
        ref = predictions["reference", offset, "shifted"][:, SCORED]
        avg = predictions["local_average", offset, "shifted"][:, SCORED]
        aligned = predictions["reference", offset, "aligned"][:, SCORED]
        fixed = (avg == expected) & (ref != expected)
        broken = (ref == expected) & (avg != expected)
        groups = {}
        for name, group in (("event_presence_changed", mismatch), ("event_presence_unchanged", ~mismatch)):
            groups[name] = {
                "segments": int(group.sum()),
                "reference_net_loss_from_shift": int(np.count_nonzero((aligned == expected) & group)
                                                    - np.count_nonzero((ref == expected) & group)),
                "local_average_fixed": int(np.count_nonzero(fixed & group)),
                "local_average_broken": int(np.count_nonzero(broken & group)),
            }
        analysis.append({"offset_seconds": offset, "groups": groups, "fixed": int(fixed.sum()),
                         "broken": int(broken.sum()),
                         "fixed_example": example(fixed, mismatch, offset, ref, avg),
                         "broken_example": example(broken, mismatch, offset, ref, avg)})
    return analysis


def verify_unshifted(rows, targets, predictions, path):
    with path.open(newline="") as file:
        actual = [(int(r["ave_row"]), int(r["second"]), int(r["target_class_id"]), int(r["predicted_class_id"]))
                  for r in csv.DictReader(file)]
    expected = [(int(row), second, int(target), int(prediction))
                for row, labels, predicted in zip(rows, targets, predictions)
                for second, (target, prediction) in enumerate(zip(labels, predicted))]
    if actual != expected:
        raise ValueError("Unshifted predictions disagree with the original AVE test reproduction")


def main():
    output = LOCAL.parent / "results"
    validation = json.loads((output / "ave_improvement_validation.json").read_text())
    reference = json.loads((output / "ave_reference.json").read_text())
    config_sha = sha256(CONFIG_PATH)
    method_sha = sha256(Path(ave_improvement.__file__))
    if config_sha != validation["config_sha256"] or method_sha != validation["script_sha256"]:
        raise ValueError("The configuration or method differs from the frozen validation run")
    settings = json.loads(CONFIG_PATH.read_text())
    rows = official_test_rows()
    audio, targets, audio_path, audio_origin = load_audio_and_targets(rows)
    provenance = {"audio_sha256": sha256(audio_path), "labels_sha256": sha256(LABELS_PATH),
                  "checkpoint_sha256": CHECKPOINT_SHA256, "model_source_sha256": MODEL_SOURCE_SHA256,
                  "test_order_sha256": sha256(UPSTREAM / "data/test_order.h5")}
    for key, digest in provenance.items():
        if digest != reference[key] or (key in validation and digest != validation[key]):
            raise ValueError(f"Unexpected input digest for {key}")

    conditions = {offset: shift_and_control(audio, offset) for offset in settings["offsets_seconds"]}
    torch.set_num_threads(settings["cpu_threads"])
    model = load_model(torch)
    with torch.inference_mode():
        predictions, visual_sha = collect_predictions(model, rows, conditions, settings, VISUAL_DIR)
        latency = benchmark(model, rows, conditions, settings, VISUAL_DIR)
    if visual_sha != reference["visual_sha256_in_test_order"]:
        raise ValueError("Test visual features differ from the original reference run")
    verify_unshifted(rows, targets, predictions["reference", 0, "shifted"], output / "ave_reference_predictions.csv")

    annotations = read_annotations()
    video_ids = np.array([annotations[row][1] for row in rows])
    prior_ids = {annotations[row][1] for split in ("train", "val") for row in split_indices(split)}
    independent = ~np.isin(video_ids, sorted(prior_ids))
    metrics = clip_metrics(predictions, targets, settings["primary_offsets_seconds"])
    intervals = cluster_bootstrap(metrics, video_ids, settings["bootstrap"])
    independent_metrics = {name: {key: value[independent] for key, value in measures.items()}
                           for name, measures in metrics.items()}
    sensitivity = cluster_bootstrap(independent_metrics, video_ids[independent], settings["bootstrap"])
    accuracy, _ = summarize(predictions, targets, conditions, settings)
    for condition in accuracy:
        offset = condition["offset_seconds"]
        for method, stats in condition["methods"].items():
            stats["accuracy_ci95_percent"] = {kind: intervals["accuracy"][method, offset, kind]["ci95"]
                                             for kind in CONDITIONS}
            stats["aligned_minus_shifted_ci95_pp"] = intervals["shift_loss"][method, offset]["ci95"]
        condition["local_average_gain_pp"] = {other: intervals["local_average_gain"][other, offset]
                                             for other in ("reference", "norm_matched")}

    report = {
        "split": "official AVE test", "model": "A+V-att", "upstream_revision": UPSTREAM_REVISION,
        "settings": settings, "config_sha256": config_sha, "method_sha256": method_sha,
        "clips": len(rows), "source_videos": len(np.unique(video_ids)),
        "scored_segments_per_condition": targets[:, SCORED].size,
        "bootstrap": "paired percentile intervals, resampling source videos with replacement",
        "unmasked_full_clip_reference": {"segments": reference["segments"], "correct_segments": reference["correct_segments"],
                                         "accuracy_percent": reference["accuracy_percent"],
                                         "published_accuracy_percent": reference["published_accuracy_percent"]},
        "conditions": accuracy,
        "overall": summarize_overall(intervals),
        "sensitivity_without_train_or_validation_source_videos": {
            "excluded_ave_rows": rows[~independent].tolist(), "excluded_clips": int((~independent).sum()),
            "clips": int(independent.sum()), "source_videos": len(np.unique(video_ids[independent])),
            "scored_segments_per_condition": targets[independent, SCORED].size,
            "overall": summarize_overall(sensitivity),
        },
        "latency": {"unit": "ms per clip", "conditions": "shifted inputs at all five offsets", "methods": latency},
        "error_analysis": analyze_errors(rows, targets, predictions, annotations),
        "provenance": {**provenance, "visual_sha256_in_test_order": visual_sha, "audio_origin": audio_origin},
        "environment": {"device": "cpu", "machine": platform.machine(), "python": platform.python_version(),
                        "pytorch": torch.__version__, "h5py": h5py.__version__, "numpy": np.__version__},
    }
    write_predictions(output / "ave_test_predictions.csv", rows, targets, predictions)
    (output / "ave_test.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"overall": report["overall"], "latency": latency}, indent=2))


if __name__ == "__main__":
    main()
