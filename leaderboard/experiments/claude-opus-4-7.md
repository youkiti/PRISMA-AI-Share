# Claude Opus 4.7

- **Model id**: `claude-opus-4-7`
- **Provider**: Anthropic
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `effort`: `high`
- **Unified JSON**: [`test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_claude-opus-4-7_20260417_075422.json`](../../test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_claude-opus-4-7_20260417_075422.json)
- **Pricing entry**: `anthropic/claude-opus-4-7`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 79.81 | 94.28 | 61.37 | 83.96 | 0.576 |
| Main body | 410 | 80.98 | 93.70 | 60.26 | 85.92 | 0.572 |
| Abstract | 120 | 75.83 | 97.67 | 63.64 | 74.34 | 0.538 |

TP / TN / FP / FN: 280 / 143 / 90 / 17 (correct 423 of 530)

## Performance

- Mean time per SR: 39.2 seconds
- Cost per SR: $0.183 (USD)
- Total cohort cost: $1.830

## Notes

Effort level chosen by Tsuge sweep (low/medium/high/xhigh/max); see test/issues/2026-04-17_tsuge10_md_claude47_effort_sweep/.
