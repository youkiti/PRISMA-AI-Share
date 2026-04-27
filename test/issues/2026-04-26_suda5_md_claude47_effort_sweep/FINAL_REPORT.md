# FINAL REPORT — Claude Opus 4.7 Effort Sweep on Suda Parameter Optimization Cohort

- Date: 2026-04-26
- Model: `claude-opus-4-7`
- Dataset: Suda 2025 emergency medicine, 5 papers (canonical parameter optimization cohort)
  - `Suda2025_5, Suda2025_7, Suda2025_15, Suda2025_17, Suda2025_18`
- Pipeline: locked Markdown, simple schema, eande-first order, section-mode off
- Sweep: adaptive thinking effort ∈ {low, medium, high, xhigh, max}
- Total runtime: ~24 minutes wall-clock (07:11 → 07:35 JST)
- Total estimated API spend: ~$5.64

## Why this run replaces the 2026-04-17 Tsuge sweep for parameter selection

Anthropic released Claude Opus 4.7 during the rebuttal period (April 2026), after
the manuscript's parameter optimization phase had already closed. The original
2026-04-17 sweep
([test/issues/2026-04-17_tsuge10_md_claude47_effort_sweep/](../2026-04-17_tsuge10_md_claude47_effort_sweep/))
selected the adaptive-thinking effort level on the 10-paper Tsuge cohort — the
same set used to report Opus 4.7's validation accuracy in Figure 4. To match the
parameter-locking protocol used for all other Claude models (Opus 4.1, Sonnet
4.5), this run repeats the effort sweep on the canonical 5-paper Suda
parameter optimization cohort.

The Suda effort selection becomes the locked configuration cited in the
manuscript and rebuttal. The Suda sweep below shows that `low` matches `high`
on the priority sensitivity metric (93.26 % each) while strictly dominating
`high` on accuracy, specificity, Cohen κ, latency, and cost. Accordingly, the
Opus 4.7 row in Figure 4
([test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_claude-opus-4-7_20260417_074300.json](../2025-10-23_tsuge_md_validation_metrics/results/md_claude-opus-4-7_20260417_074300.json))
was re-pointed from the `effort=high` unified JSON of the 2026-04-17 sweep to
the `effort=low` JSON of the same sweep; no additional Tsuge run was
performed because the 2026-04-17 sweep already produced both effort variants
under the locked pipeline.

## Results

| effort | Acc | Prec | Rec (sens) | F1 | Spec | κ | mean t/SR (s) | tokens | $/SR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **low** | 79.25 | 81.08 | **93.26** | 86.75 | 41.67 | 0.3998 | 24.6 | 124,474 | 0.1653 |
| medium | 79.62 | 81.74 | 92.75 | 86.89 | 44.44 | 0.4194 | 27.8 | 125,834 | 0.1721 |
| high | 78.87 | 80.72 | **93.26** | 86.54 | 40.28 | 0.3858 | 37.9 | 129,591 | 0.1908 |
| xhigh | 77.36 | 80.37 | 91.19 | 85.44 | 40.28 | 0.3549 | 42.9 | 132,177 | 0.2038 |
| max | 79.62 | 82.33 | 91.71 | 86.76 | 47.22 | 0.4306 | 129.4 | 170,669 | 0.3962 |

Counts gating: every run satisfied overall=265 / main=205 / abstract=60.

## Selected effort: `low`

Rationale (consistent with the rebuttal letter's stated screening use-case):

1. **Highest sensitivity, tied with `high`** at 93.26%. Sensitivity is the
   priority metric because missed PRISMA items are more costly than false
   alarms in a screening application.
2. **Tiebreaker against `high`**: among the two sensitivity-tied levels,
   `low` dominates `high` on every other reported metric (accuracy 79.25 vs
   78.87, specificity 41.67 vs 40.28, Cohen κ 0.400 vs 0.386), so it is the
   Pareto-superior choice.
3. **Cost and latency**: `low` runs in 24.6 s/SR at $0.165/SR versus `high` at
   37.9 s/SR and $0.191/SR (Suda cohort), giving a ~35 % speed-up and ~14 %
   cost reduction at no loss of sensitivity.
4. **Effort-level robustness**: accuracy ranges only 77.36–79.62 % across the
   five levels (2.26-pt spread), so the effort choice is not a dominant
   driver of validation performance.

## Comparison with the 2026-04-17 Tsuge sweep

For reference, the earlier 10-paper Tsuge sweep recorded accuracy /
sensitivity / specificity / κ of 78.68 / 91.92 / 61.80 / 0.554 (low),
80.38 / 93.27 / 63.95 / 0.590 (medium), 79.81 / 94.28 / 61.37 / 0.576 (high),
79.81 / 92.59 / 63.52 / 0.578 (xhigh), 81.51 / 90.91 / 69.53 / 0.617 (max).
On Tsuge, `low` is within 1.13 pt of `high` on accuracy and 2.4 pt on
sensitivity, so the choice of `low` keeps validation performance comparable
to `high` while being preferable on the Suda parameter optimization cohort
that drove the selection.

## Artefacts

```
results/
  md_claude-opus-4-7_20260426_071401.json   # low    <-- locked
  md_claude-opus-4-7_20260426_071636.json   # medium
  md_claude-opus-4-7_20260426_072006.json   # high
  md_claude-opus-4-7_20260426_072403.json   # xhigh
  md_claude-opus-4-7_20260426_073538.json   # max
  ai_evaluations_*, accuracy_summary_*, comparison_details_*  (raw trios per effort)
reports/
  effort_comparison.csv
  effort_comparison.md
logs/
  run_<effort>_<ts>.log, sweep_master.log
```

## Reproduction

```bash
bash test/issues/2026-04-26_suda5_md_claude47_effort_sweep/scripts/run_effort_sweep.sh
venv/bin/python test/issues/2026-04-26_suda5_md_claude47_effort_sweep/scripts/aggregate_effort_sweep.py
```
