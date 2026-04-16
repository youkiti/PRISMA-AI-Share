#!/usr/bin/env python3
"""Summarize Qwen/OpenRouter structured-output stability for rebuttal use."""

from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import mean, median

ISSUE_DIR = Path("test/issues/2026-04-16_qwen_json_validity_rebuttal")
LOG_DIR = ISSUE_DIR / "logs"
RAW_DIR = ISSUE_DIR / "results/raw"
REPORT_JSON = ISSUE_DIR / "reports/summary.json"
REPORT_MD = ISSUE_DIR / "reports/summary.md"
PAPER_ID = "Suda2025_15"

INITIAL_SUCCESS_RE = re.compile(r"Initial evaluation: 42 success, 0 failed")
JSON_ERROR_RE = re.compile(rf"JSON decode error for '{re.escape(PAPER_ID)}', type 'main'")
VALIDATION_OK_RE = re.compile(r"Validation succeeded")
ELAPSED_RE = re.compile(r"Elapsed ([0-9]+(?:\.[0-9]+)?)s")


def list_runs() -> list[str]:
    run_ids = set()
    for path in LOG_DIR.glob("run_*.log"):
        run_ids.add(path.stem.replace("run_", ""))
    for path in RAW_DIR.glob("*.json"):
        match = re.search(r"run_(\d{3})", path.name)
        if match:
            run_ids.add(match.group(1))
    return sorted(run_ids)


def find_result_for_run(run_id: str) -> Path | None:
    candidates = sorted(RAW_DIR.glob(f"*run_{run_id}*.json"))
    if candidates:
        return candidates[-1]
    return None


def inspect_result(json_path: Path) -> dict[str, object]:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"found": False}

    for paper_eval in data.get("paper_evaluations") or []:
        if not isinstance(paper_eval, dict) or paper_eval.get("paper_id") != PAPER_ID:
            continue
        main_set = ((paper_eval.get("evaluation_sets") or {}).get("main") or {})
        evaluations = main_set.get("evaluations") or {}
        if not isinstance(evaluations, dict):
            evaluations = {}

        failed_items = sorted(
            item_id
            for item_id, item_eval in evaluations.items()
            if isinstance(item_eval, dict)
            and str(item_eval.get("reason", "")).startswith("Failed after ")
        )
        processing = main_set.get("processing_metadata") or {}
        token_count = processing.get("token_count")
        processing_time = processing.get("processing_time")
        return {
            "found": True,
            "final_failure_count": len(failed_items),
            "failed_items": failed_items,
            "token_count": token_count,
            "processing_time": processing_time,
        }

    return {"found": False}


