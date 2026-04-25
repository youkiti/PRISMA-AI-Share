# Claude Sonnet 4.5

- **Model id**: `claude-sonnet-4-5-20250929`
- **Provider**: Anthropic
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `thinking_budget_tokens`: `28000`
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_claude-sonnet-4-5-20250929_20251023_184404.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_claude-sonnet-4-5-20250929_20251023_184404.json)
- **Pricing entry**: `anthropic/claude-sonnet-4-5`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 72.64 | 74.75 | 69.96 | 75.38 | 0.446 |
| Main body | 410 | 71.22 | 71.26 | 71.15 | 75.42 | 0.410 |
| Abstract | 120 | 77.50 | 95.35 | 67.53 | 75.23 | 0.562 |

TP / TN / FP / FN: 222 / 163 / 70 / 75 (correct 385 of 530)

## Performance

- Mean time per SR: 207.8 seconds
- Cost per SR: $0.163 (USD)
- Total cohort cost: $1.628

## Notes

_(none)_
