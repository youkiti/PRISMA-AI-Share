# Kimi K2.6

- **Model id**: `moonshotai/kimi-k2.6`
- **Provider**: Moonshot
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  _(none)_
- **Unified JSON**: [`test/issues/2026-04-22_kimi_k2_6_moonshot_tsuge10_validation/results/md_moonshotai_kimi-k2.6_20260422_192742.json`](../../test/issues/2026-04-22_kimi_k2_6_moonshot_tsuge10_validation/results/md_moonshotai_kimi-k2.6_20260422_192742.json)
- **Pricing entry**: `moonshotai/kimi-k2.6`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 77.55 | 71.04 | 85.84 | 78.00 | 0.555 |
| Main body | 410 | 74.39 | 66.54 | 87.18 | 76.30 | 0.497 |
| Abstract | 120 | 88.33 | 97.67 | 83.12 | 85.71 | 0.761 |

TP / TN / FP / FN: 211 / 200 / 33 / 86 (correct 411 of 530)

## Performance

- Mean time per SR: 522.9 seconds
- Cost per SR: $0.048 (USD)
- Total cohort cost: $0.481

## Notes

Routed via Moonshot direct API; OpenRouter routes hung on long tool calls (see test/issues/2026-04-22_kimi_k2_6_openrouter_structured_output/).
