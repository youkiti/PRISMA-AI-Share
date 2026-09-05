# Grok-4.6

- **Model id**: `x-ai/grok-4.6`
- **Provider**: xAI
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `reasoning_effort`: `low`
- **Unified JSON**: [`test/issues/2026-09-05_tsuge10_md_grok46_effort_sweep/results/md_x-ai_grok-4.6_20260905_110737.json`](../../test/issues/2026-09-05_tsuge10_md_grok46_effort_sweep/results/md_x-ai_grok-4.6_20260905_110737.json)
- **Pricing entry**: `xai/grok-4-6`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 83.40 | 85.19 | 81.12 | 85.19 | 0.663 |
| Main body | 410 | 81.22 | 82.68 | 78.85 | 84.51 | 0.607 |
| Abstract | 120 | 90.83 | 100.00 | 85.71 | 88.66 | 0.811 |

TP / TN / FP / FN: 253 / 189 / 44 / 44 (correct 442 of 530)

## Performance

- Mean time per SR: 59.2 seconds
- Cost per SR: $0.055 (USD)
- Total cohort cost: $0.545

## Notes

Routed via xAI direct (OpenRouter upstream times out on long tool calls). Effort=low chosen by Tsuge sweep (low/medium) on sensitivity: low misses fewer reported items (sensitivity 85.19%, 44 FN vs medium 83.84%, 48 FN) at 0.6x the cost and 0.4x the latency. Raising effort improves specificity (81.12 -> 85.84%) and accuracy (83.40 -> 84.72%), not sensitivity. reasoning_effort none/max are rejected by the API (HTTP 400). See test/issues/2026-09-05_tsuge10_md_grok46_effort_sweep/.
