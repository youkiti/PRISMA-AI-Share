#!/usr/bin/env python3
"""
フォーマット別マクロ指標のドットチャート（95%信頼区間付き）を生成するユーティリティ。

入力:
    export/suda_multi_format_scaling/reports/format_metrics.md
出力:
    paper/figures/format_macro_metrics.svg
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = REPO_ROOT / "export" / "suda_multi_format_scaling" / "reports" / "format_metrics.md"
OUTPUT_PATH = Path(__file__).with_name("format_macro_metrics.svg")


def load_section_lines(lines: List[str], header: str) -> List[str]:
    try:
        start = lines.index(header)
    except ValueError as exc:
        raise RuntimeError(f"セクション {header!r} が見つかりません。") from exc

    table_lines: List[str] = []
    for line in lines[start + 1 :]:
        if not line.strip():
            if table_lines:
                break
            continue
        if line.startswith("|"):
            table_lines.append(line)
            continue
        if table_lines:
            break
    if len(table_lines) < 3:
        raise RuntimeError(f"{header} の表が想定より短いです。")
    return table_lines


def parse_table(table_lines: List[str]) -> List[Dict[str, str]]:
    header = [cell.strip() for cell in table_lines[0].split("|")[1:-1]]
    data_rows: List[Dict[str, str]] = []
    for row in table_lines[2:]:
        cells = [cell.strip() for cell in row.split("|")[1:-1]]
        if len(cells) != len(header):
            raise RuntimeError(f"列数が一致しません: {cells}")
        data_rows.append(dict(zip(header, cells)))
    return data_rows


def to_float(value: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(f"数値に変換できません: {value}") from exc


def compute_mean_and_ci(values: List[float]) -> tuple[float, float]:
    if not values:
        raise RuntimeError("値が空です。")
    mean = float(np.mean(values))
    if len(values) < 2:
        return mean, 0.0
    std = float(np.std(values, ddof=1))
    stderr = std / math.sqrt(len(values))
    ci = 1.96 * stderr
    return mean, ci


def build_dataset() -> dict:
    lines = REPORT_PATH.read_text(encoding="utf-8").splitlines()
    macro_rows = parse_table(load_section_lines(lines, "## Format Macro Summary"))
    per_model_rows = parse_table(load_section_lines(lines, "## Per-Model Metrics"))

    # 希望する順序を定義
    desired_order = ["md", "json", "xml", "text", "none"]
    format_display_names = {
        "md": "Markdown",
        "json": "JSON",
        "xml": "XML",
        "text": "Plain text",
        "none": "Control"
    }

    metrics = ["Accuracy", "Sensitivity", "Specificity"]

    # 全フォーマットのデータを収集
    all_formats = set(row["Format"] for row in macro_rows)
    grouped_values: Dict[str, Dict[str, List[float]]] = {
        fmt: {metric: [] for metric in metrics} for fmt in all_formats
    }
    for row in per_model_rows:
        fmt = row["Format"]
        if fmt not in grouped_values:
            continue
        for metric in metrics:
            grouped_values[fmt][metric].append(to_float(row[metric]))

    # 指定された順序でラベルと統計値を構築（Y軸は下から上なので逆順にする）
    labels = [format_display_names[fmt] for fmt in reversed(desired_order) if fmt in all_formats]
    means = {metric: [] for metric in metrics}
    cis = {metric: [] for metric in metrics}
    for fmt in reversed(desired_order):
        if fmt not in all_formats:
            continue
        for metric in metrics:
            mean, ci = compute_mean_and_ci(grouped_values[fmt][metric])
            means[metric].append(mean)
            cis[metric].append(ci)

    return {"labels": labels, "metrics": metrics, "means": means, "cis": cis}


def draw_chart(dataset: dict) -> None:
    labels = dataset["labels"]
    metrics = dataset["metrics"]
    means = dataset["means"]
    cis = dataset["cis"]
    colors = {"Accuracy": "#1f77b4", "Sensitivity": "#2ca02c", "Specificity": "#d62728"}

    fig, axes = plt.subplots(
        nrows=len(metrics),
        ncols=1,
        figsize=(9.2, 7.2),
        sharex=True,
        constrained_layout=True,
    )

    y_positions = np.arange(len(labels))
    for ax, metric in zip(axes, metrics):
        values = np.array(means[metric])
        errors = np.array(cis[metric])

        ax.set_xlim(0, 100)
        ax.set_xticks(np.arange(0, 101, 10))
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels, fontsize=11)
        ax.grid(axis="x", linestyle="--", alpha=0.3)
        ax.set_title(f"{metric}", fontsize=12, color=colors[metric], pad=8)

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

    axes[-1].set_xlabel("Macro score (%)", fontsize=12)
    fig.savefig(OUTPUT_PATH, format="svg", facecolor="white")
    png_path = OUTPUT_PATH.with_suffix(".png")
    fig.savefig(png_path, format="png", dpi=300, facecolor="white")
    plt.close(fig)


def main() -> None:
    dataset = build_dataset()
    draw_chart(dataset)


if __name__ == "__main__":
    main()
