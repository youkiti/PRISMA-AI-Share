# DeepSeek V4 Pro

- **Model id**: `deepseek/deepseek-v4-pro`
- **Provider**: DeepSeek (via OpenRouter)
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `tool_choice`: `auto`
  - `reasoning_exclude`: `True`
- **Unified JSON**: [`test/issues/2026-04-25_deepseek_v4_pro_tsuge10_validation/results/md_deepseek_deepseek-v4-pro_20260425_094204.json`](../../test/issues/2026-04-25_deepseek_v4_pro_tsuge10_validation/results/md_deepseek_deepseek-v4-pro_20260425_094204.json)
- **Pricing entry**: `deepseek/deepseek-v4-pro`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 80.94 | 76.43 | 86.70 | 81.80 | 0.620 |
| Main body | 410 | 79.76 | 76.38 | 85.26 | 82.38 | 0.589 |
| Abstract | 120 | 85.00 | 76.74 | 89.61 | 78.57 | 0.670 |

TP / TN / FP / FN: 227 / 202 / 31 / 70 (correct 429 of 530)

## Performance

- Mean time per SR: 177.3 seconds
- Cost per SR: $0.053 (USD)
- Total cohort cost: $0.526

## Notes

Tool calling via tool_choice=auto (forced rejected upstream); see test/issues/2026-04-25_deepseek_v4_pro_openrouter_capability_check/ for capability probes.
