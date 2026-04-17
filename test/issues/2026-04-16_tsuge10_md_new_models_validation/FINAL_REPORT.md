# FINAL REPORT — 2026-04-16 Tsuge10 MD × New-Generation Models

> Skeleton. Fill in after the 10-paper run finishes and the unified JSONs have
> been copied into `test/issues/2025-10-23_tsuge_md_validation_metrics/results/`.

## Summary

- **Goal**: extend the Tsuge 2025 PRISMA markdown validation cohort with five
  new-generation LLMs (`claude-opus-4-6`, `gpt-5.4`, `gemini-3.1-pro-preview`,
  `x-ai/grok-4.20`, `qwen/qwen3.6-plus`).
- **Dataset**: Tsuge 2025 PRISMA, 10 papers, Markdown checklist.
- **Pipeline**: simple schema, `order-mode eande-first`, `section-mode off`,
  `MAX_CONCURRENT_PAPERS=1`.
- **Status**: TODO after full run completes.

## Main metrics (Overall)

| Model                      | Acc | Prec | Rec | F1 | Specificity | Cohen κ | Unified JSON |
|---------------------------|----:|-----:|----:|---:|------------:|--------:|--------------|
| `claude-opus-4-6`         | TBD | TBD  | TBD | TBD | TBD        | TBD     | `results/md_claude-opus-4-6_<ts>.json` |
| `gpt-5.4`                 | TBD | TBD  | TBD | TBD | TBD        | TBD     | `results/md_gpt-5.4_<ts>.json` |
| `gemini-3.1-pro-preview`  | TBD | TBD  | TBD | TBD | TBD        | TBD     | `results/md_gemini-3.1-pro-preview_<ts>.json` |
| `x-ai/grok-4.20`          | TBD | TBD  | TBD | TBD | TBD        | TBD     | `results/md_x-ai_grok-4.20_<ts>.json` |
| `qwen/qwen3.6-plus`       | TBD | TBD  | TBD | TBD | TBD        | TBD     | `results/md_qwen_qwen3.6-plus_<ts>.json` |

## Runtime / Cost (Table 2 contribution)

| Model                      | Mean time per SR (sec) | Cost per SR (USD) | Pricing notes |
|---------------------------|-----------------------:|------------------:|---------------|
| `claude-opus-4-6`         | TBD | TBD | Provisional rates — verify before publication |
| `gpt-5.4`                 | TBD | TBD | Provisional rates — verify before publication |
| `gemini-3.1-pro-preview`  | TBD | TBD | Provisional rates — verify before publication |
| `x-ai/grok-4.20`          | TBD | TBD | Provisional rates — verify before publication |
| `qwen/qwen3.6-plus`       | TBD | TBD | Provisional rates — verify before publication |

## Denominator sanity

| Model | Overall (530) | Main (410) | Abstract (120) | Model ID consistent? |
|------|--------------:|-----------:|---------------:|:---------------------|
| TBD  | TBD           | TBD        | TBD            | TBD                  |

Ran via `scripts/check_validation_counts.py <unified>.json --expected-size full`.

## Downstream reflection

- [ ] Unified JSONs copied to `test/issues/2025-10-23_tsuge_md_validation_metrics/results/`
- [ ] `paper/figures/make_validation_macro_chart.py` updated and re-rendered
- [ ] `test/issues/2025-10-24_validation_ci_update/scripts/compute_validation_ci.py` rerun
- [ ] `test/issues/2025-10-24_table2_runtime_cost/scripts/aggregate_table2_runtime_cost.py` rerun
- [ ] Manuscript `canonical` target fixed, then validation paragraph / Table 2 / Methods updated

## Open issues

- Pricing for all 5 models was seeded with conservative placeholder rates
  (`data/pricing/model_pricing.toml`). Confirm against public pricing pages at
  publication time.
- Observed model IDs sometimes drift through evaluator metadata (Gemini alias,
  Claude model mapping). `scripts/check_validation_counts.py` gates this but
  fixes may require `gemini_direct_evaluator.py` or `claude_evaluator.py` edits
  if drift is detected during the smoke run.
