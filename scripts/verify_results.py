"""Verify the reported AVE accuracy and error counts using committed predictions."""

import csv
import json
from math import isclose
from pathlib import Path
import sys


RESULTS = Path(__file__).resolve().parents[1] / "results"
METHODS = ("reference", "local_average", "norm_matched")
OFFSETS = (-2, -1, 0, 1, 2)


def check(label, measured, recorded):
    if not isclose(measured, recorded, rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"{label}: measured {measured}, recorded {recorded}")


def predictions(filename):
    rows = {}
    with (RESULTS / filename).open(newline="") as stream:
        for record in csv.DictReader(stream):
            key = (int(record["ave_row"]), int(record["second"]))
            if key in rows:
                raise ValueError(f"{filename}: duplicate clip/second {key}")
            rows[key] = record
    return rows


def verify():
    reference = json.loads((RESULTS / "ave_reference.json").read_text())
    test = json.loads((RESULTS / "ave_test.json").read_text())
    full = predictions("ave_reference_predictions.csv")
    shifted = predictions("ave_test_predictions.csv")
    clips = {clip for clip, second in full}
    expected = {(clip, sec) for clip in clips for sec in range(10)}
    if full.keys() != expected or shifted.keys() != expected:
        raise ValueError("The two prediction files must cover the same ten seconds per clip")
    check("original test split", len(clips), 402)
    correct = sum(r["predicted_class_id"] == r["target_class_id"] for r in full.values())
    accuracy = 100 * correct / len(full)
    for summary in (reference, test["unmasked_full_clip_reference"]):
        check("full-clip segments", len(full), summary["segments"])
        check("full-clip correct", correct, summary["correct_segments"])
        check("full-clip accuracy", accuracy, summary["accuracy_percent"])

    scored = []
    for key, row in shifted.items():
        if row["target_class_id"] != full[key]["target_class_id"]:
            raise ValueError(f"Target class differs at {key}")
        if row["reference_shifted_+0"] != full[key]["predicted_class_id"]:
            raise ValueError(f"Unshifted prediction differs at {key}")
        in_window = 2 <= key[1] <= 7
        check(f"scoring mask at {key}", int(row["scored"]), int(in_window))
        if in_window:
            scored.append(row)
    check("scored segments per condition", len(scored), test["scored_segments_per_condition"])

    conditions = {c["offset_seconds"]: c["methods"] for c in test["conditions"]}
    errors = {c["offset_seconds"]: c for c in test["error_analysis"]}
    rates = {}
    fixed_total = broken_total = 0
    for offset in OFFSETS:
        for method in METHODS:
            for kind in ("aligned", "shifted"):
                column = f"{method}_{kind}_{offset:+d}"
                count = sum(r[column] == r["target_class_id"] for r in scored)
                rate = 100 * count / len(scored)
                recorded = conditions[offset][method]
                check(column + " correct", count, recorded["correct_segments"][kind])
                check(column + " accuracy", rate, recorded["accuracy_percent"][kind])
                rates[method, kind, offset] = rate
        if abs(offset) == 2:
            fixed = broken = 0
            for row in scored:
                target = row["target_class_id"]
                before = row[f"reference_shifted_{offset:+d}"] == target
                after = row[f"local_average_shifted_{offset:+d}"] == target
                fixed += after and not before
                broken += before and not after
            check(f"{offset:+d}s corrected errors", fixed, errors[offset]["fixed"])
            check(f"{offset:+d}s new errors", broken, errors[offset]["broken"])
            fixed_total += fixed
            broken_total += broken

    def two_second_mean(method, kind):
        return (rates[method, kind, -2] + rates[method, kind, 2]) / 2

    baseline = two_second_mean("reference", "shifted")
    local = two_second_mean("local_average", "shifted")
    penalty = two_second_mean("reference", "aligned") - baseline
    gain = local - baseline
    contrasts = test["overall"]["reference"]
    check("baseline shift penalty", penalty, contrasts["d2_pp"]["estimate"])
    check("local averaging gain", gain, contrasts["local_average_gain_at_two_seconds_pp"]["estimate"])

    print(f"Full-clip reproduction: {correct}/{len(full)} = {accuracy:.2f}%")
    print(f"Verified all 30 accuracies ({len(scored)} segments per condition).")
    print(f"Mean at ±2 s: baseline {baseline:.2f}%, local averaging {local:.2f}%, gain {gain:+.2f} pp")
    print(f"Matched baseline shift penalty: {penalty:.2f} pp")
    print(f"Local averaging across both two-second shifts: {fixed_total} corrected, {broken_total} new errors")


if __name__ == "__main__":
    try:
        verify()
    except (OSError, KeyError, ValueError) as error:
        sys.exit(f"Verification failed: {error}")
