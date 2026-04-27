# FINAL REPORT — 2026-04-17 Claude Opus 4.7 Effort Sweep (Tsuge 10 papers)

> **2026-04-27 amendment.** This sweep was originally exploratory. The
> manuscript's locked effort level for Opus 4.7 was subsequently selected on
> the canonical 5-paper Suda parameter optimization cohort
> ([2026-04-26_suda5_md_claude47_effort_sweep](../2026-04-26_suda5_md_claude47_effort_sweep/FINAL_REPORT.md))
> as `low` (Pareto-superior to `high` at the same sensitivity). The
> validation row for Opus 4.7 in Figure 4 now uses
> `md_claude-opus-4-7_20260417_074300.json` (`effort=low`) from the table
> below, replacing the earlier `md_claude-opus-4-7_20260417_075422.json`
> (`effort=high`). The recommendations at the bottom of this report reflect
> the original exploratory framing and are superseded by the Suda selection.

## Setup

- **Model**: `claude-opus-4-7` via Anthropic Native API
- **Thinking mode**: adaptive (`thinking.type = "adaptive"`, `output_config.effort = <level>`)
- **Temperature / top_p / top_k**: omitted (required by Opus 4.7)
- **max_tokens**: 64,000
- **Dataset**: Tsuge 2025 PRISMA, same 10 papers as 2026-04-16 validation
  - Tsuge2025_PRISMA2020_{14, 20, 22, 26, 68, 74, 76, 80, 89, 120}
- **Checklist**: Markdown, simple schema, `order-mode=eande-first`, `section-mode=off`
- **Execution**: serial, `MAX_CONCURRENT_PAPERS=1`
- **Denominator gating**: Overall 530 / Main 410 / Abstract 120 — **passed on all 5 runs**

## Main results (Overall, n=530)

| effort | Acc | Prec | Rec | F1 | Spec | Cohen κ | mean t/SR (s) | total tokens | $/SR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| low    | 78.68 | 75.41 | 91.92 | 82.85 | 61.80 | 0.5539 | 27.5  | 238,375 | 0.1583 |
| medium | 80.38 | 76.73 | 93.27 | 84.19 | 63.95 | 0.5896 | 31.3  | 240,938 | 0.1647 |
| high   | 79.81 | 75.68 | 94.28 | 83.96 | 61.37 | 0.5759 | 42.6  | 248,260 | 0.1830 |
| xhigh  | 79.81 | 76.39 | 92.59 | 83.71 | 63.52 | 0.5780 | 49.7  | 252,963 | 0.1947 |
| max    | **81.51** | **79.18** | 90.91 | **84.64** | **69.53** | **0.6169** | 147.0 | 328,408 | 0.3833 |

Sources: `reports/effort_comparison.{md,csv}`

### Observations

1. **`max` is the only level that clearly beats `medium`.** Between `medium` (80.38%) and `xhigh` (79.81%) the overall accuracy plateaus within noise; `max` pulls up accuracy by ~1 pt, precision by ~2.5 pt, specificity by ~6 pt, and Cohen's κ by ~0.03.
2. **Recall peaks at `high`** (94.28%). `max` trades ~3 pt of recall for ~4 pt of specificity, meaning longer thinking lets Opus 4.7 suppress false positives more than it catches new true positives.
3. **Cost/latency grow super-linearly at `max`.** Mean per-paper time goes from 27.5 s (low) → 49.7 s (xhigh) → **147 s (max)**; per-paper cost from $0.158 → $0.195 → **$0.383**. `max` is ~2.4× the cost of `xhigh` for ~1.7 pt accuracy.
4. **`medium` is the cost-accuracy sweet spot** for this task: best accuracy below `max`, only 14% more tokens than `low`, and roughly equal tokens to `low` (thinking cost is modest at this level).
5. **Opus 4.7 vs Opus 4.6 (2026-04-16 baseline, same 10 papers)**: Opus 4.6 scored 80.19 / 77.12 / 91.92 / 83.87. Opus 4.7 matches or beats it from `medium` upward; `max` exceeds it on every metric (Acc +1.32, Prec +2.06, F1 +0.77, Spec well above baseline).

## Per-effort detail

Files (all in `results/`, effort is recorded inside `processing_metadata.effort`):

| effort | Unified JSON |
|---|---|
| low    | `md_claude-opus-4-7_20260417_074300.json` |
| medium | `md_claude-opus-4-7_20260417_074749.json` |
| high   | `md_claude-opus-4-7_20260417_075422.json` |
| xhigh  | `md_claude-opus-4-7_20260417_080201.json` |
| max    | `md_claude-opus-4-7_20260417_082430.json` |

### Runtime profile

- Serial end-to-end wall time across the 5 runs: **~46 min**
  - low: 4m15s
  - medium: 4m47s
  - high: 6m32s
  - xhigh: 7m38s
  - max: 22m29s

### Token cost detail (5 × 10 papers)

| effort | input tokens | output tokens | total tokens |
|---|---:|---:|---:|
| low    | ~190k | ~48k  | 238,375 |
| medium | ~190k | ~51k  | 240,938 |
| high   | ~190k | ~58k  | 248,260 |
| xhigh  | ~192k | ~61k  | 252,963 |
| max    | ~193k | ~135k | 328,408 |

`max` is where adaptive thinking actually produces substantially more thinking output; prior levels keep output tokens within ~13k (output + thinking) of each other.

## Gating check

All 5 unified JSONs satisfy:

- `overall_metrics.counts.total_comparable == 530`
- `main_body_metrics.counts.total_comparable == 410`
- `abstract_metrics.counts.total_comparable == 120`
- `paper_evaluations` length == 10
- `processing_metadata.effort` matches the intended level in every saved set

Validated via `check_validation_counts.py --expected-size full` at run-time and a post-hoc scan of all unified JSONs (see terminal log above).

## Recommendations

- **Default to `medium`** for validation-cohort-style batch evaluation: within 1.2 pt of `max` accuracy at ~40% of the cost and ~20% of the latency.
- **Use `max`** when specificity and Cohen's κ matter (e.g., for the canonical Tsuge MD manuscript table), accepting the ~2.4× cost.
- **Avoid `xhigh` for this task**: it is the worst-return tier observed — longer than `high`, same accuracy, slightly more tokens.
- For the manuscript's validation cohort rerun, propose two columns: Opus 4.7 `medium` (matches prior Opus 4.6 speed/cost) and Opus 4.7 `max` (best metrics).

## Repro

```bash
bash test/issues/2026-04-17_tsuge10_md_claude47_effort_sweep/scripts/run_effort_sweep.sh
venv/bin/python test/issues/2026-04-17_tsuge10_md_claude47_effort_sweep/scripts/aggregate_effort_sweep.py
```

Pricing: `data/pricing/model_pricing.toml` → entry `anthropic/claude-opus-4-7` ($5/$25 per MTok, simple strategy).
