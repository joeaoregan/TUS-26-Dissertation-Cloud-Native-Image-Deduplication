#!/usr/bin/env python3
"""Generate publication-ready figures for the dissertation."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL1_SUMMARY = (
    REPO_ROOT / "results" / "interim" / "eval1" / "metrics" / "table_eval1_summary.csv"
)
EVAL2_DETECTION_SUMMARY = (
    REPO_ROOT
    / "results"
    / "interim"
    / "eval2"
    / "metrics"
    / "table_eval2_detection_summary.csv"
)
EVAL3_LABELS = REPO_ROOT / "data" / "labels" / "reference_labels_eval_v2_robustness.csv"
EVAL3_C1_PREDICTIONS = (
    REPO_ROOT
    / "results"
    / "interim"
    / "eval3"
    / "predictions"
    / "eval3-robustness-c1-stage3.csv"
)
EVAL4_SCALABILITY = (
    REPO_ROOT / "results" / "final" / "report-data" / "eval4_c1_scalability.csv"
)
EVAL4_RUNTIME_COMPOSITION = (
    REPO_ROOT / "results" / "final" / "report-data" / "eval4_c1_runtime_composition.csv"
)
OUTPUT_DIR = REPO_ROOT / "docs" / "thesis-assets"


def build_cost_ordered_cascade_figure() -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUTPUT_DIR / "figure-1-cost-ordered-cascade.png"
    svg_path = OUTPUT_DIR / "figure-1-cost-ordered-cascade.svg"

    fig, axis = plt.subplots(figsize=(10.4, 6.0), dpi=300)
    fig.patch.set_facecolor("white")
    axis.set_xlim(0, 10.4)
    axis.set_ylim(0, 6.0)
    axis.axis("off")

    stages = [
        {
            "x": 0.9,
            "y": 4.25,
            "width": 8.6,
            "colour": "#1C75BC",
            "number": "STAGE 1",
            "name": "SHA-256 exact matching",
            "detail": "Binary identity  |  Digest lookup  |  Exact copies resolved",
            "cost": "LOWEST COST",
        },
        {
            "x": 1.55,
            "y": 2.65,
            "width": 7.3,
            "colour": "#E66B4E",
            "number": "STAGE 2",
            "name": "DCT pHash candidate generation",
            "detail": "64-bit fingerprint  |  Hamming distance  |  Dissimilar pairs rejected",
            "cost": "MODERATE COST",
        },
        {
            "x": 2.2,
            "y": 1.05,
            "width": 6.0,
            "colour": "#007F7B",
            "number": "STAGE 3",
            "name": "SSIM structural verification",
            "detail": "Image-level comparison  |  Similarity threshold  |  Near-duplicates verified",
            "cost": "HIGHEST COST",
        },
    ]

    for stage in stages:
        box = FancyBboxPatch(
            (stage["x"], stage["y"]),
            stage["width"],
            1.05,
            boxstyle="round,pad=0.02,rounding_size=0.05",
            facecolor=stage["colour"],
            edgecolor="#263238",
            linewidth=0.8,
        )
        axis.add_patch(box)
        axis.text(
            stage["x"] + 0.25,
            stage["y"] + 0.76,
            stage["number"],
            color="white",
            fontsize=10,
            fontweight="bold",
            va="center",
        )
        axis.text(
            stage["x"] + 1.38,
            stage["y"] + 0.76,
            stage["name"],
            color="white",
            fontsize=14,
            fontweight="bold",
            va="center",
        )
        axis.text(
            stage["x"] + 0.25,
            stage["y"] + 0.31,
            stage["detail"],
            color="white",
            fontsize=9.5,
            va="center",
        )
        axis.text(
            stage["x"] + stage["width"] - 0.25,
            stage["y"] + 0.76,
            stage["cost"],
            color="white",
            fontsize=9,
            fontweight="bold",
            ha="right",
            va="center",
        )

    for upper, lower in zip(stages, stages[1:]):
        axis.add_patch(
            FancyArrowPatch(
                (upper["x"] + upper["width"] / 2, upper["y"]),
                (lower["x"] + lower["width"] / 2, lower["y"] + 1.05),
                arrowstyle="-|>",
                mutation_scale=18,
                linewidth=1.4,
                color="#263238",
            )
        )

    axis.text(
        0.9,
        5.62,
        "ALL INGESTED FILES",
        fontsize=11,
        fontweight="bold",
        color="#263238",
        va="center",
    )
    axis.text(
        9.5,
        5.62,
        "Broad workload",
        fontsize=10,
        color="#5E6A71",
        ha="right",
        va="center",
    )
    axis.add_patch(
        FancyArrowPatch(
            (0.45, 5.25),
            (0.45, 1.05),
            arrowstyle="-|>",
            mutation_scale=16,
            linewidth=1.2,
            color="#5E6A71",
        )
    )
    axis.text(
        0.2,
        3.15,
        "Candidate workload narrows",
        rotation=90,
        fontsize=9.5,
        color="#5E6A71",
        ha="center",
        va="center",
    )
    axis.add_patch(
        FancyArrowPatch(
            (9.95, 5.25),
            (9.95, 1.05),
            arrowstyle="-|>",
            mutation_scale=16,
            linewidth=1.2,
            color="#5E6A71",
        )
    )
    axis.text(
        10.2,
        3.15,
        "Comparison detail and cost increase",
        rotation=270,
        fontsize=9.5,
        color="#5E6A71",
        ha="center",
        va="center",
    )
    axis.text(
        5.2,
        0.38,
        "VERIFIED EXACT AND NEAR-DUPLICATE RELATIONSHIPS",
        fontsize=11,
        fontweight="bold",
        color="#263238",
        ha="center",
        va="center",
    )

    fig.tight_layout(pad=0.6)
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png_path, svg_path


def build_eval1_runtime_chart() -> tuple[Path, Path]:
    with EVAL1_SUMMARY.open(newline="", encoding="utf-8") as source:
        row = next(csv.DictReader(source))

    stages = ["SHA-256", "pHash", "SSIM"]
    means = [
        float(row["Stage1TimeMsMean"]),
        float(row["Stage2TimeMsMean"]),
        float(row["Stage3TimeMsMean"]),
    ]
    deviations = [
        float(row["Stage1TimeMsStd"]),
        float(row["Stage2TimeMsStd"]),
        float(row["Stage3TimeMsStd"]),
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUTPUT_DIR / "figure-4-1-eval1-runtime-by-stage.png"
    svg_path = OUTPUT_DIR / "figure-4-1-eval1-runtime-by-stage.svg"

    fig, axis = plt.subplots(figsize=(8.2, 4.8), dpi=300)
    bars = axis.bar(
        stages,
        means,
        yerr=deviations,
        capsize=5,
        width=0.62,
        color=["#1C75BC", "#E66B4E", "#007F7B"],
        edgecolor="#263238",
        linewidth=0.7,
    )

    axis.set_ylabel("Mean runtime (ms)", fontsize=11)
    axis.set_ylim(0, max(means) * 1.16)
    axis.grid(axis="y", color="#D7DEE2", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    axis.spines[["left", "bottom"]].set_color("#7A878E")
    axis.tick_params(axis="both", labelsize=10, colors="#263238")

    for bar, mean, deviation in zip(bars, means, deviations):
        axis.text(
            bar.get_x() + bar.get_width() / 2,
            mean + deviation + max(means) * 0.025,
            f"{mean:.2f} +/- {deviation:.2f} ms",
            ha="center",
            va="bottom",
            fontsize=9.5,
            fontweight="bold",
            color="#263238",
        )

    fig.tight_layout(pad=0.8)
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png_path, svg_path


def build_eval2_detection_chart() -> tuple[Path, Path]:
    with EVAL2_DETECTION_SUMMARY.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))

    configurations = [row["ConfigID"] for row in rows]
    metric_series = {
        "Precision": ("Precision", "#1C75BC", "o"),
        "Recall": ("Recall", "#E66B4E", "s"),
        "F1 score": ("F1Score", "#007F7B", "^"),
        "Accuracy": ("Accuracy", "#6F5A9C", "D"),
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUTPUT_DIR / "figure-4-2-eval2-detection-by-configuration.png"
    svg_path = OUTPUT_DIR / "figure-4-2-eval2-detection-by-configuration.svg"

    fig, axis = plt.subplots(figsize=(8.2, 4.8), dpi=300)
    for label, (column, colour, marker) in metric_series.items():
        values = [float(row[column]) for row in rows]
        axis.plot(
            configurations,
            values,
            label=label,
            color=colour,
            marker=marker,
            markersize=6.5,
            linewidth=2,
        )

    axis.set_ylabel("Classification metric", fontsize=11)
    axis.set_ylim(0.90, 1.005)
    axis.set_yticks([0.90, 0.92, 0.94, 0.96, 0.98, 1.00])
    axis.grid(axis="y", color="#D7DEE2", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    axis.spines[["left", "bottom"]].set_color("#7A878E")
    axis.tick_params(axis="both", labelsize=10, colors="#263238")
    axis.legend(ncol=4, loc="lower center", frameon=False, fontsize=9.5)

    fig.tight_layout(pad=0.8)
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png_path, svg_path


def pair_key(first: str, second: str) -> tuple[str, str]:
    return tuple(sorted((first.strip(), second.strip())))


def build_eval3_transform_recall_chart() -> tuple[Path, Path]:
    with EVAL3_C1_PREDICTIONS.open(newline="", encoding="utf-8") as source:
        predictions = {
            pair_key(row["img_a"], row["img_b"])
            for row in csv.DictReader(source)
            if row["predicted_label"] == "1"
        }

    labels = {
        "Brightness": "brightness",
        "Contrast": "contrast",
        "Colour shift": "colour_shift",
        "JPEG recompression": "jpeg_recompress",
        "Resize": "resize",
        "Centre crop": "center_crop",
        "Rotation": "rotate",
        "PNG conversion": "convert_png",
    }
    totals = dict.fromkeys(labels.values(), 0)
    detected = dict.fromkeys(labels.values(), 0)

    with EVAL3_LABELS.open(newline="", encoding="utf-8") as source:
        for row in csv.DictReader(source):
            if row["label"] != "1":
                continue
            transform = row["notes"].split("transform=", 1)[1].split(";", 1)[0]
            totals[transform] += 1
            detected[transform] += pair_key(row["img_a"], row["img_b"]) in predictions

    names = list(labels)
    recalls = [100 * detected[key] / totals[key] for key in labels.values()]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUTPUT_DIR / "figure-4-3-eval3-recall-by-transformation.png"
    svg_path = OUTPUT_DIR / "figure-4-3-eval3-recall-by-transformation.svg"

    fig, axis = plt.subplots(figsize=(8.2, 5.0), dpi=300)
    bars = axis.barh(
        names,
        recalls,
        color=["#007F7B" if value >= 95 else "#E66B4E" for value in recalls],
        edgecolor="#263238",
        linewidth=0.6,
        height=0.62,
    )
    axis.invert_yaxis()
    axis.set_xlabel("Recall for labelled positive pairs (%)", fontsize=11)
    axis.set_xlim(0, 108)
    axis.set_xticks([0, 20, 40, 60, 80, 100])
    axis.grid(axis="x", color="#D7DEE2", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    axis.spines[["left", "bottom"]].set_color("#7A878E")
    axis.tick_params(axis="both", labelsize=9.5, colors="#263238")

    for bar, value in zip(bars, recalls):
        axis.text(
            max(value + 1.5, 1.5),
            bar.get_y() + bar.get_height() / 2,
            f"{value:.1f}%",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color="#263238",
        )

    fig.tight_layout(pad=0.8)
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png_path, svg_path


def build_eval4_scalability_chart() -> tuple[Path, Path]:
    with EVAL4_SCALABILITY.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))

    images = [int(row["ProcessedImages"]) for row in rows]
    runtimes = [float(row["MeanRuntimeSeconds"]) for row in rows]
    deviations = [float(row["StdDevRuntimeSeconds"]) for row in rows]
    workloads = [row["SizeKey"] for row in rows]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUTPUT_DIR / "figure-4-4-eval4-runtime-growth.png"
    svg_path = OUTPUT_DIR / "figure-4-4-eval4-runtime-growth.svg"

    fig, axis = plt.subplots(figsize=(8.2, 4.8), dpi=300)
    axis.errorbar(
        images,
        runtimes,
        yerr=deviations,
        color="#007F7B",
        marker="o",
        markersize=6.5,
        markerfacecolor="#F2B84B",
        markeredgecolor="#263238",
        linewidth=2,
        capsize=4,
    )
    for image_count, runtime, workload in zip(images, runtimes, workloads):
        axis.annotate(
            workload,
            (image_count, runtime),
            xytext=(0, 9),
            textcoords="offset points",
            ha="center",
            fontsize=9.5,
            fontweight="bold",
            color="#263238",
        )

    axis.set_xscale("log")
    axis.set_yscale("log")
    axis.set_xticks(images, [f"{value:,}" for value in images])
    axis.set_yticks([1, 10, 100, 1000], ["1", "10", "100", "1,000"])
    axis.set_xlabel("Processed images (log scale)", fontsize=11)
    axis.set_ylabel("Mean runtime in seconds (log scale)", fontsize=11)
    axis.grid(which="major", color="#D7DEE2", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines[["top", "right"]].set_visible(False)
    axis.spines[["left", "bottom"]].set_color("#7A878E")
    axis.tick_params(axis="both", labelsize=9.5, colors="#263238")

    fig.tight_layout(pad=0.8)
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png_path, svg_path


def build_eval4_runtime_composition_chart() -> tuple[Path, Path]:
    with EVAL4_RUNTIME_COMPOSITION.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))

    workloads = [row["Workload"] for row in rows]
    stage1 = [float(row["Stage1SHA256Percent"]) for row in rows]
    stage2 = [float(row["Stage2PHashPercent"]) for row in rows]
    stage3 = [float(row["Stage3SSIMPercent"]) for row in rows]
    positions = list(range(len(workloads)))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    png_path = OUTPUT_DIR / "figure-4-5-eval4-runtime-composition.png"
    svg_path = OUTPUT_DIR / "figure-4-5-eval4-runtime-composition.svg"

    fig, axis = plt.subplots(figsize=(8.2, 4.2), dpi=300)
    axis.barh(positions, stage1, height=0.58, color="#1C75BC", label="SHA-256")
    axis.barh(
        positions,
        stage2,
        left=stage1,
        height=0.58,
        color="#E66B4E",
        label="pHash",
    )
    stage3_left = [first + second for first, second in zip(stage1, stage2)]
    axis.barh(
        positions,
        stage3,
        left=stage3_left,
        height=0.58,
        color="#A9B4B8",
        label="SSIM",
    )

    for index, (phash, ssim, ssim_left) in enumerate(zip(stage2, stage3, stage3_left)):
        if phash >= 8:
            axis.text(
                stage1[index] + phash / 2,
                index,
                f"{phash:.1f}%",
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                color="white",
            )
        axis.text(
            ssim_left + ssim / 2,
            index,
            f"{ssim:.1f}%",
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color="#263238",
        )

    axis.set_yticks(positions, workloads)
    axis.invert_yaxis()
    axis.set_xlim(0, 100)
    axis.set_xlabel("Share of aggregate stage runtime (%)", fontsize=11)
    axis.grid(axis="x", color="#D7DEE2", linewidth=0.8)
    axis.set_axisbelow(True)
    axis.spines[:].set_visible(False)
    axis.tick_params(axis="both", labelsize=9.5, colors="#263238")
    axis.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.18), frameon=False)

    fig.tight_layout(pad=0.8)
    fig.savefig(png_path, dpi=300, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return png_path, svg_path


if __name__ == "__main__":
    outputs = (
        *build_cost_ordered_cascade_figure(),
        *build_eval1_runtime_chart(),
        *build_eval2_detection_chart(),
        *build_eval3_transform_recall_chart(),
        *build_eval4_scalability_chart(),
        *build_eval4_runtime_composition_chart(),
    )
    for output_path in outputs:
        print(output_path.relative_to(REPO_ROOT))
