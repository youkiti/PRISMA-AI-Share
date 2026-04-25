# GPT-OSS-120B

- **Model id**: `openai/gpt-oss-120b`
- **Provider**: OpenAI (via OpenRouter)
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `reasoning_effort`: `high`
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_openai_gpt-oss-120b_20251023_184404.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_openai_gpt-oss-120b_20251023_184404.json)
- **Pricing entry**: `openrouter/gpt-oss-120b`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 80.94 | 89.56 | 69.96 | 84.04 | 0.606 |
| Main body | 410 | 81.22 | 90.16 | 66.67 | 85.61 | 0.588 |
| Abstract | 120 | 80.00 | 86.05 | 76.62 | 75.51 | 0.590 |

TP / TN / FP / FN: 266 / 163 / 70 / 31 (correct 429 of 530)

## Performance

- Mean time per SR: 42.8 seconds
- Cost per SR: $0.002 (USD)
- Total cohort cost: $0.020

## Notes

_(none)_
