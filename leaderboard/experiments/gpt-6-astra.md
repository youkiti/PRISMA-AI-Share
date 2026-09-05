# GPT-6 Astra

- **Model id**: `gpt-6-astra`
- **Provider**: OpenAI
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `verbosity`: `low`
  - `reasoning_effort`: `high`
- **Unified JSON**: [`test/issues/2026-09-05_tsuge10_md_gpt6_astra_effort_sweep/results/md_gpt-6-astra_20260905_095331.json`](../../test/issues/2026-09-05_tsuge10_md_gpt6_astra_effort_sweep/results/md_gpt-6-astra_20260905_095331.json)
- **Pricing entry**: `openai/gpt-6-astra`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 76.42 | 77.44 | 75.11 | 78.63 | 0.523 |
| Main body | 410 | 75.85 | 74.02 | 78.85 | 79.16 | 0.508 |
| Abstract | 120 | 78.33 | 97.67 | 67.53 | 76.36 | 0.581 |

TP / TN / FP / FN: 230 / 175 / 58 / 67 (correct 405 of 530)

## Performance

- Mean time per SR: 110.4 seconds
- Cost per SR: $0.478 (USD)
- Total cohort cost: $4.781

## Notes

Effort=high chosen by Tsuge sweep (low/medium/high): accuracy improves monotonically but only +1.14pt from low to high while cost rises 1.9x. reasoning_effort=none is rejected by the API (HTTP 400). See test/issues/2026-09-05_tsuge10_md_gpt6_astra_effort_sweep/.
