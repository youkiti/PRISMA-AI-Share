# Qwen3.6 Plus

- **Model id**: `qwen/qwen3.6-plus`
- **Provider**: Alibaba (via OpenRouter)
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  _(none)_
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_qwen_qwen3.6-plus_20260416_205101.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_qwen_qwen3.6-plus_20260416_205101.json)
- **Pricing entry**: `openrouter/qwen3-6-plus`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 81.32 | 87.54 | 73.39 | 84.01 | 0.616 |
| Main body | 410 | 80.98 | 85.43 | 73.72 | 84.77 | 0.594 |
| Abstract | 120 | 82.50 | 100.00 | 72.73 | 80.37 | 0.656 |

TP / TN / FP / FN: 260 / 171 / 62 / 37 (correct 431 of 530)

## Performance

- Mean time per SR: 245.3 seconds
- Cost per SR: $0.050 (USD)
- Total cohort cost: $0.504
**Cost computation notes**: pricing_flag:variable_rate

## Notes

_(none)_
