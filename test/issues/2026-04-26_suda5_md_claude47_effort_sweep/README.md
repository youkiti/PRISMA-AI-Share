# Claude Opus 4.7 — Effort Sweep on Suda Parameter Optimization Cohort (5 papers)

- Date: 2026-04-26
- Model: `claude-opus-4-7`
- Dataset: Suda 2025 emergency medicine, 5 papers (canonical parameter optimization cohort)
  - `Suda2025_5, Suda2025_7, Suda2025_15, Suda2025_17, Suda2025_18`
- Checklist: Markdown, simple schema, eande-first order, section-mode off
- Sweep: adaptive thinking effort ∈ {low, medium, high, xhigh, max}

## Why this run exists

Anthropic released Claude Opus 4.7 during the rebuttal period (April 2026), after
the Suda parameter optimization phase had already been completed for the original
ten development-phase models. The earlier 2026-04-17 sweep
(`test/issues/2026-04-17_tsuge10_md_claude47_effort_sweep/`) selected the
adaptive-thinking effort level on the Tsuge validation cohort, which is the same
set of 10 papers used to report Opus 4.7's validation accuracy. To eliminate this
methodological concern (effort selection on the same cohort used for reporting),
this run repeats the effort sweep on the canonical 5-paper Suda parameter
optimization cohort, matching the protocol used for all other models'
parameter-locking decisions.

The effort level chosen by this Suda run becomes the locked configuration for
Opus 4.7 in the manuscript; the validation cohort metrics will be re-rendered
from the same set of effort runs already in the 2026-04-17 directory (no
re-evaluation on Tsuge required).

## Files

```
README.md                          — this file
FINAL_REPORT.md                    — populated after sweep completes
data/suda_selected5.txt            — fixed 5 paper IDs
scripts/run_effort_sweep.sh        — serial 5-effort sweep driver
scripts/run_optimization_model.py  — single-effort runner (Suda dataset)
scripts/build_unified_validation_json.py  — unified JSON builder (symlink to 2026-04-17 sibling)
scripts/check_optimization_counts.py      — count gating (Suda 5: 265/205/60)
scripts/aggregate_effort_sweep.py         — per-effort comparison table
results/                           — md_claude-opus-4-7_<effort>_<ts>.json + raw trios
reports/effort_comparison.{md,csv}
logs/run_<effort>_<ts>.log
```

## How to run

```bash
bash test/issues/2026-04-26_suda5_md_claude47_effort_sweep/scripts/run_effort_sweep.sh
venv/bin/python test/issues/2026-04-26_suda5_md_claude47_effort_sweep/scripts/aggregate_effort_sweep.py
```

## Gating

Each unified JSON must satisfy:
- `overall_metrics.counts.total_comparable == 265`
- `main_body_metrics.counts.total_comparable == 205`
- `abstract_metrics.counts.total_comparable == 60`
- `processing_metadata.effort` equals the intended effort for that run
