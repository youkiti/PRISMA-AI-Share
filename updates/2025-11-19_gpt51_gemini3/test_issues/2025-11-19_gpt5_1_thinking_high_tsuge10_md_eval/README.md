# 2025-11-19 — GPT-5.1 (Reasoning High) Tsuge10 Markdown Evaluation

## Objective
Measure whether enabling GPT-5.1 high reasoning effort improves Tsuge PRISMA Markdown accuracy relative to the reasoning-none baseline executed earlier the same day, keeping data, schema, and format constant.

## Setup reference
- Paper list: `data/tsuge_selected_papers.txt` (seed `20250928`).
- Dataset toggles: `ENABLE_SUDA=false`, `ENABLE_TSUGE_PRISMA=true`, `ENABLE_TSUGE_OTHER=false`, `STRUCTURED_DATA_SUBDIRS_OVERRIDE="supplement/data/tsuge2025/structured_prisma"`.
- CLI core: `--dataset tsuge-prisma --paper-ids <list> --model gpt-5.1 --checklist-format md` with `GPT5_REASONING_EFFORT=high` exported in the run script.
- Runner: `scripts/run_gpt5_1_tsuge10_md_high.sh` (mirrors reasoning-none script but forces reasoning high).

## Deliverables
- `results/md_gpt5_1_tsuge10_high_<timestamp>.json` plus the corresponding log under `logs/`.
- `reports/md_gpt5_1_tsuge10_high_run.md` (runtime/token observations) and `reports/md_gpt5_1_tsuge10_high_summary.md` (metric comparison vs. reasoning-none and older baselines).
- Optional manuscript table delta report.

## Status checklist
- [x] Create issue scaffold (plan, README, paper list copy, script stub directories).
- [ ] Run GPT-5.1 reasoning-high evaluation and archive outputs/logs.
- [ ] Document run details + metric comparisons.
- [ ] Update manuscript tables if reasoning-high is cited.

## Quickstart
```bash
cd test/issues/2025-11-19_gpt5_1_thinking_high_tsuge10_md_eval
scripts/run_gpt5_1_tsuge10_md_high.sh
```
