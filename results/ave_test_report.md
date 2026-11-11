# Original AVE test results

Local audio averaging improves mean shifted accuracy at ±2 seconds by **0.83 percentage points** over A+V-att (95% CI [0.29, 1.35]) and by **0.56 points** over the norm-matched ablation [0.02, 1.10]. The interval for reduction of the matched shift penalty includes zero.

The experiment used the original 402 test clips and the published weights on 10 November 2026. The two-second neighborhood and 0.5 mixing weight were fixed during validation. Each shift has an aligned control with identical audio boundary zeros. All conditions score indices 2-7, giving 2,412 segments per condition. Visual features and split lists come from the authors. Audio uses the recorded LECOO/AVE mirror, whose full identity with the official audio file remains unverified. [Fixed configuration](../configs/ave_improvement.json) · [Machine-readable record](ave_test.json)

## Accuracy and confidence intervals

Cells show segment accuracy (%) followed by the source-video bootstrap 95% interval. All rows, including zero shift, use the same six central seconds.

### Shifted audio

| Offset | A+V-att baseline | Local audio averaging | Norm-matched ablation |
| ---: | ---: | ---: | ---: |
| -2 s | 69.98 [66.50, 73.51] | 70.81 [67.33, 74.34] | 70.40 [66.87, 73.88] |
| -1 s | 72.64 [69.15, 76.12] | 72.72 [69.24, 76.20] | 72.47 [68.99, 75.91] |
| +0 s | 72.60 [69.07, 76.08] | 72.51 [68.95, 76.04] | 72.39 [68.91, 75.83] |
| +1 s | 71.52 [67.99, 74.96] | 72.10 [68.53, 75.58] | 71.43 [67.91, 74.88] |
| +2 s | 69.40 [65.88, 72.93] | 70.23 [66.67, 73.80] | 69.53 [66.00, 73.05] |

### Aligned controls with matched boundary masks

| Offset | A+V-att baseline | Local audio averaging | Norm-matched ablation |
| ---: | ---: | ---: | ---: |
| -2 s | 71.27 [67.74, 74.75] | 71.81 [68.33, 75.33] | 71.06 [67.54, 74.54] |
| -1 s | 72.26 [68.78, 75.66] | 72.55 [68.99, 76.04] | 72.31 [68.82, 75.70] |
| +0 s | 72.60 [69.07, 76.08] | 72.51 [68.95, 76.04] | 72.39 [68.91, 75.83] |
| +1 s | 72.68 [69.15, 76.12] | 72.31 [68.78, 75.83] | 72.47 [68.99, 75.91] |
| +2 s | 71.89 [68.37, 75.37] | 71.85 [68.33, 75.33] | 71.81 [68.33, 75.29] |

The unmasked full-clip reproduction is **72.7363%** (2,924/4,020). Its 4,020 zero-shift predictions match the earlier reproduction exactly. Tian et al. report **72.7%** in Table 1. The central-segment protocol above has a denominator of 2,412. [Reproduction record](ave_reference.json) · [Tian et al., Table 1](https://arxiv.org/pdf/1803.08842#page=12)

## Paired comparisons

Intervals use the 2.5th and 97.5th percentiles of 10,000 bootstrap replicates, jointly resampling source video IDs across all methods and offsets with seed 2026. Per-offset intervals are unadjusted for multiple comparisons.

| Method | Mean shifted accuracy at ±2 s (%) | D₁ (pp) | D₂ (pp) | D₂ minus D₁ (pp) |
| --- | ---: | ---: | ---: | ---: |
| A+V-att baseline | 69.69 | 0.39 [-0.19, 0.97] | 1.89 [1.06, 2.74] | 1.49 [0.68, 2.34] |
| Local audio averaging | 70.52 | 0.02 [-0.46, 0.52] | 1.31 [0.56, 2.07] | 1.29 [0.62, 1.99] |
| Norm-matched ablation | 69.96 | 0.44 [-0.15, 1.02] | 1.47 [0.64, 2.30] | 1.04 [0.25, 1.82] |

D₁ and D₂ are mean aligned-control minus shifted accuracy differences across the two directions at the corresponding magnitude. The baseline intervals for D₂ and D₂ minus D₁ lie above zero, supporting both the primary shift hypothesis and the secondary magnitude expectation.

The intervention reduces baseline D₂ by **0.58 pp** (95% CI [-0.04, 1.18]). Its aligned-input difference at zero shift is **-0.08 pp** [-0.70, 0.54]. The lower bound for the ±2-second comparison against the norm-matched ablation is close to zero. [Figure PNG](ave_test_accuracy.png) · [Figure SVG](ave_test_accuracy.svg)

Excluding eight source IDs also seen in training or validation leaves 394 clips. Baseline D₂ becomes **1.92 pp** [1.10, 2.81]. Local averaging gains **0.85 pp** [0.32, 1.40] over the baseline and **0.57 pp** [0.02, 1.12] over the ablation. The D₂ reduction remains uncertain at **0.59 pp** [-0.04, 1.23]. [Sensitivity analysis](ave_test.json)

## Inference latency

Measurements start with features in memory and include preprocessing, the model and argmax. The macOS arm64 CPU uses four threads, a single-clip batch and five warmups per arm. The first 32 clips at each offset give 160 samples. Method order rotates across inputs.

| Method | Calls | Median ms/clip | p95 ms/clip |
| --- | ---: | ---: | ---: |
| A+V-att baseline | 160 | 0.696 | 0.757 |
| Local audio averaging | 160 | 0.717 | 0.787 |
| Norm-matched ablation | 160 | 0.723 | 0.795 |

Local averaging adds approximately **0.020 ms/clip (2.9%)** to the median. These timings exclude disk access, network access and raw feature extraction.

## Failure analysis

At ±2 seconds, event presence differs between the original audio source and target seconds in 508 of 4,824 segment-conditions (10.5%). This subset accounts for 76 of 91 net baseline losses relative to matched controls (83.5%). Grouping is derived from original event annotations.

Local averaging corrects 86 errors and introduces 46 across the two directions. In the event-presence mismatch subset, it corrects 21 and introduces 8.

| Offset | Event-presence mismatches | Net baseline loss in that subset | Corrected / broken by local averaging, all segments |
| --- | ---: | ---: | ---: |
| -2 s | 254 | 28 | 42 / 22 |
| -1 s | 133 | 14 | 25 / 23 |
| +0 s | 0 | 0 | 27 / 29 |
| +1 s | 130 | 15 | 33 / 19 |
| +2 s | 254 | 48 | 44 / 24 |

- **Recovered onset.** AVE row 27, +2 seconds, target second 5. The bell begins at second 5, while original audio second 3 arrives at the target. The baseline predicts background, and local averaging predicts the bell.
- **New missed event.** AVE row 421, +2 seconds, target second 2. Barking begins at second 1, while audio from second 0 arrives at the target. The baseline detects barking, and local averaging predicts background.
- **Aligned onset error.** AVE row 68 at zero shift, second 6. The baseline correctly detects the bell onset, while local averaging predicts background.

Examples were selected from annotations and saved predictions. [All counts and examples](ave_test.json) · [Segment predictions](ave_test_predictions.csv)

## Reproduction commands

With the feature cache and recorded validation files present, run the following from the repository root. The figure uses Matplotlib 3.10.8.

~~~bash
.ave-local/venv/bin/python -B scripts/ave_test.py
.ave-local/venv/bin/python -B scripts/export_tables.py
.ave-local/venv/bin/python -B scripts/plot_ave_test.py
~~~
