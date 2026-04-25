# GPT-4o

- **Model id**: `gpt-4o`
- **Provider**: OpenAI
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  _(none)_
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gpt-4o_20251023_184404.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gpt-4o_20251023_184404.json)
- **Pricing entry**: `openai/gpt-4o`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 68.49 | 96.97 | 32.19 | 77.52 | 0.313 |
| Main body | 410 | 67.56 | 96.85 | 19.87 | 78.72 | 0.196 |
| Abstract | 120 | 71.67 | 97.67 | 57.14 | 71.19 | 0.471 |

TP / TN / FP / FN: 288 / 75 / 158 / 9 (correct 363 of 530)

## Performance

- Mean time per SR: 31.8 seconds
- Cost per SR: $0.043 (USD)
- Total cohort cost: $0.434

## Notes

_(none)_
