"""Issue-local runner for the 2026-04-26 Suda parameter optimization Opus 4.7 sweep.

Adapted from
``test/issues/2026-04-17_tsuge10_md_claude47_effort_sweep/scripts/run_validation_model.py``
with the dataset configuration switched from Tsuge PRISMA validation (10 papers)
to the canonical Suda parameter optimization cohort (5 papers).

Why this exists: Anthropic released Claude Opus 4.7 during the rebuttal period,
after the manuscript's parameter optimization phase. The earlier 2026-04-17 sweep
selected the adaptive-thinking effort level on the Tsuge validation cohort, which
is the same set of 10 papers used to report Opus 4.7's validation accuracy. To
eliminate that methodological concern, this runner repeats the effort sweep on
the canonical 5-paper Suda parameter optimization cohort.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from prisma_evaluator.config import settings  # noqa: E402
from prisma_evaluator.core.pipeline import run_evaluation_pipeline  # noqa: E402
from prisma_evaluator.logging_config import setup_logging  # noqa: E402

ISSUE_DIR = Path(__file__).resolve().parents[1]
ISSUE_RESULTS_DIR = ISSUE_DIR / "results"
SCRIPTS_DIR = Path(__file__).resolve().parent
BUILD_UNIFIED = SCRIPTS_DIR / "build_unified_validation_json.py"
CHECK_COUNTS = SCRIPTS_DIR / "check_optimization_counts.py"

LOGGER = logging.getLogger("run_optimization_model")


def _load_paper_ids(path: Path) -> List[str]:
    papers: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        papers.append(line)
    if not papers:
        raise ValueError(f"No paper IDs found in {path}")
    return papers


def _sanitize(model_id: str) -> str:
    return model_id.replace("/", "_").replace(":", "_")


def _ensure_suda_dataset() -> None:
    settings.ENABLE_SUDA = True
    settings.ENABLE_TSUGE_OTHER = False
    settings.ENABLE_TSUGE_PRISMA = False


def _copy_raw(source_path: Path, dest_dir: Path) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / source_path.name
    shutil.copy2(source_path, dest_path)
    return dest_path


async def _run_pipeline(
    *,
    target_model_id: str,
    num_papers: int,
    format_type: str,
    paper_ids: List[str],
    gemini_params: Dict[str, Any],
) -> None:
    await run_evaluation_pipeline(
        target_model_id=target_model_id,
        target_format_type=format_type,
        num_papers_to_process=num_papers,
        gemini_params=gemini_params or None,
        paper_ids=paper_ids,
    )


def _resolve_raw_trio(
    source_dir: Path,
    target_model_id: str,
    format_type: str,
    before_names: set,
) -> Dict[str, Path]:
    model_safe = _sanitize(target_model_id)
    format_safe = format_type.replace("/", "_").replace(":", "_")
    shared_tail = f"_{model_safe}_{format_safe}_"

    candidates = {
        "ai_evaluations": sorted(source_dir.glob(f"ai_evaluations{shared_tail}*.json")),
        "accuracy_summary": sorted(source_dir.glob(f"accuracy_summary{shared_tail}*.json")),
        "comparison_details": sorted(source_dir.glob(f"comparison_details{shared_tail}*.json")),
    }

    resolved: Dict[str, Path] = {}
    missing: List[str] = []
    for kind, paths in candidates.items():
        new_paths = [p for p in paths if p.name not in before_names]
        if not new_paths:
            missing.append(kind)
            continue
        resolved[kind] = new_paths[-1]

    if missing:
        raise FileNotFoundError(
            "Pipeline did not produce all expected raw outputs "
            f"(missing: {missing}) under {source_dir}"
        )

    return resolved


def _extract_timestamp(path: Path) -> str:
    stem = path.stem
    parts = stem.rsplit("_", 2)
    if len(parts) < 3:
        raise ValueError(f"Cannot extract timestamp from {path.name}")
    date_part, time_part = parts[-2], parts[-1]
    if not (date_part.isdigit() and time_part.isdigit()):
        raise ValueError(f"Cannot extract timestamp from {path.name}")
    return f"{date_part}_{time_part}"


def _run_subprocess(cmd: List[str]) -> None:
    LOGGER.info("running: %s", " ".join(cmd))
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-id", required=True)
    parser.add_argument(
        "--paper-ids-file",
        type=Path,
        default=ISSUE_DIR / "data" / "suda_selected5.txt",
    )
    parser.add_argument("--paper-ids", type=str, default=None)
    parser.add_argument("--run-label", type=str, default=None)
    parser.add_argument("--schema-type", default="simple")
    parser.add_argument("--checklist-format", default="md")
    parser.add_argument("--order-mode", default="eande-first")
    parser.add_argument("--section-mode", default="off")
    parser.add_argument("--force-claude-native", action="store_true")
    parser.add_argument("--claude-effort", default=None,
                        choices=("low", "medium", "high", "xhigh", "max"))
    parser.add_argument("--keep-raw-in-source", action="store_true")
    parser.add_argument("--expected-size", choices=("smoke", "full"), default=None)
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    setup_logging(log_level_str=args.log_level.upper(), log_to_console=True)

    if args.paper_ids:
        paper_ids = [pid.strip() for pid in args.paper_ids.split(",") if pid.strip()]
    else:
        paper_ids = _load_paper_ids(args.paper_ids_file)

    LOGGER.info("Paper IDs (%d): %s", len(paper_ids), ", ".join(paper_ids))

    os.environ["ENABLE_SUDA"] = "true"
    os.environ["ENABLE_TSUGE_PRISMA"] = "false"
    os.environ["ENABLE_TSUGE_OTHER"] = "false"
    os.environ.setdefault("MAX_CONCURRENT_PAPERS", "1")

    _ensure_suda_dataset()
    settings.MAX_CONCURRENT_PAPERS = 1

    source_dir = settings.RESULTS_DIR
    source_dir.mkdir(parents=True, exist_ok=True)
    before_names = {p.name for p in source_dir.glob("*.json")}

    run_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    _suffix = f"_{args.claude_effort}" if args.claude_effort else ""
    format_type = args.run_label or f"md_{_sanitize(args.model_id)}{_suffix}_{run_timestamp}"

    gemini_params: Dict[str, Any] = {
        "schema_type": args.schema_type,
        "checklist_format": args.checklist_format,
        "order_mode": args.order_mode,
        "section_mode": args.section_mode,
    }
    if args.force_claude_native:
        gemini_params["force_claude_native"] = True
    if args.claude_effort:
        gemini_params["claude_effort"] = args.claude_effort

    LOGGER.info("Starting pipeline model=%s format=%s", args.model_id, format_type)
    LOGGER.info("gemini_params=%s", gemini_params)

    asyncio.run(
        _run_pipeline(
            target_model_id=args.model_id,
            num_papers=len(paper_ids),
            format_type=format_type,
            paper_ids=paper_ids,
            gemini_params=gemini_params,
        )
    )

    raw_trio = _resolve_raw_trio(
        source_dir=source_dir,
        target_model_id=args.model_id,
        format_type=format_type,
        before_names=before_names,
    )
    LOGGER.info("raw trio resolved: %s", raw_trio)

    run_ts_from_file = _extract_timestamp(raw_trio["ai_evaluations"])

    if not args.keep_raw_in_source:
        dest_dir = ISSUE_RESULTS_DIR
        dest_dir.mkdir(parents=True, exist_ok=True)
        copied = {}
        for kind, path in raw_trio.items():
            copied[kind] = _copy_raw(path, dest_dir)
            LOGGER.info("copied %s -> %s", path.name, copied[kind])
        raw_trio = copied

    cli_parameters = {
        "num_papers_to_process": len(paper_ids),
        "paper_ids_file": str(args.paper_ids_file),
        "schema_type": args.schema_type,
        "checklist_format": args.checklist_format,
        "order_mode": args.order_mode,
        "section_mode": args.section_mode,
        "force_claude_native": args.force_claude_native,
        "claude_effort": args.claude_effort,
    }
    actual_execution = {
        "runner_script": str(Path(__file__).relative_to(REPO_ROOT)),
        "raw_ai_evaluations": str(raw_trio["ai_evaluations"].relative_to(REPO_ROOT)),
        "raw_accuracy_summary": str(raw_trio["accuracy_summary"].relative_to(REPO_ROOT)),
        "raw_comparison_details": str(raw_trio["comparison_details"].relative_to(REPO_ROOT)),
    }
    dataset_info = {
        "sources": ["suda2025_merged"],
        "total_papers_available": len(paper_ids),
        "evaluated_papers": paper_ids,
        "num_papers_requested": len(paper_ids),
    }

    ISSUE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    build_cmd = [
        sys.executable,
        str(BUILD_UNIFIED),
        "--model-id", args.model_id,
        "--format-type", format_type,
        "--run-timestamp", run_ts_from_file,
        "--ai-evaluations", str(raw_trio["ai_evaluations"]),
        "--accuracy-summary", str(raw_trio["accuracy_summary"]),
        "--comparison-details", str(raw_trio["comparison_details"]),
        "--output-dir", str(ISSUE_RESULTS_DIR),
        "--cli-parameters", json.dumps(cli_parameters, ensure_ascii=False),
        "--actual-execution", json.dumps(actual_execution, ensure_ascii=False),
        "--dataset-info", json.dumps(dataset_info, ensure_ascii=False),
    ]
    _run_subprocess(build_cmd)

    unified_path = ISSUE_RESULTS_DIR / f"md_{_sanitize(args.model_id)}_{run_ts_from_file}.json"
    if not unified_path.exists():
        raise SystemExit(f"unified JSON not produced at {unified_path}")

    expected_size = args.expected_size or ("smoke" if len(paper_ids) == 1 else "full")
    check_cmd = [
        sys.executable,
        str(CHECK_COUNTS),
        str(unified_path),
        "--expected-size", expected_size,
    ]
    _run_subprocess(check_cmd)

    print(f"unified_json={unified_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
