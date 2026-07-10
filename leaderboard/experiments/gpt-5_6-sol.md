# GPT-5.6 Sol

- **Model id**: `gpt-5.6-sol`
- **Provider**: OpenAI
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `verbosity`: `low`
  - `reasoning_effort`: `none`
- **Unified JSON**: [`test/issues/2026-07-10_tsuge10_md_gpt56_sol_effort_sweep/results/md_gpt-5.6-sol_20260710_110644.json`](../../test/issues/2026-07-10_tsuge10_md_gpt56_sol_effort_sweep/results/md_gpt-5.6-sol_20260710_110644.json)
- **Pricing entry**: `openai/gpt-5.6-sol`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 80.00 | 84.51 | 74.25 | 82.57 | 0.591 |
| Main body | 410 | 79.76 | 81.89 | 76.28 | 83.37 | 0.575 |
| Abstract | 120 | 80.83 | 100.00 | 70.13 | 78.90 | 0.627 |

TP / TN / FP / FN: 251 / 173 / 60 / 46 (correct 424 of 530)

## Performance

- Mean time per SR: 23.3 seconds
- Cost per SR: $0.120 (USD)
- Total cohort cost: $1.204

## Notes

Effort=none chosen by Tsuge sweep (none/low): accuracies within 0.4pt, none is fastest/cheapest; see test/issues/2026-07-10_tsuge10_md_gpt56_sol_effort_sweep/.
