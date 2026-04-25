# Gemini 3 Pro

- **Model id**: `gemini-3-pro`
- **Provider**: Google
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `temperature`: `1.0`
  - `thinking_level`: `HIGH`
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gemini-3-pro_20251119_070126.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gemini-3-pro_20251119_070126.json)
- **Pricing entry**: `google/gemini-3-pro`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 81.32 | 91.25 | 68.67 | 84.56 | 0.612 |
| Main body | 410 | 80.98 | 89.76 | 66.67 | 85.39 | 0.583 |
| Abstract | 120 | 82.50 | 100.00 | 72.73 | 80.37 | 0.656 |

TP / TN / FP / FN: 271 / 160 / 73 / 26 (correct 431 of 530)

## Performance

- Mean time per SR: 113.0 seconds
- Cost per SR: - (USD)
- Total cohort cost: -
**Cost computation notes**: cost_unavailable:no_input_output_split

## Notes

_(none)_
