# Grok-4.20

- **Model id**: `x-ai/grok-4.20`
- **Provider**: xAI
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  _(none)_
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_x-ai_grok-4.20_20260416_201008.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_x-ai_grok-4.20_20260416_201008.json)
- **Pricing entry**: `openrouter/grok-4-20`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 86.04 | 89.23 | 81.97 | 87.75 | 0.715 |
| Main body | 410 | 84.39 | 87.40 | 79.49 | 87.40 | 0.669 |
| Abstract | 120 | 91.67 | 100.00 | 87.01 | 89.58 | 0.828 |

TP / TN / FP / FN: 265 / 191 / 42 / 32 (correct 456 of 530)

## Performance

- Mean time per SR: 53.5 seconds
- Cost per SR: $0.017 (USD)
- Total cohort cost: $0.170

## Notes

Routed via xAI direct (OpenRouter upstream times out on long tool calls).
