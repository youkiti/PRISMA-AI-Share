# GPT-5.6 Luna

- **Model id**: `gpt-5.6-luna`
- **Provider**: OpenAI
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `verbosity`: `low`
  - `reasoning_effort`: `none`
- **Unified JSON**: [`test/issues/2026-07-10_tsuge10_md_gpt56_luna_effort_sweep/results/md_gpt-5.6-luna_20260710_082734.json`](../../test/issues/2026-07-10_tsuge10_md_gpt56_luna_effort_sweep/results/md_gpt-5.6-luna_20260710_082734.json)
- **Pricing entry**: `openai/gpt-5.6-luna`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 79.81 | 85.86 | 72.10 | 82.66 | 0.586 |
| Main body | 410 | 81.46 | 83.86 | 77.56 | 84.86 | 0.610 |
| Abstract | 120 | 74.17 | 97.67 | 61.04 | 73.04 | 0.511 |

TP / TN / FP / FN: 255 / 168 / 65 / 42 (correct 423 of 530)

## Performance

- Mean time per SR: 10.8 seconds
- Cost per SR: $0.024 (USD)
- Total cohort cost: $0.239

## Notes

Effort=none chosen by Tsuge sweep (none/low/high/xhigh): accuracies within 0.6pt, none is fastest/cheapest; see test/issues/2026-07-10_tsuge10_md_gpt56_luna_effort_sweep/.
