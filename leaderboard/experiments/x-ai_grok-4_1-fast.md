# Grok-4.1-fast

- **Model id**: `x-ai/grok-4.1-fast`
- **Provider**: xAI (via OpenRouter)
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  _(none)_
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_x-ai_grok-4.1-fast_20251120_152819.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_x-ai_grok-4.1-fast_20251120_152819.json)
- **Pricing entry**: `openrouter/grok-4-1-fast`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 81.13 | 88.25 | 67.40 | 86.03 | 0.570 |
| Main body | 410 | 81.71 | 86.99 | 68.64 | 87.14 | 0.555 |
| Abstract | 120 | 79.17 | 94.74 | 65.08 | 81.20 | 0.589 |

TP / TN / FP / FN: 308 / 122 / 59 / 41 (correct 430 of 530)

## Performance

- Mean time per SR: 58.3 seconds
- Cost per SR: $0.006 (USD)
- Total cohort cost: $0.062

## Notes

_(none)_
