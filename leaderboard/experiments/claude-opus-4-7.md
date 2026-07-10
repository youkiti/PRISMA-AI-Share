# Claude Opus 4.7

- **Model id**: `claude-opus-4-7`
- **Provider**: Anthropic
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `effort`: `low`
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_claude-opus-4-7_20260417_074300.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_claude-opus-4-7_20260417_074300.json)
- **Pricing entry**: `anthropic/claude-opus-4-7`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 78.68 | 91.92 | 61.80 | 82.85 | 0.554 |
| Main body | 410 | 79.02 | 90.94 | 59.62 | 84.31 | 0.532 |
| Abstract | 120 | 77.50 | 97.67 | 66.23 | 75.68 | 0.566 |

TP / TN / FP / FN: 273 / 144 / 89 / 24 (correct 417 of 530)

## Performance

- Mean time per SR: 25.4 seconds
- Cost per SR: $0.158 (USD)
- Total cohort cost: $1.583

## Notes

Effort=low locked by the Suda5 parameter-optimization sweep (2026-04-26): ties high on sensitivity, dominates on accuracy/specificity/kappa/latency; see test/issues/2026-04-26_suda5_md_claude47_effort_sweep/.
