# GPT-5.6 Terra

- **Model id**: `gpt-5.6-terra`
- **Provider**: OpenAI
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `verbosity`: `low`
  - `reasoning_effort`: `none`
- **Unified JSON**: [`test/issues/2026-07-10_tsuge10_md_gpt56_terra_effort_sweep/results/md_gpt-5.6-terra_20260710_093129.json`](../../test/issues/2026-07-10_tsuge10_md_gpt56_terra_effort_sweep/results/md_gpt-5.6-terra_20260710_093129.json)
- **Pricing entry**: `openai/gpt-5.6-terra`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 82.08 | 89.90 | 72.10 | 84.90 | 0.630 |
| Main body | 410 | 82.44 | 88.19 | 73.08 | 86.15 | 0.622 |
| Abstract | 120 | 80.83 | 100.00 | 70.13 | 78.90 | 0.627 |

TP / TN / FP / FN: 267 / 168 / 65 / 30 (correct 435 of 530)

## Performance

- Mean time per SR: 12.7 seconds
- Cost per SR: $0.059 (USD)
- Total cohort cost: $0.590

## Notes

Effort=none chosen by Tsuge sweep (none/low/high): best accuracy, fastest, cheapest; see test/issues/2026-07-10_tsuge10_md_gpt56_terra_effort_sweep/.
