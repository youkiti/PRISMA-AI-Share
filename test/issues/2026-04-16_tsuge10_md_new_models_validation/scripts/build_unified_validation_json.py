"""Combine raw evaluator outputs into a Figure-4-compatible unified JSON.

The production pipeline writes three files per run:

  * ``ai_evaluations_<model>_<format>_<timestamp>.json``
  * ``accuracy_summary_<model>_<format>_<timestamp>.json``
  * ``comparison_details_<model>_<format>_<timestamp>.json``

Figure 4, the validation CI recomputation, and the runtime/cost aggregator all
expect a single unified JSON whose shape matches
:class:`prisma_evaluator.schemas.UnifiedEvaluationResult`.  This helper glues the
three inputs back together and writes ``md_<model_safe>_<timestamp>.json``.

Used by ``scripts/run_validation_model.py``; can also be invoked directly.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _safe_model_slug(model_id: str) -> str:
    return model_id.replace("/", "_").replace(":", "_")


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def _token_summary(paper_evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
    token_counts: List[int] = []
    input_tokens = 0
    output_tokens = 0
    total_tokens = 0
    for paper in paper_evaluations:
        meta = paper.get("overall_metadata") or {}
        usage = meta.get("token_usage") or {}
        token_counts.append(int(meta.get("token_count") or 0))
        input_tokens += int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
        output_tokens += int(usage.get("output_tokens") or usage.get("completion_tokens") or 0)
        total_tokens += int(
            usage.get("total_tokens")
            or usage.get("total_token_count")
            or meta.get("token_count")
            or 0
        )

    if token_counts:
        mean = statistics.mean(token_counts)
        sd = statistics.pstdev(token_counts) if len(token_counts) > 1 else 0.0
        med = statistics.median(token_counts)
        try:
            q = statistics.quantiles(token_counts, n=4, method="inclusive")
            iqr = float(q[2] - q[0])
        except Exception:
            iqr = 0.0
    else:
        mean = sd = med = iqr = 0.0

    summary: Dict[str, Any] = {
        "mean": float(mean),
        "sd": float(sd),
        "median": float(med),
        "iqr": float(iqr),
    }
    if total_tokens or input_tokens or output_tokens:
        summary["usage_breakdown"] = {
            "input_tokens": float(input_tokens),
            "output_tokens": float(output_tokens),
            "total_tokens": float(total_tokens),
        }
    return summary


def _derive_time_bounds(paper_evaluations: List[Dict[str, Any]]) -> Dict[str, Any]:
    timestamps: List[datetime] = []
    processing_times: List[float] = []
    for paper in paper_evaluations:
        meta = paper.get("overall_metadata") or {}
        ts_raw = meta.get("timestamp")
        if isinstance(ts_raw, str):
            try:
                timestamps.append(datetime.fromisoformat(ts_raw.replace("Z", "+00:00")))
            except ValueError:
                try:
                    timestamps.append(datetime.strptime(ts_raw, "%Y-%m-%d %H:%M:%S.%f"))
                except ValueError:
                    pass
        pt = meta.get("processing_time")
        if isinstance(pt, (int, float)):
            processing_times.append(float(pt))

    bounds: Dict[str, Any] = {}
    if timestamps:
        bounds["start_time"] = min(timestamps).isoformat(sep=" ")
        bounds["end_time"] = max(timestamps).isoformat(sep=" ")
    if processing_times:
        bounds["total_processing_time"] = float(sum(processing_times))
    return bounds


def build_unified(
    ai_evaluations_path: Path,
    accuracy_summary_path: Path,
    comparison_details_path: Path,
    *,
    target_model_id: str,
    format_type: str,
    run_timestamp: str,
    cli_parameters: Optional[Dict[str, Any]] = None,
    actual_execution: Optional[Dict[str, Any]] = None,
    dataset_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    paper_evaluations = _load_json(ai_evaluations_path)
    if not isinstance(paper_evaluations, list):
        raise ValueError(
            f"ai_evaluations file is not a list: {ai_evaluations_path}"
        )
    accuracy_summary = _load_json(accuracy_summary_path)
    if not isinstance(accuracy_summary, dict):
        raise ValueError(
            f"accuracy_summary file is not an object: {accuracy_summary_path}"
        )
    comparison_details = _load_json(comparison_details_path)
    if not isinstance(comparison_details, list):
        raise ValueError(
            f"comparison_details file is not a list: {comparison_details_path}"
        )

    paper_ids = [p.get("paper_id") for p in paper_evaluations if p.get("paper_id")]
    total_token_count = 0
    for paper in paper_evaluations:
        meta = paper.get("overall_metadata") or {}
        total_token_count += int(meta.get("token_count") or 0)

    time_bounds = _derive_time_bounds(paper_evaluations)
    start_time = time_bounds.get("start_time") or f"{run_timestamp[:4]}-{run_timestamp[4:6]}-{run_timestamp[6:8]} {run_timestamp[9:11]}:{run_timestamp[11:13]}:{run_timestamp[13:15]}"
    end_time = time_bounds.get("end_time") or start_time

    experiment_metadata: Dict[str, Any] = {
        "experiment_id": run_timestamp,
        "start_time": start_time,
        "end_time": end_time,
        "total_processing_time": time_bounds.get("total_processing_time", 0.0),
        "total_token_count": total_token_count,
        "token_count_summary": _token_summary(paper_evaluations),
        "cli_parameters": {
            "target_model_id": target_model_id,
            "target_format_type": format_type,
            **(cli_parameters or {}),
        },
        "actual_execution": {
            "model_id_to_use": target_model_id,
            "format_type_to_use": format_type,
            **(actual_execution or {}),
        },
        "dataset_info": dataset_info
        or {
            "sources": ["tsuge2025_merged"],
            "total_papers_available": len(paper_ids),
            "evaluated_papers": paper_ids,
            "num_papers_requested": len(paper_ids),
        },
    }

    unified: Dict[str, Any] = {
        "experiment_metadata": experiment_metadata,
        "paper_evaluations": paper_evaluations,
        "overall_metrics": accuracy_summary.get("overall_metrics"),
        "main_body_metrics": accuracy_summary.get("main_body_metrics"),
        "abstract_metrics": accuracy_summary.get("abstract_metrics"),
        "item_specific_metrics": accuracy_summary.get("item_specific_metrics"),
        "comparison_details": comparison_details,
    }
    return unified


def _resolve_raw_paths(
    source_dir: Path,
    model_id: str,
    format_type: str,
    timestamp: str,
) -> Dict[str, Path]:
    model_safe = _safe_model_slug(model_id)
    format_safe = format_type.replace("/", "_").replace(":", "_")
    suffix = f"_{model_safe}_{format_safe}_{timestamp}.json"
    mapping = {
        "ai_evaluations": source_dir / f"ai_evaluations{suffix}",
        "accuracy_summary": source_dir / f"accuracy_summary{suffix}",
        "comparison_details": source_dir / f"comparison_details{suffix}",
    }
    missing = [str(path) for path in mapping.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "Could not locate raw evaluator outputs:\n  " + "\n  ".join(missing)
        )
    return mapping


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--format-type", required=True,
                        help="The --format value passed to the pipeline (e.g. md_<slug>_<ts>).")
    parser.add_argument("--run-timestamp", required=True,
                        help="Timestamp the pipeline used to stamp the raw output file names (YYYYMMDD_HHMMSS).")
    parser.add_argument("--source-dir", type=Path, default=Path("results/evaluator_output"))
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="Directory where the unified md_<slug>_<ts>.json will be written.")
    parser.add_argument("--ai-evaluations", type=Path,
                        help="Override for ai_evaluations_*.json path.")
    parser.add_argument("--accuracy-summary", type=Path,
                        help="Override for accuracy_summary_*.json path.")
    parser.add_argument("--comparison-details", type=Path,
                        help="Override for comparison_details_*.json path.")
    parser.add_argument("--cli-parameters", type=str, default=None,
                        help="JSON string recorded under experiment_metadata.cli_parameters.")
    parser.add_argument("--actual-execution", type=str, default=None,
                        help="JSON string recorded under experiment_metadata.actual_execution.")
    parser.add_argument("--dataset-info", type=str, default=None,
                        help="JSON string recorded under experiment_metadata.dataset_info.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.ai_evaluations and args.accuracy_summary and args.comparison_details:
        paths = {
            "ai_evaluations": args.ai_evaluations,
            "accuracy_summary": args.accuracy_summary,
            "comparison_details": args.comparison_details,
        }
    else:
        paths = _resolve_raw_paths(
            source_dir=args.source_dir,
            model_id=args.model_id,
            format_type=args.format_type,
            timestamp=args.run_timestamp,
        )

    cli_params = json.loads(args.cli_parameters) if args.cli_parameters else None
    actual_exec = json.loads(args.actual_execution) if args.actual_execution else None
    dataset_info = json.loads(args.dataset_info) if args.dataset_info else None

    unified = build_unified(
        ai_evaluations_path=paths["ai_evaluations"],
        accuracy_summary_path=paths["accuracy_summary"],
        comparison_details_path=paths["comparison_details"],
        target_model_id=args.model_id,
        format_type=args.format_type,
        run_timestamp=args.run_timestamp,
        cli_parameters=cli_params,
        actual_execution=actual_exec,
        dataset_info=dataset_info,
    )

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"md_{_safe_model_slug(args.model_id)}_{args.run_timestamp}.json"
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(unified, fp, ensure_ascii=False, indent=2, default=str)

    print(f"unified_json={output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
