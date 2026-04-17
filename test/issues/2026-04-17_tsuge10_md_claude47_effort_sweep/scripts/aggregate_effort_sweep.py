"""Aggregate unified JSON outputs from the Opus 4.7 effort sweep.

For each unified JSON md_claude-opus-4-7_<effort>_<timestamp>.json in
the issue results directory, extract overall metrics plus per-paper
tokens and processing time, compute per-SR cost via the pricing TOML,
and emit a single comparison CSV + Markdown table.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
import tomllib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ISSUE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS_DIR = ISSUE_DIR / "results"
DEFAULT_REPORTS_DIR = ISSUE_DIR / "reports"
REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PRICING = REPO_ROOT / "data" / "pricing" / "model_pricing.toml"

EFFORTS = ("low", "medium", "high", "xhigh", "max")
FILE_RE = re.compile(
    r"^md_claude-opus-4-7_(?P<ts>\d{8}_\d{6})\.json$"
)


def _read_effort(path: Path) -> Optional[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    for paper in data.get("paper_evaluations", []) or []:
        for _, es in (paper.get("evaluation_sets") or {}).items():
            pm = es.get("processing_metadata") or {}
            if pm.get("effort"):
                return pm["effort"]
    return None


def _load_pricing(path: Path, model_id: str) -> Optional[Tuple[float, float]]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    for entry in data.get("models", []):
        aliases = set(entry.get("aliases", []))
        aliases.add(entry.get("id"))
        if model_id in aliases:
            if entry.get("billing_strategy") == "simple":
                return (float(entry["input_rate"]), float(entry["output_rate"]))
    return None


def _latest_per_effort(results_dir: Path) -> Dict[str, Path]:
    latest: Dict[str, Path] = {}
    for f in sorted(results_dir.glob("md_claude-opus-4-7_*.json")):
        if not FILE_RE.match(f.name):
            continue
        effort = _read_effort(f)
        if not effort:
            continue
        prev = latest.get(effort)
        if prev is None or f.stat().st_mtime > prev.stat().st_mtime:
            latest[effort] = f
    return latest


def _summarize_paper_metadata(paper: Dict[str, Any]) -> Dict[str, Any]:
    sets = paper.get("evaluation_sets", {}) or {}
    total_tokens = 0
    input_tokens = 0
    output_tokens = 0
    proc_time = 0.0
    effort = None
    for _, es in sets.items():
        pm = es.get("processing_metadata", {}) or {}
        tu = pm.get("token_usage", {}) or {}
        total_tokens += int(pm.get("token_count") or 0)
        input_tokens += int(tu.get("input_tokens", 0) or 0)
        output_tokens += int(tu.get("output_tokens", 0) or 0)
        proc_time += float(pm.get("processing_time") or 0.0)
        if effort is None and pm.get("effort"):
            effort = pm.get("effort")
    return {
        "total_tokens": total_tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "processing_time": proc_time,
        "effort": effort,
    }


def summarize(
    unified_path: Path,
    input_rate: Optional[float],
    output_rate: Optional[float],
) -> Dict[str, Any]:
    data = json.loads(unified_path.read_text(encoding="utf-8"))
    om = (data.get("overall_metrics") or {})
    mb = (data.get("main_body_metrics") or {})
    ab = (data.get("abstract_metrics") or {})
    counts = om.get("counts", {}) or {}

    per_paper = [
        _summarize_paper_metadata(p) for p in data.get("paper_evaluations", [])
    ]
    papers = len(per_paper)
    sum_input = sum(p["input_tokens"] for p in per_paper)
    sum_output = sum(p["output_tokens"] for p in per_paper)
    sum_tokens = sum(p["total_tokens"] for p in per_paper)
    sum_time = sum(p["processing_time"] for p in per_paper)
    mean_time = statistics.mean([p["processing_time"] for p in per_paper]) if per_paper else 0.0
    effort_metadata = next((p["effort"] for p in per_paper if p["effort"]), None)

    cost_usd = None
    if input_rate is not None and output_rate is not None and papers:
        cost_usd = (
            (sum_input / 1_000_000.0) * input_rate
            + (sum_output / 1_000_000.0) * output_rate
        )

    return {
        "file": unified_path.name,
        "effort_metadata": effort_metadata,
        "papers": papers,
        "overall_total": counts.get("total_comparable"),
        "main_total": (mb.get("counts") or {}).get("total_comparable"),
        "abs_total": (ab.get("counts") or {}).get("total_comparable"),
        "accuracy": om.get("accuracy"),
        "precision": om.get("precision"),
        "recall": om.get("recall"),
        "f1": om.get("f1_score"),
        "specificity": om.get("specificity"),
        "cohen_kappa": om.get("cohen_kappa"),
        "input_tokens_total": sum_input,
        "output_tokens_total": sum_output,
        "total_tokens": sum_tokens,
        "mean_proc_time_per_paper_sec": mean_time,
        "total_proc_time_sec": sum_time,
        "cost_total_usd": cost_usd,
        "cost_per_paper_usd": (cost_usd / papers) if (cost_usd is not None and papers) else None,
    }


def render_markdown(rows: List[Dict[str, Any]]) -> str:
    header = (
        "| effort | Acc | Prec | Rec | F1 | Spec | κ | mean t/SR (s) | tokens | $/SR |"
    )
    sep = "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"
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
            f"| {_fmt(r['accuracy'])} | {_fmt(r['precision'])} | {_fmt(r['recall'])} | {_fmt(r['f1'])} "
            f"| {_fmt(r['specificity'])} | {_fmt(r['cohen_kappa'], '.4f')} "
            f"| {_fmt(r['mean_proc_time_per_paper_sec'], '.1f')} "
            f"| {r['total_tokens']:,} "
            f"| {_fmt(r['cost_per_paper_usd'], '.4f')} |"
        )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    p.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    p.add_argument("--pricing", type=Path, default=DEFAULT_PRICING)
    p.add_argument("--model-id", default="claude-opus-4-7")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.reports_dir.mkdir(parents=True, exist_ok=True)

    rates = _load_pricing(args.pricing, args.model_id) if args.pricing.exists() else None
    input_rate, output_rate = (rates or (None, None))
    if rates is None:
        print(f"WARN: pricing entry for {args.model_id} not found in {args.pricing}", file=sys.stderr)

    latest = _latest_per_effort(args.results_dir)
    if not latest:
        print(f"no unified JSON files under {args.results_dir}", file=sys.stderr)
        return 1

    rows: List[Dict[str, Any]] = []
    for effort in EFFORTS:
        path = latest.get(effort)
        if not path:
            print(f"WARN: no unified JSON found for effort={effort}", file=sys.stderr)
            continue
        rows.append(summarize(path, input_rate, output_rate))

    csv_path = args.reports_dir / "effort_comparison.csv"
    if rows:
        fieldnames = list(rows[0].keys())
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=fieldnames)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"wrote {csv_path}")

    md_path = args.reports_dir / "effort_comparison.md"
    md_path.write_text(render_markdown(rows) + "\n", encoding="utf-8")
    print(f"wrote {md_path}")

    print("\n=== Summary ===")
    print(render_markdown(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
