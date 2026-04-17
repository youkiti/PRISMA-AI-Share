# Claude Opus 4.7 — Effort Sweep Validation (Tsuge 10 papers)

- Date: 2026-04-17
- Model: `claude-opus-4-7`
- Dataset: Tsuge 2025 PRISMA, 10 papers (same set as 2026-04-16 validation)
- Checklist: Markdown, simple schema, eande-first order, section-mode off
- Sweep: adaptive thinking effort ∈ {low, medium, high, xhigh, max}

## Files

```
PLAN.md                       — experiment plan
README.md                     — this file
FINAL_REPORT.md               — populated after sweep completes
data/tsuge_selected10.txt     — fixed 10 paper IDs
scripts/run_effort_sweep.sh   — serial 5-effort sweep driver
scripts/run_validation_model.py
scripts/build_unified_validation_json.py
scripts/check_validation_counts.py
scripts/aggregate_effort_sweep.py
results/                      — md_claude-opus-4-7_<effort>_<ts>.json + raw trios
reports/effort_comparison.{md,csv}
logs/run_<effort>_<ts>.log
```

## How to run

```bash
bash test/issues/2026-04-17_tsuge10_md_claude47_effort_sweep/scripts/run_effort_sweep.sh
venv/bin/python test/issues/2026-04-17_tsuge10_md_claude47_effort_sweep/scripts/aggregate_effort_sweep.py
```

## Gating

Each unified JSON must satisfy:
- `overall_metrics.counts.total_comparable == 530`
- `main_body_metrics.counts.total_comparable == 410`
- `abstract_metrics.counts.total_comparable == 120`
- `processing_metadata.effort` equals the intended effort for that run
