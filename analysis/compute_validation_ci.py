from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

Z_95 = 1.96  # 95% confidence level for Wilson interval


@dataclass(frozen=True)
class MetricCI:
    label: str
    point: float
    lower: float
    upper: float

    def as_percentage_tuple(self) -> tuple[str, str]:
        """Return formatted point estimate and CI range."""
        point_pct = f"{self.point * 100:.2f}%"
        ci_range = f"{self.lower * 100:.2f}–{self.upper * 100:.2f}%"
        return point_pct, ci_range


@dataclass(frozen=True)
class ModelMetrics:
    model_id: str
    display_name: str
    accuracy: MetricCI
    sensitivity: MetricCI
    specificity: MetricCI

    def as_markdown_row(self) -> str:
        acc_point, acc_ci = self.accuracy.as_percentage_tuple()
        sens_point, sens_ci = self.sensitivity.as_percentage_tuple()
        spec_point, spec_ci = self.specificity.as_percentage_tuple()
        return (
            f"| {self.display_name} | {acc_point} | {acc_ci} | "
            f"{sens_point} | {sens_ci} | {spec_point} | {spec_ci} |"
        )


MODEL_NAME_OVERRIDES: dict[str, str] = {
    "gpt-5": "GPT-5",
    "gpt-5.1": "GPT-5.1",
    "gpt-5.4": "GPT-5.4",
    "gpt-4o": "GPT-4o",
    "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5",
    "claude-opus-4-1-20250805": "Claude Opus 4.1",
    "claude-opus-4-7": "Claude Opus 4.7",
    "google/gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini-3-pro": "Gemini 3 Pro",
    "gemini-3-flash-preview": "Gemini 3 Flash",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
    "x-ai/grok-4-fast": "Grok-4 Fast",
    "x-ai/grok-4": "Grok-4",
    "x-ai/grok-4.1-fast": "Grok-4.1 Fast",
    "x-ai/grok-4.20": "Grok-4.20",
    "openai/gpt-oss-120b": "GPT-OSS-120B",
    "qwen/qwen3-235b-a22b-2507": "Qwen3-235B",
    "qwen/qwen3-max": "Qwen3-Max",
    "qwen/qwen3.6-plus": "Qwen3.6 Plus",
}


def compute_wilson_interval(successes: int, total: int, *, z: float = Z_95) -> MetricCI:
    if total <= 0:
        raise ValueError("Total count must be positive for interval computation.")
    p_hat = successes / total
    z_sq = z**2
    denom = 1 + z_sq / total
    center = (p_hat + (z_sq / (2 * total))) / denom
    half_width = z * math.sqrt((p_hat * (1 - p_hat) / total) + (z_sq / (4 * total**2))) / denom
    lower = max(0.0, center - half_width)
    upper = min(1.0, center + half_width)
    return MetricCI(label="", point=p_hat, lower=lower, upper=upper)


def load_result(path: Path) -> ModelMetrics:
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    overall = payload["overall_metrics"]
    counts = overall["counts"]
    cli_parameters = payload["experiment_metadata"]["cli_parameters"]
    model_id = cli_parameters["target_model_id"]
    display_name = MODEL_NAME_OVERRIDES.get(model_id, model_id)

    total = counts["total_comparable"]
    correct = counts["correct"]
    tp = counts["tp"]
    fn = counts["fn"]
    tn = counts["tn"]
    fp = counts["fp"]

    accuracy = compute_wilson_interval(correct, total)
    sensitivity = compute_wilson_interval(tp, tp + fn)
    specificity = compute_wilson_interval(tn, tn + fp)

    return ModelMetrics(
        model_id=model_id,
        display_name=display_name,
        accuracy=accuracy,
        sensitivity=sensitivity,
        specificity=specificity,
    )


def iter_result_files(base_dir: Path) -> Iterable[Path]:
    for path in sorted(base_dir.glob("md_*.json")):
        if not path.is_file():
            continue
        # Skip intermediate runs without aggregated metrics.
        try:
            with path.open("r", encoding="utf-8") as f:
                payload = json.load(f)
        except json.JSONDecodeError:
            continue
        if "overall_metrics" not in payload or "counts" not in payload["overall_metrics"]:
            continue
        yield path


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    issue_dir = script_dir.parent
    previous_issue_dir = issue_dir.parent / "2025-10-23_tsuge_md_validation_metrics"
    result_dir = previous_issue_dir / "results"

    if not result_dir.exists():
        raise SystemExit(f"Expected results directory not found: {result_dir}")

    metrics: list[ModelMetrics] = []
    for path in iter_result_files(result_dir):
        metrics.append(load_result(path))

    if not metrics:
        raise SystemExit("No result files with aggregate metrics were found.")

    order = [
        "gpt-4o",
        "gpt-5",
        "gpt-5.1",
        "gpt-5.4",
        "claude-sonnet-4-5-20250929",
        "claude-opus-4-1-20250805",
        "claude-opus-4-7",
        "google/gemini-2.5-pro",
        "gemini-2.5-pro",
        "gemini-3-pro",
        "gemini-3-flash-preview",
        "gemini-3.1-pro-preview",
        "x-ai/grok-4-fast",
        "x-ai/grok-4",
        "x-ai/grok-4.1-fast",
        "x-ai/grok-4.20",
        "openai/gpt-oss-120b",
        "qwen/qwen3-235b-a22b-2507",
        "qwen/qwen3-max",
        "qwen/qwen3.6-plus",
    ]
    order_map = {model_id: index for index, model_id in enumerate(order)}
    metrics.sort(key=lambda m: order_map.get(m.model_id, len(order)))

    header = (
        "| Model | Accuracy | 95% CI | Sensitivity | 95% CI | Specificity | 95% CI |\n"
        "|-------|----------|--------|-------------|--------|-------------|--------|\n"
    )
    rows = "\n".join(m.as_markdown_row() for m in metrics)
    table = header + rows + "\n"

    output_path = issue_dir / "reports" / "validation_ci_summary.md"
    output_path.write_text(
        "# Validation Metrics with 95% Confidence Intervals\n\n" + table,
        encoding="utf-8",
    )

    print(f"Wrote CI summary to {output_path.relative_to(issue_dir)}")


if __name__ == "__main__":
    main()
