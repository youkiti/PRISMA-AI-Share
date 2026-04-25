#!/usr/bin/env python3
"""Build the PRISMA-AI public leaderboard from unified validation JSONs.

Reads:
- `leaderboard/manifest.yaml`             - model roster + paths
- each model's unified validation JSON    - metrics + per-paper token usage / runtime
- `data/pricing/model_pricing.toml`       - cost rates per model

Writes:
- `leaderboard/leaderboard.md`            - sortable Markdown table
- `leaderboard/leaderboard.csv`           - same content as CSV
- `leaderboard/leaderboard.json`          - machine-readable
- `leaderboard/experiments/<slug>.md`     - per-model experiment log

Optional: `--inject-readme` rewrites the contents between
`<!-- LEADERBOARD:START -->` and `<!-- LEADERBOARD:END -->` in `README.md`.

Usage:
    PYTHONPATH=. python3 analysis/build_leaderboard.py
    PYTHONPATH=. python3 analysis/build_leaderboard.py --inject-readme
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[1]

PRICING_TOML = REPO_ROOT / "data" / "pricing" / "model_pricing.toml"
MANIFEST_PATH = REPO_ROOT / "leaderboard" / "manifest.yaml"
LEADERBOARD_DIR = REPO_ROOT / "leaderboard"
EXPERIMENTS_DIR = LEADERBOARD_DIR / "experiments"
README_PATH = REPO_ROOT / "README.md"

LEADERBOARD_START = "<!-- LEADERBOARD:START -->"
LEADERBOARD_END = "<!-- LEADERBOARD:END -->"

Z_95 = 1.96


@dataclass
class LeaderboardRow:
    rank: int
    model_id: str
    display_name: str
    provider: str
    accuracy_pct: float
    accuracy_ci_lower_pct: float
    accuracy_ci_upper_pct: float
    sensitivity_pct: float
    specificity_pct: float
    f1_pct: float
    cohen_kappa: float
    cost_per_sr_usd: Optional[float]
    cost_total_usd: Optional[float]
    mean_time_per_sr_sec: Optional[float]
    schema_type: str
    notes: str
    unified_json: str
    pricing_id: Optional[str]
    cost_warnings: List[str]
    parameters: Dict[str, Any]
    counts: Dict[str, int]
    main_body: Dict[str, float]
    abstract: Dict[str, float]


@dataclass
class PricingEntry:
    id: str
    display_name: str
    provider: str
    billing_strategy: str
    aliases: List[str]
    input_rate: Optional[float]
    output_rate: Optional[float]
    tiers: List[Dict[str, Any]]
    notes: str = ""


def load_pricing_catalog() -> Dict[str, PricingEntry]:
    """Load pricing entries indexed by id and by every alias (lowercased)."""
    raw = tomllib.loads(PRICING_TOML.read_text(encoding="utf-8"))
    catalog: Dict[str, PricingEntry] = {}
    for m in raw.get("models", []) or []:
        entry = PricingEntry(
            id=m["id"],
            display_name=m.get("display_name", m["id"]),
            provider=m.get("provider", ""),
            billing_strategy=m.get("billing_strategy", "simple"),
            aliases=list(m.get("aliases", [])),
            input_rate=m.get("input_rate"),
            output_rate=m.get("output_rate"),
            tiers=list(m.get("tiers", []) or []),
            notes=m.get("notes", ""),
        )
        for key in [entry.id] + entry.aliases:
            catalog[key.lower()] = entry
    return catalog


def _resolve_tier_rates(tiers: List[Dict[str, Any]], prompt_tokens: int, completion_tokens: int) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Return (input_rate, output_rate, multiplier) for a tiered pricing entry.

    Uses prompt_tokens for tiers tagged token_basis="prompt_tokens" (e.g., GPT-5.4
    short / long context split), otherwise falls back to total tokens.
    """
    total_tokens = prompt_tokens + completion_tokens
    chosen = None
    for tier in tiers:
        basis = tier.get("token_basis")
        amount = prompt_tokens if basis == "prompt_tokens" else total_tokens
        lo = int(tier.get("min_tokens", 0))
        hi = int(tier.get("max_tokens", 10**12))
        if lo <= amount <= hi:
            chosen = tier
            break
    if chosen is None and tiers:
        chosen = tiers[-1]
    if chosen is None:
        return None, None, None
    return chosen.get("input_rate"), chosen.get("output_rate"), chosen.get("multiplier")


