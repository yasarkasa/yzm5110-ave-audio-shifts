"""Render the official AVE test accuracies and paired contrasts as PNG and SVG."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
import numpy as np


RESULTS = Path(__file__).resolve().parents[1] / "results"
COLORS = {"reference": "#375886", "local_average": "#087b68", "norm_matched": "#ad5d24"}
LABELS = {"reference": "A+V-att referansı", "local_average": "Yerel ses ortalaması",
          "norm_matched": "Norm eşlemeli ablasyon"}


def plot_intervals(ax, offsets, estimates, bounds, *, method, label, nudge, marker):
    points = np.asarray(estimates)
    low, high = np.asarray(bounds).T
    ax.errorbar(offsets + nudge, points, yerr=[points - low, high - points], color=COLORS[method],
                fmt=f"{marker}-", markersize=5, capsize=3, linewidth=1.3, label=label)


def main():
    report = json.loads((RESULTS / "ave_test.json").read_text())
    data = report["conditions"]
    offsets = np.array([condition["offset_seconds"] for condition in data])
    fmt_offset = [f"{value:+d}".replace("-", "−") if value else "0" for value in offsets]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10.5, "text.color": "#182536",
                         "axes.labelcolor": "#182536", "xtick.color": "#47566b", "ytick.color": "#47566b"})
    fig, (accuracy, gain) = plt.subplots(2, 1, figsize=(9.1, 7.2), sharex=True,
                                         gridspec_kw={"height_ratios": [1.1, 1]})
    fig.subplots_adjust(left=0.145, right=0.955, top=0.79, bottom=0.15, hspace=0.55)
    fig.text(0.145, 0.945, "AVE testinde ses kaymasının etkisi", fontsize=20, fontweight="bold")
    segments = f"{report['scored_segments_per_condition']:,}".replace(",", ".")
    fig.text(0.145, 0.905, f"{report['clips']} klip · Koşul başına {segments} bölüm · %95 güven aralığı",
             color="#47566b")

    for (method, label), nudge, marker in zip(LABELS.items(), (-0.085, 0, 0.085), ("o", "s", "D")):
        stats = [condition["methods"][method] for condition in data]
        plot_intervals(accuracy, offsets, [s["accuracy_percent"]["shifted"] for s in stats],
                       [s["accuracy_ci95_percent"]["shifted"] for s in stats],
                       method=method, label=label, nudge=nudge, marker=marker)
    accuracy.set_ylabel("Bölüm doğruluğu (%)")
    accuracy.set_title("A   Kaydırılmış sesle doğruluk", loc="left", fontweight="bold", pad=14)
    accuracy.legend(loc="upper left", bbox_to_anchor=(0, 1.43), ncol=3, frameon=False,
                    borderaxespad=0, handletextpad=0.45, columnspacing=1.6, fontsize=9.5)

    gain.axhline(0, color="#64748b", linestyle="--", linewidth=1)
    for method, label, nudge, marker in (("reference", "Referansa göre", -0.055, "o"),
                                         ("norm_matched", "Ablasyona göre", 0.055, "D")):
        stats = [condition["local_average_gain_pp"][method] for condition in data]
        plot_intervals(gain, offsets, [s["estimate"] for s in stats], [s["ci95"] for s in stats],
                       method=method, label=label, nudge=nudge, marker=marker)
    gain.set_title("B   Yerel ortalamanın doğruluk farkı", loc="left", fontweight="bold", pad=10)
    gain.set_ylabel("Fark (yüzde puanı)")
    gain.set_xlabel("Ses kayması (saniye)", labelpad=7)
    gain.legend(loc="lower right", frameon=True, facecolor="white", edgecolor="none", fontsize=9.5)

    for ax in (accuracy, gain):
        ax.set_xlim(-2.38, 2.38)
        ax.set_xticks(offsets, fmt_offset)
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#dbe2e9", linewidth=0.7)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.spines["bottom"].set_color("#b7c2cf")
        ax.tick_params(axis="y", length=0, pad=6)
        ax.tick_params(axis="x", length=0, pad=5)
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}".replace("-", "−").replace(".", ",")))

    fig.text(0.145, 0.038, "Aralıklar kaynak video düzeyinde 10.000 eşlenmiş bootstrap örneğinden hesaplandı.",
             color="#47566b", fontsize=9)
    for extension in ("png", "svg"):
        fig.savefig(RESULTS / f"ave_test_accuracy.{extension}", dpi=220, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
