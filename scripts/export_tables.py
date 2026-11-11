"""Export the reported test tables from the saved JSON without running the model."""

import csv
import json
from pathlib import Path


RESULTS = Path(__file__).resolve().parents[1] / "results"


def write_table(name, columns, records):
    with (RESULTS / "tables" / name).open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        writer.writerows(records)


if __name__ == "__main__":
    data = json.loads((RESULTS / "ave_test.json").read_text())
    (RESULTS / "tables").mkdir(exist_ok=True)
    accuracy = []
    for condition in data["conditions"]:
        for method, values in condition["methods"].items():
            for kind in ("shifted", "aligned"):
                accuracy.append([condition["offset_seconds"], method, kind,
                                 values["correct_segments"][kind], data["scored_segments_per_condition"],
                                 values["accuracy_percent"][kind], *values["accuracy_ci95_percent"][kind]])
    write_table("accuracy.csv", ["offset_seconds", "method", "condition", "correct", "segments",
                                  "accuracy_percent", "ci95_low", "ci95_high"], accuracy)
    write_table("contrasts.csv", ["method_or_comparator", "contrast", "estimate_pp", "ci95_low", "ci95_high"],
                [[method, contrast, value["estimate"], *value["ci95"]]
                 for method, values in data["overall"].items() for contrast, value in values.items()])
    write_table("latency.csv", ["method", "calls", "median_ms_per_clip", "p95_ms_per_clip"],
                [[method, value["samples"], value["median_ms"], value["p95_ms"]]
                 for method, value in data["latency"]["methods"].items()])
    print("Exported accuracy, contrasts and latency under results/tables/")
