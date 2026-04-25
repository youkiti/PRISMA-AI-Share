# GPT-5

- **Model id**: `gpt-5`
- **Provider**: OpenAI
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `reasoning_effort`: `high`
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gpt-5_20251023_184404.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gpt-5_20251023_184404.json)
- **Pricing entry**: `openai/gpt-5`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 78.11 | 87.21 | 66.52 | 81.70 | 0.547 |
| Main body | 410 | 77.80 | 85.43 | 65.38 | 82.67 | 0.519 |
| Abstract | 120 | 79.17 | 97.67 | 68.83 | 77.06 | 0.595 |

TP / TN / FP / FN: 259 / 155 / 78 / 38 (correct 414 of 530)

## Performance

- Mean time per SR: 18.4 seconds
- Cost per SR: $0.031 (USD)
- Total cohort cost: $0.306

## Notes

_(none)_
