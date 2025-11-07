#!/usr/bin/env python3
"""
Generate per-model macro metric dot chart (Markdown input runs).

Input:
    export/suda_multi_format_scaling/data/model_macro_metrics.csv
Output:
    paper/figures/model_macro_metrics.svg
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = REPO_ROOT / "export" / "suda_multi_format_scaling" / "data" / "model_macro_metrics.csv"
OUTPUT_PATH = Path(__file__).with_name("model_macro_metrics.svg")


METRICS = ["accuracy", "sensitivity", "specificity"]
# 本文Table 2の順序（上から下への表示のため、Y軸用に逆順で定義）
MODEL_DISPLAY_ORDER = [
    "x-ai/grok-4-fast",
    "x-ai/grok-4",
    "qwen/qwen3-max",
    "qwen/qwen3-235b-a22b-2507",
    "openai/gpt-oss-120b",
    "claude-sonnet-4-5-20250929",
    "claude-opus-4-1-20250805",
    "gemini-2.5-pro",
    "gpt-4o",
    "gpt-5",
]


def read_dataset(path: Path) -> List[Dict[str, float]]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")
    records: List[Dict[str, float]] = []
    with path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            # CSVの値は既にパーセント形式（69.81 = 69.81%）なので100倍しない
            records.append(
                {
                    "model": row["model"],
                    "accuracy": float(row["accuracy"]),
                    "sensitivity": float(row["sensitivity"]),
                    "specificity": float(row["specificity"]),
                }
            )
    if not records:
        raise RuntimeError("No records found in dataset.")
    return records


def compute_stats(records: List[Dict[str, float]]) -> Dict[str, Dict[str, Dict[str, float]]]:
    grouped: Dict[str, Dict[str, List[float]]] = {}
    for row in records:
        grouped.setdefault(row["model"], {metric: [] for metric in METRICS})
        for metric in METRICS:
            grouped[row["model"]][metric].append(row[metric])

    stats: Dict[str, Dict[str, Dict[str, float]]] = {}
    for model, metric_values in grouped.items():
        stats[model] = {}
        for metric, values in metric_values.items():
            mean = float(np.mean(values))
            if len(values) < 2:
                ci = 0.0
            else:
                std = float(np.std(values, ddof=1))
                ci = 1.96 * std / math.sqrt(len(values))
            stats[model][metric] = {"mean": mean, "ci": ci}
    return stats


def draw_chart(
    stats: Dict[str, Dict[str, Dict[str, float]]],
    output_path: Path,
    annotate: bool = False,
) -> None:
    # Match manuscript narrative order; append any unexpected models at the end.
    models = [model for model in MODEL_DISPLAY_ORDER if model in stats]
    remaining = sorted(set(stats.keys()) - set(models))
    models.extend(remaining)

    # モデル名をテーブル表記に統一（Table 2と同じ形式）
    def clean_model_name(model: str) -> str:
        # テーブル表記との完全一致
        name_map = {
            "gpt-5": "GPT‑5",
            "gpt-4o": "GPT‑4o",
            "gemini-2.5-pro": "Gemini 2.5 Pro",
            "claude-opus-4-1-20250805": "Claude Opus 4.1",
            "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5",
            "openai/gpt-oss-120b": "GPT‑OSS‑120B",
            "qwen/qwen3-235b-a22b-2507": "Qwen3‑235B",
            "qwen/qwen3-max": "Qwen3‑Max",
            "x-ai/grok-4": "Grok‑4",
            "x-ai/grok-4-fast": "Grok‑4‑fast",
        }
        return name_map.get(model, model)

    display_names = [clean_model_name(model) for model in models]
    y_positions = np.arange(len(models))

    colors = {"accuracy": "#1f77b4", "sensitivity": "#2ca02c", "specificity": "#d62728"}

    fig, axes = plt.subplots(
        nrows=len(METRICS),
        ncols=1,
        figsize=(9.2, 7.2),
        sharex=True,
        constrained_layout=True,
    )

    for ax, metric in zip(axes, METRICS):
        values = np.array([stats[model][metric]["mean"] for model in models])
        errors = np.array([stats[model][metric]["ci"] for model in models])

        ax.set_xlim(0, 100)
        ax.set_xticks(np.arange(0, 101, 10))
        ax.set_yticks(y_positions)
        ax.set_yticklabels(display_names, fontsize=11)
        ax.grid(axis="x", linestyle="--", alpha=0.3)
        ax.set_title(metric.capitalize(), fontsize=12, color=colors[metric], pad=8)

        ax.errorbar(
            values,
            y_positions,
            xerr=errors,
            fmt="o",
            color=colors[metric],
            ecolor=colors[metric],
            elinewidth=1.2,
            capsize=4,
            markersize=6,
            markeredgecolor="white",
            markeredgewidth=0.8,
        )

        if annotate:
            for i, (val, ci) in enumerate(zip(values, errors)):
                left = max(0.0, float(val - ci))
                right = min(100.0, float(val + ci))
                label = f"{val:.1f}% ({left:.1f}–{right:.1f})"
                x = right + 1.0
                ha = "left"
                if x > 98.5:
                    x = left - 1.0
                    ha = "right"
                x = min(98.5, max(1.5, x))
                ax.text(x, y_positions[i], label, va="center", ha=ha, fontsize=8, color="#555555")

    axes[-1].set_xlabel("Macro score (%)", fontsize=12)
    # Export SVG (journal-quality vector)
    fig.savefig(output_path, format="svg", facecolor="white")
    # Also export a PNG fallback for Markdown/IDE preview compatibility
    png_path = output_path.with_suffix(".png")
    fig.savefig(png_path, format="png", dpi=300, facecolor="white")
    plt.close(fig)


def main() -> None:
    records = read_dataset(DATA_PATH)
    stats = compute_stats(records)
    # Clean version (without annotations)
    draw_chart(stats, OUTPUT_PATH, annotate=False)
    print(
        f"Wrote figure to {OUTPUT_PATH} and {OUTPUT_PATH.with_suffix('.png')}"
    )


if __name__ == "__main__":
    main()
