"""Aggregate unified JSON outputs from the Grok-4.6 effort sweep.

For each unified JSON ``md_x-ai_grok-4.6_<timestamp>.json`` in the issue results
directory, extract overall metrics plus per-paper tokens and processing time,
compute cost through :func:`prisma_evaluator.analysis.costs.calculate_run_cost`
(which bills reasoning tokens that xAI reports outside ``output_tokens``), and
emit a comparison CSV + Markdown table.

The Markdown table leads with recall, which is the metric of interest for this
sweep: a PRISMA screening aid is judged first on how few reported items it
misses.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

ISSUE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_DIR = ISSUE_DIR / "results"
DEFAULT_REPORTS_DIR = ISSUE_DIR / "reports"
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from prisma_evaluator.analysis.costs import calculate_run_cost  # noqa: E402

EFFORTS = ("low", "medium")


def _sanitize(model_id: str) -> str:
    return model_id.replace("/", "_").replace(":", "_")


def _read_effort(path: Path) -> Optional[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    cli = (data.get("experiment_metadata") or {}).get("cli_parameters") or {}
    return cli.get("gpt5_reasoning")


def _latest_per_effort(results_dir: Path, model_id: str) -> Dict[str, Path]:
    latest: Dict[str, Path] = {}
    for f in sorted(results_dir.glob(f"md_{_sanitize(model_id)}_*.json")):
        effort = _read_effort(f)
        if not effort:
            continue
        prev = latest.get(effort)
        if prev is None or f.stat().st_mtime > prev.stat().st_mtime:
            latest[effort] = f
    return latest


def _paper_processing_time(paper: Dict[str, Any]) -> float:
    sets = paper.get("evaluation_sets", {}) or {}
    total = 0.0
    for _, es in sets.items():
        pm = es.get("processing_metadata", {}) or {}
        total += float(pm.get("processing_time") or 0.0)
    return total


def summarize(unified_path: Path) -> Dict[str, Any]:
    data = json.loads(unified_path.read_text(encoding="utf-8"))
    om = data.get("overall_metrics") or {}
    mb = data.get("main_body_metrics") or {}
    ab = data.get("abstract_metrics") or {}
    counts = om.get("counts", {}) or {}

    cli = (data.get("experiment_metadata") or {}).get("cli_parameters") or {}
    effort_metadata = cli.get("gpt5_reasoning")

    times = [_paper_processing_time(p) for p in data.get("paper_evaluations", [])]
    papers = len(times)
    mean_time = statistics.mean(times) if times else 0.0

    cost = calculate_run_cost(unified_path)
    cost_per_paper = (cost.total_cost / papers) if (cost.total_cost is not None and papers) else None

    return {
        "file": unified_path.name,
        "effort_metadata": effort_metadata,
        "papers": papers,
        "overall_total": counts.get("total_comparable"),
        "main_total": (mb.get("counts") or {}).get("total_comparable"),
        "abs_total": (ab.get("counts") or {}).get("total_comparable"),
        "recall": om.get("recall"),
        "precision": om.get("precision"),
        "f1": om.get("f1_score"),
        "accuracy": om.get("accuracy"),
        "specificity": om.get("specificity"),
        "cohen_kappa": om.get("cohen_kappa"),
        "false_negatives": counts.get("fn"),
        "false_positives": counts.get("fp"),
        "main_recall": mb.get("recall"),
        "abstract_recall": ab.get("recall"),
        "input_tokens_total": cost.total_prompt_tokens,
        "output_tokens_reported": cost.total_completion_tokens,
        "output_tokens_billed": cost.total_billed_output_tokens,
        "reasoning_tokens_total": cost.total_reasoning_tokens,
        "total_tokens": cost.total_tokens,
        "mean_proc_time_per_paper_sec": mean_time,
        "total_proc_time_sec": sum(times),
        "pricing_model_id": cost.pricing_model_id,
        "cost_total_usd": cost.total_cost,
        "cost_per_paper_usd": cost_per_paper,
        "cost_warnings": "; ".join(cost.warnings) if cost.warnings else "",
    }


def render_markdown(rows: List[Dict[str, Any]]) -> str:
    header = (
        "| effort | Rec | Prec | F1 | Acc | Spec | κ | FN | FP | mean t/SR (s) "
        "| billed out tokens | $/SR |"
    )
    sep = "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
    lines = [header, sep]
    for r in rows:
        def _fmt(v, spec=".2f"):
            if v is None:
                return "—"
            try:
                return format(v, spec)
            except Exception:
                return str(v)
        lines.append(
            f"| {r['effort_metadata'] or '?'} "
            f"| {_fmt(r['recall'])} | {_fmt(r['precision'])} | {_fmt(r['f1'])} | {_fmt(r['accuracy'])} "
            f"| {_fmt(r['specificity'])} | {_fmt(r['cohen_kappa'], '.4f')} "
            f"| {r['false_negatives'] if r['false_negatives'] is not None else '—'} "
            f"| {r['false_positives'] if r['false_positives'] is not None else '—'} "
            f"| {_fmt(r['mean_proc_time_per_paper_sec'], '.1f')} "
            f"| {r['output_tokens_billed']:,} "
            f"| {_fmt(r['cost_per_paper_usd'], '.4f')} |"
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    p.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    p.add_argument("--model-id", default="x-ai/grok-4.6")
    p.add_argument("--label", default="effort_comparison",
                   help="Base name for the emitted CSV/Markdown reports.")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.reports_dir.mkdir(parents=True, exist_ok=True)

    latest = _latest_per_effort(args.results_dir, args.model_id)
    if not latest:
        print(f"no unified JSON files under {args.results_dir}", file=sys.stderr)
        return 1

    rows: List[Dict[str, Any]] = []
    for effort in EFFORTS:
        path = latest.get(effort)
        if not path:
            print(f"WARN: no unified JSON found for effort={effort}", file=sys.stderr)
            continue
        rows.append(summarize(path))

    csv_path = args.reports_dir / f"{args.label}.csv"
    if rows:
        fieldnames = list(rows[0].keys())
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"wrote {csv_path}")

    md_path = args.reports_dir / f"{args.label}.md"
    md_path.write_text(render_markdown(rows) + "\n", encoding="utf-8")
    print(f"wrote {md_path}")

    print("\n=== Summary ===")
    print(render_markdown(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
