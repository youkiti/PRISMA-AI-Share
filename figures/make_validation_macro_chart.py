#!/usr/bin/env python3
"""
Generate validation-phase per-model macro metric dot chart.

Input:
    Reads unified JSON results from test/issues/2025-10-24_table2_runtime_cost/results/validation/
Output:
    paper/figures/validation_macro_metrics.svg
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
# Validation results directory
VALIDATION_DIR = REPO_ROOT / "test/issues/2025-10-23_tsuge_md_validation_metrics/results"
OUTPUT_PATH = Path(__file__).with_name("validation_macro_metrics.svg")


METRICS = ["accuracy", "sensitivity", "specificity"]
# Table 3の順序（上から下への表示のため、Y軸用に逆順で定義）
MODEL_DISPLAY_ORDER = [
    # First entry = bottom of chart. List is the reverse of the top→bottom
    # reading order used by compute_validation_ci.py so the figure matches
    # the CI table exactly.
    # Qwen family (at bottom of chart)
    "qwen/qwen3.6-plus",
    "qwen/qwen3-max",
    "qwen/qwen3-235b-a22b-2507",
    # GPT-OSS
    "openai/gpt-oss-120b",
    # Grok family
    "x-ai/grok-4.20",
    "x-ai/grok-4.1-fast",
    "x-ai/grok-4",
    "x-ai/grok-4-fast",
    # Gemini
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview",
    "gemini-3-pro",
    "gemini-2.5-pro",
    # Claude Opus
    "claude-opus-4-7",
    "claude-opus-4-1-20250805",
    # Claude Sonnet
    "claude-sonnet-4-5-20250929",
    # GPT (at top of chart)
    "gpt-5.4",
    "gpt-5.1",
    "gpt-5",
    "gpt-4o",
]


def wilson_ci(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """Calculate Wilson score confidence interval for a proportion."""
    if n == 0:
        return (0.0, 0.0)

    denom = 1 + (z * z) / n
    center = p + (z * z) / (2 * n)
    radius = z * math.sqrt((p * (1 - p) + (z * z) / (4 * n)) / n)

    lower = max(0.0, (center - radius) / denom)
    upper = min(1.0, (center + radius) / denom)

    return (lower, upper)


def extract_metrics_from_json(json_path: Path) -> Dict[str, float]:
    """Extract accuracy, sensitivity, specificity from a unified JSON result."""
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Get model ID from CLI parameters
    cli_params = data.get("experiment_metadata", {}).get("cli_parameters", {})
    model_id = (
        cli_params.get("target_model_id")
        or data.get("experiment_metadata", {}).get("actual_execution", {}).get("model_id_to_use")
        or json_path.stem
    )

    # Use overall_metrics which combines abstract and main body
    overall_metrics = data.get("overall_metrics", {})
    counts = overall_metrics.get("counts", {})

    tp_total = counts.get("tp", 0)
    tn_total = counts.get("tn", 0)
    fp_total = counts.get("fp", 0)
    fn_total = counts.get("fn", 0)

    total = tp_total + tn_total + fp_total + fn_total
    accuracy = (tp_total + tn_total) / total if total > 0 else 0.0

    sensitivity_denom = tp_total + fn_total
    sensitivity = tp_total / sensitivity_denom if sensitivity_denom > 0 else 0.0

    specificity_denom = tn_total + fp_total
    specificity = tn_total / specificity_denom if specificity_denom > 0 else 0.0

    # Calculate Wilson CIs
    acc_lower, acc_upper = wilson_ci(accuracy, total)
    sens_lower, sens_upper = wilson_ci(sensitivity, sensitivity_denom)
    spec_lower, spec_upper = wilson_ci(specificity, specificity_denom)

    return {
        "model": model_id,
        "accuracy": accuracy * 100,  # Convert to percentage
        "accuracy_lower": acc_lower * 100,
        "accuracy_upper": acc_upper * 100,
        "sensitivity": sensitivity * 100,
        "sensitivity_lower": sens_lower * 100,
        "sensitivity_upper": sens_upper * 100,
        "specificity": specificity * 100,
        "specificity_lower": spec_lower * 100,
        "specificity_upper": spec_upper * 100,
    }


def read_validation_results() -> Dict[str, Dict[str, float]]:
    """Read all validation JSON files and extract metrics."""
    if not VALIDATION_DIR.exists():
        raise FileNotFoundError(f"Validation directory not found: {VALIDATION_DIR}")

    results = {}
    for json_file in VALIDATION_DIR.glob("*.json"):
        if json_file.name.startswith("."):
            continue

        # Skip old/test files - only use files with proper timestamps
        valid_timestamps = ["20251023_184404", "20251119_070126", "20251119_074132", "20251120_152819", "20251218_082141", "20260416_194607", "20260416_200112", "20260416_201008", "20260416_205101", "20260417_075422"]
        if not any(ts in json_file.name for ts in valid_timestamps):
            continue

        metrics = extract_metrics_from_json(json_file)
        model_id = metrics["model"]
        results[model_id] = metrics

    if not results:
        raise RuntimeError(f"No validation results found in {VALIDATION_DIR}")

    return results


def draw_chart(stats: Dict[str, Dict[str, float]], output_path: Path) -> None:
    """Draw validation macro metrics chart."""
    # Match manuscript narrative order
    models = [model for model in MODEL_DISPLAY_ORDER if model in stats]
    remaining = sorted(set(stats.keys()) - set(models))
    models.extend(remaining)

    # モデル名をテーブル表記に統一
    def clean_model_name(model: str) -> str:
        name_map = {
            "gpt-5": "GPT‑5",
            "gpt-5.1": "GPT‑5.1",
            "gpt-5.4": "GPT‑5.4",
            "gpt-4o": "GPT‑4o",
            "gemini-2.5-pro": "Gemini 2.5 Pro",
            "gemini-3-pro": "Gemini 3 Pro",
            "gemini-3-flash-preview": "Gemini 3 Flash",
            "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
            "claude-opus-4-1-20250805": "Claude Opus 4.1",
            "claude-opus-4-7": "Claude Opus 4.7",
            "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5",
            "openai/gpt-oss-120b": "GPT‑OSS‑120B",
            "qwen/qwen3-235b-a22b-2507": "Qwen3‑235B",
            "qwen/qwen3-max": "Qwen3‑Max",
            "qwen/qwen3.6-plus": "Qwen3.6 Plus",
            "x-ai/grok-4": "Grok‑4",
            "x-ai/grok-4-fast": "Grok‑4‑fast",
            "x-ai/grok-4.1-fast": "Grok‑4.1‑fast",
            "x-ai/grok-4.20": "Grok‑4.20",
        }
        return name_map.get(model, model)

    display_names = [clean_model_name(model) for model in models]
    y_positions = np.arange(len(models))

    colors = {"accuracy": "#1f77b4", "sensitivity": "#2ca02c", "specificity": "#d62728"}

    fig, axes = plt.subplots(
        nrows=len(METRICS),
        ncols=1,
        figsize=(9.6, 12.0),  # Height sized for 18 models
        sharex=True,
        constrained_layout=True,
    )

    for ax, metric in zip(axes, METRICS):
        values = np.array([stats[model][metric] for model in models])
        lower_bounds = np.array([stats[model][f"{metric}_lower"] for model in models])
        upper_bounds = np.array([stats[model][f"{metric}_upper"] for model in models])

        # Calculate error bars (asymmetric)
        errors_lower = values - lower_bounds
        errors_upper = upper_bounds - values

        ax.set_xlim(0, 100)
        ax.set_xticks(np.arange(0, 101, 10))
        ax.set_yticks(y_positions)
        ax.set_yticklabels(display_names, fontsize=11)
        ax.grid(axis="x", linestyle="--", alpha=0.3)
        ax.set_title(metric.capitalize(), fontsize=12, color=colors[metric], pad=8)

        ax.errorbar(
            values,
            y_positions,
            xerr=[errors_lower, errors_upper],
            fmt="o",
            color=colors[metric],
            ecolor=colors[metric],
            elinewidth=1.2,
            capsize=4,
            markersize=6,
            markeredgecolor="white",
            markeredgewidth=0.8,
        )

    axes[-1].set_xlabel("Macro score (%)", fontsize=12)

    # Export SVG (journal-quality vector)
    fig.savefig(output_path, format="svg", facecolor="white")
    # Also export PNG fallback
    png_path = output_path.with_suffix(".png")
    fig.savefig(png_path, format="png", dpi=300, facecolor="white")
    plt.close(fig)


def main() -> None:
    stats = read_validation_results()
    draw_chart(stats, OUTPUT_PATH)
    print(f"Wrote validation figure to {OUTPUT_PATH} and {OUTPUT_PATH.with_suffix('.png')}")


if __name__ == "__main__":
    main()
