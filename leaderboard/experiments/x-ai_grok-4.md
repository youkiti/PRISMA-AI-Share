# Grok-4

- **Model id**: `x-ai/grok-4`
- **Provider**: xAI (via OpenRouter)
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  _(none)_
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_x-ai_grok-4_20251023_184404.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_x-ai_grok-4_20251023_184404.json)
- **Pricing entry**: `openrouter/grok-4`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 81.13 | 86.20 | 74.68 | 83.66 | 0.614 |
| Main body | 410 | 79.51 | 84.25 | 71.79 | 83.59 | 0.563 |
| Abstract | 120 | 86.67 | 97.67 | 80.52 | 84.00 | 0.730 |

TP / TN / FP / FN: 256 / 174 / 59 / 41 (correct 430 of 530)

## Performance

- Mean time per SR: 117.8 seconds
- Cost per SR: $0.111 (USD)
- Total cohort cost: $1.106

## Notes

_(none)_
