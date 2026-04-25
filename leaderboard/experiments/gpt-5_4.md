# GPT-5.4

- **Model id**: `gpt-5.4`
- **Provider**: OpenAI
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `verbosity`: `low`
  - `reasoning_effort`: `none`
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gpt-5.4_20260416_194607.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gpt-5.4_20260416_194607.json)
- **Pricing entry**: `openai/gpt-5.4`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 82.08 | 86.87 | 75.97 | 84.45 | 0.633 |
| Main body | 410 | 81.71 | 84.65 | 76.92 | 85.15 | 0.613 |
| Abstract | 120 | 83.33 | 100.00 | 74.03 | 81.13 | 0.671 |

TP / TN / FP / FN: 258 / 177 / 56 / 39 (correct 435 of 530)

## Performance

- Mean time per SR: 31.6 seconds
- Cost per SR: $0.060 (USD)
- Total cohort cost: $0.596

## Notes

_(none)_
