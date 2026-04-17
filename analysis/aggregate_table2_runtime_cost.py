#!/usr/bin/env python3
"""Aggregate runtime and API cost for Table 2 (Suda Markdown evaluations)."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

SCRIPT_PATH = Path(__file__).resolve()
ISSUE_DIR = SCRIPT_PATH.parents[1]
PROJECT_ROOT = SCRIPT_PATH.parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from prisma_evaluator.analysis.costs import calculate_run_cost, load_pricing_catalog  # noqa: E402

# Default directory that holds the Markdown runs for Table 2
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "test/issues/2025-09-27_suda_multi_format_scaling/results"

# Mapping from CLI model IDs to manuscript display names
MODEL_DISPLAY_NAMES: Dict[str, str] = {
    "gpt-5": "GPT‑5",
    "gpt-5.1": "GPT‑5.1",
    "gpt-5.4": "GPT‑5.4",
    "gpt-4o": "GPT‑4o",
    "gemini-2.5-pro": "Gemini 2.5 Pro",
    "gemini-3-pro": "Gemini 3 Pro",
    "gemini-3-flash-preview": "Gemini 3 Flash",
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro",
    "claude-opus-4-1-20250805": "Claude Opus 4.1",
    "claude-sonnet-4-5-20250929": "Claude Sonnet 4.5",
    "claude-opus-4-7": "Claude Opus 4.7",
    "openai/gpt-oss-120b": "GPT‑OSS‑120B",
    "qwen/qwen3-235b-a22b-2507": "Qwen3‑235B",
    "qwen/qwen3-max": "Qwen3‑Max",
    "qwen/qwen3.6-plus": "Qwen3.6 Plus",
    "x-ai/grok-4": "Grok‑4",
    "x-ai/grok-4-fast": "Grok‑4‑fast",
    "x-ai/grok-4.1-fast": "Grok‑4.1‑fast",
    "x-ai/grok-4.20": "Grok‑4.20",
}

FORMAT_KEY = "md"

# Cost figures from prisma_evaluator.analysis.costs assume per-million-token pricing.
# Keep unit conversion explicit in case reporting requirements change.
COST_UNIT_CONVERSION = 1.0


@dataclass
class Table2Row:
    model_id: str
    display_name: str
    source_file: str
    mean_time_seconds: Optional[float]
    median_time_seconds: Optional[float]
    total_cost_usd: Optional[float]
    mean_cost_per_sr_usd: Optional[float]
    notes: List[str]

    def to_serializable(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["mean_time_seconds"] = round(payload["mean_time_seconds"], 3) if self.mean_time_seconds is not None else None
        payload["median_time_seconds"] = round(payload["median_time_seconds"], 3) if self.median_time_seconds is not None else None
        payload["total_cost_usd"] = round(payload["total_cost_usd"], 6) if self.total_cost_usd is not None else None
        payload["mean_cost_per_sr_usd"] = round(payload["mean_cost_per_sr_usd"], 6) if self.mean_cost_per_sr_usd is not None else None
        return payload


def discover_markdown_results(results_dir: Path) -> List[Path]:
    """Return JSON files whose CLI parameters indicate Markdown format."""
    paths: List[Path] = []
    for json_path in sorted(results_dir.glob("*.json")):
        with json_path.open("r", encoding="utf-8") as fp:
            data = json.load(fp)
        cli_params = data.get("experiment_metadata", {}).get("cli_parameters", {})
        gemini_params = cli_params.get("gemini_params", {})
        format_hint = gemini_params.get("checklist_format") or cli_params.get("checklist_format") or cli_params.get("format_type")
        if format_hint == FORMAT_KEY:
            paths.append(json_path)
    return paths


def compute_row(json_path: Path) -> Table2Row:
    """Compute timing and cost aggregates from a single evaluator output."""
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    cli_params = payload.get("experiment_metadata", {}).get("cli_parameters", {})
    model_id = cli_params.get("target_model_id") or payload.get("experiment_metadata", {}).get("actual_execution", {}).get("model_id_to_use") or "unknown"

    pricing_catalog = load_pricing_catalog()
    cost_summary = calculate_run_cost(json_path, pricing_catalog=pricing_catalog)

    per_paper_times: List[float] = []
    for paper in payload.get("paper_evaluations", []):
        overall_meta = paper.get("overall_metadata", {})
        proc_time = overall_meta.get("processing_time")
        if proc_time is not None:
            per_paper_times.append(float(proc_time))

    mean_time = statistics.mean(per_paper_times) if per_paper_times else None
    median_time = statistics.median(per_paper_times) if per_paper_times else None

    costs = [
        paper.total_cost * COST_UNIT_CONVERSION
        for paper in cost_summary.papers
        if paper.total_cost is not None
    ]
    mean_cost = statistics.mean(costs) if costs else None
    total_cost = (
        cost_summary.total_cost * COST_UNIT_CONVERSION
        if cost_summary.total_cost is not None
        else None
    )

    notes = []
    if cost_summary.warnings:
        notes.extend(cost_summary.warnings)
    for paper in cost_summary.papers:
        notes.extend(paper.notes)

    display_name = MODEL_DISPLAY_NAMES.get(model_id, model_id)

    return Table2Row(
        model_id=model_id,
        display_name=display_name,
        source_file=json_path.name,
        mean_time_seconds=mean_time,
        median_time_seconds=median_time,
        total_cost_usd=total_cost,
        mean_cost_per_sr_usd=mean_cost,
        notes=sorted(set(notes)),
    )


def build_table(rows: Iterable[Table2Row]) -> List[Dict[str, object]]:
    return [row.to_serializable() for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Aggregate runtime and cost metrics for manuscript Table 2.")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="Directory containing evaluator JSON results (defaults to Suda multi-format results).",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ISSUE_DIR / "results" / "table2_runtime_cost.json",
        help="Path to save the aggregated runtime/cost table as JSON.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=ISSUE_DIR / "results" / "table2_runtime_cost.csv",
        help="Path to save the aggregated runtime/cost table as CSV.",
    )
    args = parser.parse_args()

    results_dir = args.results_dir
    if not results_dir.exists():
        raise SystemExit(f"Results directory does not exist: {results_dir}")

    json_paths = discover_markdown_results(results_dir)
    if not json_paths:
        raise SystemExit(f"No Markdown-format runs found in {results_dir}")

    rows = [compute_row(path) for path in json_paths]
    rows.sort(key=lambda r: r.display_name)

    table = build_table(rows)

    # Save JSON
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(table, indent=2, ensure_ascii=False), encoding="utf-8")

    # Save CSV
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", encoding="utf-8") as fp:
        fp.write("model,display_name,source_file,mean_time_seconds,median_time_seconds,total_cost_usd,mean_cost_per_sr_usd,notes\n")
        for row in table:
            fp.write(
                "{model},{display},{source},{mean_time},{median_time},{total_cost},{mean_cost},{notes}\n".format(
                    model=row["model_id"],
                    display=row["display_name"],
                    source=row["source_file"],
                    mean_time=row["mean_time_seconds"] if row["mean_time_seconds"] is not None else "",
                    median_time=row["median_time_seconds"] if row["median_time_seconds"] is not None else "",
                    total_cost=row["total_cost_usd"] if row["total_cost_usd"] is not None else "",
                    mean_cost=row["mean_cost_per_sr_usd"] if row["mean_cost_per_sr_usd"] is not None else "",
                    notes=";".join(row["notes"]) if row["notes"] else "",
                )
            )

    # Pretty-print summary to stdout
    for row in table:
        print(
            f"{row['display_name']}: mean_time={row['mean_time_seconds']}s, "
            f"median_time={row['median_time_seconds']}s, "
            f"mean_cost=${row['mean_cost_per_sr_usd']} per SR "
            f"(source={row['source_file']})"
        )


if __name__ == "__main__":
    main()
from prisma_evaluator.analysis.costs import calculate_run_cost, load_pricing_catalog  # noqa: E402

# When calculate_run_cost interprets pricing rates as per-million tokens,
# multiply by this factor to convert the result to per-thousand-token billing.
COST_UNIT_CONVERSION = 0.001
