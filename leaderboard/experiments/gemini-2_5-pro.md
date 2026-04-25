# Gemini 2.5 Pro

- **Model id**: `gemini-2.5-pro`
- **Provider**: Google
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `temperature`: `0.0`
  - `thinking_budget`: `-1`
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gemini-2.5-pro_20251023_184404.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gemini-2.5-pro_20251023_184404.json)
- **Pricing entry**: `google/gemini-2.5-pro`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 79.06 | 84.51 | 72.10 | 81.89 | 0.571 |
| Main body | 410 | 80.49 | 81.89 | 78.21 | 83.87 | 0.592 |
| Abstract | 120 | 74.17 | 100.00 | 59.74 | 73.50 | 0.515 |

TP / TN / FP / FN: 251 / 168 / 65 / 46 (correct 419 of 530)

## Performance

- Mean time per SR: 76.4 seconds
- Cost per SR: $0.045 (USD)
- Total cohort cost: $0.449

## Notes

_(none)_
