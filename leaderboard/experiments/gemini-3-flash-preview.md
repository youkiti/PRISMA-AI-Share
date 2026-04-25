# Gemini 3 Flash

- **Model id**: `gemini-3-flash-preview`
- **Provider**: Google
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `temperature`: `1.0`
  - `thinking_level`: `LOW`
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gemini-3-flash-preview_20251218_082141.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gemini-3-flash-preview_20251218_082141.json)
- **Pricing entry**: `google/gemini-3-flash`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 81.51 | 92.26 | 60.77 | 86.79 | 0.563 |
| Main body | 410 | 84.15 | 92.12 | 64.41 | 89.22 | 0.594 |
| Abstract | 120 | 72.50 | 92.98 | 53.97 | 76.26 | 0.460 |

TP / TN / FP / FN: 322 / 110 / 71 / 27 (correct 432 of 530)

## Performance

- Mean time per SR: 24.0 seconds
- Cost per SR: $0.049 (USD)
- Total cohort cost: $0.487

## Notes

_(none)_