def _price_tokens(pricing: PricingEntry, prompt_tokens: int, completion_tokens: int) -> Optional[float]:
    if pricing.billing_strategy == "tiered" and pricing.tiers:
        in_rate, out_rate, multiplier = _resolve_tier_rates(pricing.tiers, prompt_tokens, completion_tokens)
        if multiplier is not None and (in_rate is None or out_rate is None):
            base_in = pricing.tiers[0].get("input_rate") if pricing.tiers else None
            base_out = pricing.tiers[0].get("output_rate") if pricing.tiers else None
            in_rate = (base_in or 0.0) * multiplier
            out_rate = (base_out or 0.0) * multiplier
    else:
        in_rate = pricing.input_rate
        out_rate = pricing.output_rate
    if in_rate is None or out_rate is None:
        return None
    return (prompt_tokens / 1_000_000.0) * in_rate + (completion_tokens / 1_000_000.0) * out_rate


def compute_run_cost(
    unified_path: Path,
    pricing_catalog: Dict[str, PricingEntry],
    fallback_pricing_id: Optional[str] = None,
) -> Tuple[Optional[float], List[str], int, int]:
    """Sum cost across paper_evaluations or fall back to experiment-level usage.

    Resolution order for the per-paper case:
      paper.overall_metadata.model_id -> manifest pricing_id (fallback)

    Resolution order for tokens:
      1. paper-level overall_metadata.token_usage on every paper
      2. experiment_metadata.token_count_summary.usage_breakdown (input/output split)
      3. only experiment_metadata.total_token_count (no split) -> mark warning, no cost

    Returns (total_cost_usd_or_None, warnings, total_prompt_tokens, total_completion_tokens).
    Token rates in the toml are USD per 1,000,000 tokens.
    """
    data = json.loads(unified_path.read_text(encoding="utf-8"))
    warnings: List[str] = []

    fallback = pricing_catalog.get((fallback_pricing_id or "").lower()) if fallback_pricing_id else None

    papers = data.get("paper_evaluations") or []

    # Path A: per-paper token_usage available on at least one paper.
    per_paper_tokens: List[Tuple[str, int, int]] = []
    any_per_paper_usage = False
    for paper in papers:
        md = paper.get("overall_metadata") or {}
        usage = md.get("token_usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        if prompt_tokens or completion_tokens:
            any_per_paper_usage = True
        model_id = (md.get("model_id") or "").lower()
        per_paper_tokens.append((model_id, prompt_tokens, completion_tokens))

    if any_per_paper_usage:
        total_prompt = 0
        total_completion = 0
        total_cost = 0.0
        saw_pricing = False
        for model_id, prompt_tokens, completion_tokens in per_paper_tokens:
            total_prompt += prompt_tokens
            total_completion += completion_tokens
            pricing = pricing_catalog.get(model_id) or fallback
            if pricing is None:
                if model_id and f"pricing_not_found:{model_id}" not in warnings:
                    warnings.append(f"pricing_not_found:{model_id}")
                continue
            cost = _price_tokens(pricing, prompt_tokens, completion_tokens)
            if cost is None:
                warnings.append(f"missing_tier_rate:{pricing.id}")
                continue
            total_cost += cost
            saw_pricing = True
            if pricing.billing_strategy == "variable":
                tag = "pricing_flag:variable_rate"
                if tag not in warnings:
                    warnings.append(tag)
        if not saw_pricing:
            return None, warnings, total_prompt, total_completion
        return total_cost, warnings, total_prompt, total_completion

    # Path B: experiment-level breakdown (input_tokens / output_tokens).
    em = data.get("experiment_metadata") or {}
    breakdown = ((em.get("token_count_summary") or {}).get("usage_breakdown") or {})
    prompt_tokens = int(breakdown.get("prompt_tokens") or breakdown.get("input_tokens") or 0)
    completion_tokens = int(breakdown.get("completion_tokens") or breakdown.get("output_tokens") or 0)
    if prompt_tokens or completion_tokens:
        if fallback is None:
            warnings.append("pricing_not_found:fallback_missing")
            return None, warnings, prompt_tokens, completion_tokens
        cost = _price_tokens(fallback, prompt_tokens, completion_tokens)
        if cost is None:
            warnings.append(f"missing_tier_rate:{fallback.id}")
            return None, warnings, prompt_tokens, completion_tokens
        if fallback.billing_strategy == "variable":
            warnings.append("pricing_flag:variable_rate")
        warnings.append("token_source:experiment_metadata")
        return cost, warnings, prompt_tokens, completion_tokens

    # Path C: only total_token_count, no input/output split. Cannot price.
    total = em.get("total_token_count")
    if isinstance(total, (int, float)) and total > 0:
        warnings.append("cost_unavailable:no_input_output_split")
        return None, warnings, 0, 0

    warnings.append("no_paper_evaluations")
    return None, warnings, 0, 0


def wilson_ci(successes: int, total: int, z: float = Z_95) -> Tuple[float, float]:
    """Wilson score 95 percent interval for a binomial proportion."""
    if total <= 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    margin = (z * math.sqrt((p * (1.0 - p) + z * z / (4 * total)) / total)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def load_manifest() -> Dict[str, Any]:
    with MANIFEST_PATH.open("r", encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def metric_block(d: Optional[Dict[str, Any]]) -> Dict[str, float]:
    """Pull the standard fields from one of the metric blocks (overall / main / abstract)."""
    if not d:
        return {}
    counts = d.get("counts") or {}
    return {
        "accuracy": float(d.get("accuracy") or 0.0),
        "precision": float(d.get("precision") or 0.0),
        "recall": float(d.get("recall") or d.get("sensitivity") or 0.0),
        "f1_score": float(d.get("f1_score") or 0.0),
        "specificity": float(d.get("specificity") or 0.0),
        "cohen_kappa": float(d.get("cohen_kappa") or 0.0),
        "tp": int(counts.get("tp") or 0),
        "tn": int(counts.get("tn") or 0),
        "fp": int(counts.get("fp") or 0),
        "fn": int(counts.get("fn") or 0),
        "total_comparable": int(counts.get("total_comparable") or 0),
        "correct": int(counts.get("correct") or 0),
    }


def per_paper_processing_times(unified: Dict[str, Any]) -> List[float]:
    out: List[float] = []
    for paper in unified.get("paper_evaluations", []) or []:
        md = paper.get("overall_metadata") or {}
        pt = md.get("processing_time")
        if isinstance(pt, (int, float)):
            out.append(float(pt))
    return out


def mean_time_per_sr(unified: Dict[str, Any]) -> Optional[float]:
    times = per_paper_processing_times(unified)
    if times:
        return statistics.mean(times)
    em = unified.get("experiment_metadata") or {}
    total_time = em.get("total_processing_time")
    n = len(unified.get("paper_evaluations") or []) or em.get("num_papers")
    if isinstance(total_time, (int, float)) and isinstance(n, int) and n > 0:
        return float(total_time) / n
    return None


def compute_row(entry: Dict[str, Any], pricing_catalog) -> LeaderboardRow:
    unified_path = REPO_ROOT / entry["unified_json"]
    if not unified_path.exists():
        raise FileNotFoundError(f"unified JSON not found: {unified_path}")
    unified = json.loads(unified_path.read_text(encoding="utf-8"))

    overall = metric_block(unified.get("overall_metrics"))
    main = metric_block(unified.get("main_body_metrics"))
    abstract = metric_block(unified.get("abstract_metrics"))

    correct = overall.get("correct", 0)
    total = overall.get("total_comparable", 0)
    ci_lo, ci_hi = wilson_ci(correct, total)

    mean_time = mean_time_per_sr(unified)

    cost_total, cost_warnings, _prompt_tokens, _completion_tokens = compute_run_cost(
        unified_path, pricing_catalog, fallback_pricing_id=entry.get("pricing_id"),
    )
    n_papers = max(1, len(unified.get("paper_evaluations") or []))
    cost_per_sr = (cost_total / n_papers) if cost_total is not None else None

    return LeaderboardRow(
        rank=0,  # filled in after sort
        model_id=entry["id"],
        display_name=entry["display_name"],
        provider=entry["provider"],
        accuracy_pct=overall.get("accuracy", 0.0),
        accuracy_ci_lower_pct=ci_lo * 100.0,
        accuracy_ci_upper_pct=ci_hi * 100.0,
        sensitivity_pct=overall.get("recall", 0.0),
        specificity_pct=overall.get("specificity", 0.0),
        f1_pct=overall.get("f1_score", 0.0),
        cohen_kappa=overall.get("cohen_kappa", 0.0),
        cost_per_sr_usd=cost_per_sr,
        cost_total_usd=cost_total,
        mean_time_per_sr_sec=mean_time,
        schema_type=entry.get("schema_type", "simple"),
        notes=entry.get("notes", "") or "",
        unified_json=entry["unified_json"],
        pricing_id=entry.get("pricing_id"),
        cost_warnings=cost_warnings,
        parameters=entry.get("parameters") or {},
        counts={
            "tp": overall.get("tp", 0),
            "tn": overall.get("tn", 0),
            "fp": overall.get("fp", 0),
            "fn": overall.get("fn", 0),
            "total_comparable": overall.get("total_comparable", 0),
            "correct": overall.get("correct", 0),
        },
        main_body=main,
        abstract=abstract,
    )


def fmt_pct(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"{v:.2f}"


def fmt_usd(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"${v:.3f}"


def fmt_sec(v: Optional[float]) -> str:
    if v is None:
        return "-"
    return f"{v:.1f}"


def render_markdown(rows: List[LeaderboardRow], cohort: Dict[str, Any]) -> str:
    header = (
        "| Rank | Model | Provider | Accuracy % (95% CI) | Sens % | Spec % | F1 % | "
        "Cohen κ | Cost / SR | Time / SR (sec) | Schema | Notes |"
    )
    sep = "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|"
    lines = [header, sep]
    for r in rows:
        ci = f"{fmt_pct(r.accuracy_pct)} ({fmt_pct(r.accuracy_ci_lower_pct)}-{fmt_pct(r.accuracy_ci_upper_pct)})"
        notes_cell = r.notes.replace("\n", " ").strip()
        if r.cost_warnings:
            warn = "; ".join(sorted(set(r.cost_warnings)))
            if warn and warn not in notes_cell:
                notes_cell = (notes_cell + " " if notes_cell else "") + f"({warn})"
        lines.append(
            f"| {r.rank} | {r.display_name} | {r.provider} | {ci} | "
            f"{fmt_pct(r.sensitivity_pct)} | {fmt_pct(r.specificity_pct)} | "
            f"{fmt_pct(r.f1_pct)} | {r.cohen_kappa:.3f} | "
            f"{fmt_usd(r.cost_per_sr_usd)} | {fmt_sec(r.mean_time_per_sr_sec)} | "
            f"{r.schema_type} | {notes_cell} |"
        )

    cohort_paragraph = (
        f"**Cohort**: {cohort.get('name')} ({len(cohort.get('papers') or [])} systematic reviews, "
        f"{cohort.get('expected_total_comparable')} comparable item decisions = "
        f"{cohort.get('expected_main_comparable')} main-body + {cohort.get('expected_abstract_comparable')} abstract per cohort). "
        f"Schema: `{cohort.get('schema')}`. Checklist format: `{cohort.get('checklist_format')}`. "
        "Reference labels: two-rater consensus PRISMA 2020 from the source publications."
    )
    return cohort_paragraph + "\n\n" + "\n".join(lines) + "\n"


def render_csv(rows: List[LeaderboardRow]) -> str:
    field_order = [
        "rank", "model_id", "display_name", "provider",
        "accuracy_pct", "accuracy_ci_lower_pct", "accuracy_ci_upper_pct",
        "sensitivity_pct", "specificity_pct", "f1_pct", "cohen_kappa",
        "cost_per_sr_usd", "cost_total_usd", "mean_time_per_sr_sec",
        "schema_type", "notes", "unified_json", "pricing_id",
    ]
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(field_order)
    for r in rows:
        d = asdict(r)
        writer.writerow([d[k] for k in field_order])
    return buf.getvalue()


def render_json(rows: List[LeaderboardRow], cohort: Dict[str, Any]) -> str:
    return json.dumps(
        {"cohort": cohort, "models": [asdict(r) for r in rows]},
        ensure_ascii=False,
        indent=2,
    )


def render_experiment_md(row: LeaderboardRow, manifest_entry: Dict[str, Any], cohort: Dict[str, Any]) -> str:
    params_lines = []
    for k, v in (row.parameters or {}).items():
        params_lines.append(f"  - `{k}`: `{v}`")
    params_block = "\n".join(params_lines) if params_lines else "  _(none)_"

    cost_per_sr = fmt_usd(row.cost_per_sr_usd)
    cost_total = fmt_usd(row.cost_total_usd)
    cost_warning_block = ""
    if row.cost_warnings:
        cost_warning_block = "\n**Cost computation notes**: " + ", ".join(sorted(set(row.cost_warnings)))

    main = row.main_body
    ab = row.abstract

    main_table = (
        f"| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |\n"
        f"|---|---:|---:|---:|---:|---:|---:|\n"
        f"| Overall | {row.counts.get('total_comparable')} | {row.accuracy_pct:.2f} | "
        f"{row.sensitivity_pct:.2f} | {row.specificity_pct:.2f} | {row.f1_pct:.2f} | "
        f"{row.cohen_kappa:.3f} |\n"
        f"| Main body | {main.get('total_comparable', 0)} | {main.get('accuracy', 0):.2f} | "
        f"{main.get('recall', 0):.2f} | {main.get('specificity', 0):.2f} | "
        f"{main.get('f1_score', 0):.2f} | {main.get('cohen_kappa', 0):.3f} |\n"
        f"| Abstract | {ab.get('total_comparable', 0)} | {ab.get('accuracy', 0):.2f} | "
        f"{ab.get('recall', 0):.2f} | {ab.get('specificity', 0):.2f} | "
        f"{ab.get('f1_score', 0):.2f} | {ab.get('cohen_kappa', 0):.3f} |"
    )

    counts_line = (
        f"TP / TN / FP / FN: {row.counts.get('tp')} / {row.counts.get('tn')} / "
        f"{row.counts.get('fp')} / {row.counts.get('fn')} (correct {row.counts.get('correct')} "
        f"of {row.counts.get('total_comparable')})"
    )

    notes_block = row.notes.strip() or "_(none)_"

    return f"""# {row.display_name}

- **Model id**: `{row.model_id}`
- **Provider**: {row.provider}
- **Cohort**: {cohort.get('name')} ({len(cohort.get('papers') or [])} SRs, {row.counts.get('total_comparable')} comparable items)
- **Schema**: `{row.schema_type}`, checklist format `{cohort.get('checklist_format')}`, order mode `{cohort.get('order_mode')}`, section mode `{cohort.get('section_mode')}`
- **Locked parameters**:
{params_block}
- **Unified JSON**: [`{row.unified_json}`](../../{row.unified_json})
- **Pricing entry**: `{row.pricing_id or '(missing)'}`

## Metrics

{main_table}

{counts_line}

## Performance

- Mean time per SR: {fmt_sec(row.mean_time_per_sr_sec)} seconds
- Cost per SR: {cost_per_sr} (USD)
- Total cohort cost: {cost_total}{cost_warning_block}

## Notes

{notes_block}
"""


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace("/", "_").replace(".", "_")


def inject_readme(markdown_block: str) -> bool:
    if not README_PATH.exists():
        return False
    text = README_PATH.read_text(encoding="utf-8")
    if LEADERBOARD_START not in text or LEADERBOARD_END not in text:
        return False
    pre = text.split(LEADERBOARD_START)[0] + LEADERBOARD_START + "\n"
    post = "\n" + LEADERBOARD_END + text.split(LEADERBOARD_END, 1)[1]
    README_PATH.write_text(pre + markdown_block + post, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inject-readme", action="store_true",
                        help="Replace the leaderboard markers in README.md with the generated table.")
    args = parser.parse_args()

    manifest = load_manifest()
    cohort = manifest.get("cohort") or {}
    entries = manifest.get("models") or []
    if not entries:
        print("manifest has no models", file=sys.stderr)
        return 2

    pricing_catalog = load_pricing_catalog()

    rows = [compute_row(entry, pricing_catalog) for entry in entries]

    rows.sort(key=lambda r: r.accuracy_pct, reverse=True)
    for i, r in enumerate(rows, start=1):
        r.rank = i

    LEADERBOARD_DIR.mkdir(parents=True, exist_ok=True)
    EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)

    md_block = render_markdown(rows, cohort)
    (LEADERBOARD_DIR / "leaderboard.md").write_text(md_block, encoding="utf-8")
    (LEADERBOARD_DIR / "leaderboard.csv").write_text(render_csv(rows), encoding="utf-8")
    (LEADERBOARD_DIR / "leaderboard.json").write_text(render_json(rows, cohort), encoding="utf-8")

    entry_by_id = {e["id"]: e for e in entries}
    for r in rows:
        slug = slugify(r.model_id)
        out = EXPERIMENTS_DIR / f"{slug}.md"
        out.write_text(render_experiment_md(r, entry_by_id[r.model_id], cohort), encoding="utf-8")

    if args.inject_readme:
        ok = inject_readme(md_block)
        if not ok:
            print("README injection skipped: markers not found in README.md", file=sys.stderr)

    print(f"Wrote {len(rows)} models to:")
    print(f"  {LEADERBOARD_DIR / 'leaderboard.md'}")
    print(f"  {LEADERBOARD_DIR / 'leaderboard.csv'}")
    print(f"  {LEADERBOARD_DIR / 'leaderboard.json'}")
    print(f"  {EXPERIMENTS_DIR}/<slug>.md  (one per model)")
    print()
    print("Top 5 by accuracy:")
    for r in rows[:5]:
        print(f"  {r.rank:>2}. {r.display_name:<22} {r.accuracy_pct:6.2f}%  "
              f"(95% CI {r.accuracy_ci_lower_pct:.2f}-{r.accuracy_ci_upper_pct:.2f})  "
              f"{fmt_usd(r.cost_per_sr_usd)} / SR")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
