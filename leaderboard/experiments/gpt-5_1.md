# GPT-5.1

- **Model id**: `gpt-5.1`
- **Provider**: OpenAI
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `verbosity`: `low`
  - `reasoning_effort`: `high`
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gpt-5.1_20251119_074132.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gpt-5.1_20251119_074132.json)
- **Pricing entry**: `openai/gpt-5.1`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 80.19 | 87.21 | 71.24 | 83.15 | 0.592 |
| Main body | 410 | 80.73 | 85.04 | 73.72 | 84.54 | 0.590 |
| Abstract | 120 | 78.33 | 100.00 | 66.23 | 76.79 | 0.584 |

TP / TN / FP / FN: 259 / 166 / 67 / 38 (correct 425 of 530)

## Performance

- Mean time per SR: 140.4 seconds
- Cost per SR: - (USD)
- Total cohort cost: -
**Cost computation notes**: cost_unavailable:no_input_output_split

## Notes

_(none)_
