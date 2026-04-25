# Qwen3-235B

- **Model id**: `qwen/qwen3-235b-a22b-2507`
- **Provider**: Alibaba (via OpenRouter)
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  _(none)_
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_qwen_qwen3-235b-a22b-2507_20251023_184404.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_qwen_qwen3-235b-a22b-2507_20251023_184404.json)
- **Pricing entry**: `openrouter/qwen3-235b`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 79.43 | 93.94 | 60.94 | 83.66 | 0.568 |
| Main body | 410 | 79.51 | 92.91 | 57.69 | 84.89 | 0.538 |
| Abstract | 120 | 79.17 | 100.00 | 67.53 | 77.48 | 0.599 |

TP / TN / FP / FN: 279 / 142 / 91 / 18 (correct 421 of 530)

## Performance

- Mean time per SR: 53.7 seconds
- Cost per SR: $0.003 (USD)
- Total cohort cost: $0.035

## Notes

_(none)_
