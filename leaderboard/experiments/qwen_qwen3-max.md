# Qwen3-Max

- **Model id**: `qwen/qwen3-max`
- **Provider**: Alibaba (via OpenRouter)
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  _(none)_
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_qwen_qwen3-max_20251023_184404.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_qwen_qwen3-max_20251023_184404.json)
- **Pricing entry**: `openrouter/qwen3-max`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 77.92 | 95.96 | 54.94 | 82.97 | 0.532 |
| Main body | 410 | 79.27 | 95.28 | 53.21 | 85.06 | 0.524 |
| Abstract | 120 | 73.33 | 100.00 | 58.44 | 72.88 | 0.502 |

TP / TN / FP / FN: 285 / 128 / 105 / 12 (correct 413 of 530)

## Performance

- Mean time per SR: 56.1 seconds
- Cost per SR: $0.027 (USD)
- Total cohort cost: $0.274
**Cost computation notes**: pricing_flag:variable_rate

## Notes

32k output cap; reasoning disabled (provider does not expose it).