def main() -> None:
    run_ids = list_runs()
    rows: list[dict[str, object]] = []

    for run_id in run_ids:
        log_path = LOG_DIR / f"run_{run_id}.log"
        log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        result_path = find_result_for_run(run_id)
        result_info = inspect_result(result_path) if result_path else {"found": False}

        elapsed = None
        elapsed_match = ELAPSED_RE.search(log_text)
        if elapsed_match:
            elapsed = float(elapsed_match.group(1))

        row = {
            "run_id": run_id,
            "log_file": str(log_path) if log_path.exists() else None,
            "result_file": str(result_path) if result_path else None,
            "validation_succeeded": bool(VALIDATION_OK_RE.search(log_text)),
            "main_initial_full_success": bool(INITIAL_SUCCESS_RE.search(log_text)),
            "main_json_decode_error": bool(JSON_ERROR_RE.search(log_text)),
            "main_final_failure_count": int(result_info.get("final_failure_count", 0) or 0),
            "main_final_failures_present": bool(result_info.get("final_failure_count", 0)),
            "main_failed_items": result_info.get("failed_items", []),
            "elapsed_seconds_cli_wrapper": elapsed,
            "main_processing_time": result_info.get("processing_time"),
            "main_token_count": result_info.get("token_count"),
        }
        rows.append(row)

    total_runs = len(rows)
    if total_runs == 0:
        raise SystemExit("No runs found under logs/ or results/raw/")

    initial_success_runs = sum(1 for row in rows if row["main_initial_full_success"])
    json_error_runs = sum(1 for row in rows if row["main_json_decode_error"])
    final_failure_runs = sum(1 for row in rows if row["main_final_failures_present"])
    validation_success_runs = sum(1 for row in rows if row["validation_succeeded"])
    retry_recovered_runs = sum(
        1
        for row in rows
        if (not row["main_initial_full_success"]) and (not row["main_final_failures_present"])
    )

    processing_times = [
        float(row["main_processing_time"])
        for row in rows
        if isinstance(row["main_processing_time"], (int, float))
    ]
    token_counts = [
        int(row["main_token_count"])
        for row in rows
        if isinstance(row["main_token_count"], (int, float))
    ]

    summary = {
        "experiment": {
            "issue_dir": str(ISSUE_DIR),
            "paper_id": PAPER_ID,
            "total_runs": total_runs,
        },
        "metrics": {
            "initial_full_success_runs": initial_success_runs,
            "initial_full_success_rate": initial_success_runs / total_runs,
            "json_decode_error_runs": json_error_runs,
            "json_decode_error_rate": json_error_runs / total_runs,
            "retry_recovered_runs": retry_recovered_runs,
            "retry_recovered_rate": retry_recovered_runs / total_runs,
            "final_failure_runs": final_failure_runs,
            "final_failure_rate": final_failure_runs / total_runs,
            "validation_success_runs": validation_success_runs,
            "validation_success_rate": validation_success_runs / total_runs,
        },
        "timing": {
            "main_processing_time_mean": mean(processing_times) if processing_times else None,
            "main_processing_time_median": median(processing_times) if processing_times else None,
        },
        "tokens": {
            "main_token_count_mean": mean(token_counts) if token_counts else None,
            "main_token_count_median": median(token_counts) if token_counts else None,
        },
        "runs": rows,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# Qwen JSON Validity Summary",
        "",
        f"Paper ID: `{PAPER_ID}`",
        f"Total runs: `{total_runs}`",
        "",
        "## Main Results",
        "",
        f"- Initial full success: `{initial_success_runs}/{total_runs}` ({summary['metrics']['initial_full_success_rate']:.1%})",
        f"- JSON decode errors: `{json_error_runs}/{total_runs}` ({summary['metrics']['json_decode_error_rate']:.1%})",
        f"- Retry recovered: `{retry_recovered_runs}/{total_runs}` ({summary['metrics']['retry_recovered_rate']:.1%})",
        f"- Final failures after retry: `{final_failure_runs}/{total_runs}` ({summary['metrics']['final_failure_rate']:.1%})",
        f"- Wrapper validation succeeded: `{validation_success_runs}/{total_runs}` ({summary['metrics']['validation_success_rate']:.1%})",
        "",
    ]

    if processing_times:
        md_lines.append(
            f"- Main processing time: mean `{summary['timing']['main_processing_time_mean']:.2f}s`, median `{summary['timing']['main_processing_time_median']:.2f}s`"
        )
    if token_counts:
        md_lines.append(
            f"- Main token count: mean `{summary['tokens']['main_token_count_mean']:.1f}`, median `{summary['tokens']['main_token_count_median']:.1f}`"
        )

    md_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The rebuttal-facing headline number is the initial full success rate, which measures how often the main checklist evaluation was fully parseable before any item-level retry. Retry recovered runs quantify cases where the first-pass structured output was unstable but the pipeline still salvaged the evaluation. Final failure runs quantify unresolved cases after all retries.",
            "",
            "## Files",
            "",
            f"- JSON summary: `{REPORT_JSON}`",
            f"- Raw outputs: `{RAW_DIR}`",
            f"- Logs: `{LOG_DIR}`",
        ]
    )
    REPORT_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Wrote {REPORT_JSON}")
    print(f"Wrote {REPORT_MD}")


if __name__ == "__main__":
    main()
