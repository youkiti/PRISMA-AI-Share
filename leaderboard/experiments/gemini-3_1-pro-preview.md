# Gemini 3.1 Pro

- **Model id**: `gemini-3.1-pro-preview`
- **Provider**: Google
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `temperature`: `1.0`
  - `thinking_level`: `HIGH`
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gemini-3.1-pro-preview_20260416_200112.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gemini-3.1-pro-preview_20260416_200112.json)
- **Pricing entry**: `google/gemini-3.1-pro-preview`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 81.51 | 90.24 | 70.39 | 84.54 | 0.618 |
| Main body | 410 | 81.95 | 88.58 | 71.15 | 85.88 | 0.609 |
| Abstract | 120 | 80.00 | 100.00 | 68.83 | 78.18 | 0.613 |

TP / TN / FP / FN: 268 / 164 / 69 / 29 (correct 432 of 530)

## Performance

- Mean time per SR: 90.4 seconds
- Cost per SR: $0.055 (USD)
- Total cohort cost: $0.553

## Notes

_(none)_
