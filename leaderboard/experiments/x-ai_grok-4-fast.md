# Grok-4-fast

- **Model id**: `x-ai/grok-4-fast`
- **Provider**: xAI (via OpenRouter)
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  _(none)_
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_x-ai_grok-4-fast_20251023_184404.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_x-ai_grok-4-fast_20251023_184404.json)
- **Pricing entry**: `openrouter/grok-4-fast`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 83.02 | 89.56 | 74.68 | 85.53 | 0.651 |
| Main body | 410 | 82.20 | 87.80 | 73.08 | 85.93 | 0.617 |
| Abstract | 120 | 85.83 | 100.00 | 77.92 | 83.50 | 0.717 |

TP / TN / FP / FN: 266 / 174 / 59 / 31 (correct 440 of 530)

## Performance

- Mean time per SR: 27.0 seconds
- Cost per SR: $0.005 (USD)
- Total cohort cost: $0.050

## Notes

_(none)_
