# Gemini 3.8 Flash

- **Model id**: `gemini-3.8-flash`
- **Provider**: Google
- **Cohort**: tsuge_md_validation_10 (10 SRs, 530 comparable items)
- **Schema**: `simple`, checklist format `md`, order mode `eande-first`, section mode `off`
- **Locked parameters**:
  - `temperature`: `1.0`
  - `thinking_level`: `MEDIUM`
- **Unified JSON**: [`test/issues/2026-09-05_tsuge10_md_gemini38_flash_level_sweep/results/md_gemini-3.8-flash_20260905_091031.json`](../../test/issues/2026-09-05_tsuge10_md_gemini38_flash_level_sweep/results/md_gemini-3.8-flash_20260905_091031.json)
- **Pricing entry**: `google/gemini-3.8-flash`

## Metrics

| Slice | Items | Accuracy % | Sensitivity % | Specificity % | F1 % | Cohen κ |
|---|---:|---:|---:|---:|---:|---:|
| Overall | 530 | 82.26 | 86.20 | 77.25 | 84.49 | 0.638 |
| Main body | 410 | 81.95 | 84.25 | 78.21 | 85.26 | 0.620 |
| Abstract | 120 | 83.33 | 97.67 | 75.32 | 80.77 | 0.668 |

TP / TN / FP / FN: 256 / 180 / 53 / 41 (correct 436 of 530)

## Performance

- Mean time per SR: 25.1 seconds
- Cost per SR: $0.040 (USD)
- Total cohort cost: $0.397

## Notes

thinking_level=medium chosen by Tsuge sweep (low/medium): medium is +1.13pt over low on every metric at 2.1x cost ($0.040 vs $0.019/SR); see test/issues/2026-09-05_tsuge10_md_gemini38_flash_level_sweep/.
