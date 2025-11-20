# 2025-11-19 — GPT-5.1 (Reasoning None) Tsuge10 Markdown Evaluation

## Objective
Establish a GPT-5.1 baseline without reasoning tokens on the Tsuge2025-PRISMA 10-paper subset so that manuscript discussions of checklist-format sensitivity/specificity can reference a thinking-free GPT-5.x control next to the existing reasoning-minimal or high baselines.

## Setup reference
- Paper list: `data/tsuge_selected_papers.txt` (seed `20250928`, copied from the 2025-09-28 Tsuge random-10 issue).
- Dataset toggles: `ENABLE_SUDA=false`, `ENABLE_TSUGE_PRISMA=true`, `ENABLE_TSUGE_OTHER=false`, `STRUCTURED_DATA_SUBDIRS_OVERRIDE="supplement/data/tsuge2025/structured_prisma"`.
- CLI: `--schema-type simple --section-mode off --checklist-format md --model gpt-5.1 --gpt5-reasoning none --order-mode eande-first`.
- Runner script: `scripts/run_gpt5_1_tsuge10_md.sh` (copies JSON from `results/evaluator_output/` into `results/md_gpt5_1_tsuge10_<timestamp>.json`).

## Deliverables
- Unified evaluator JSON + log for the GPT-5.1 reasoning-none run (`results/` and `logs/`).
- Run report (`reports/md_gpt5_1_tsuge10_run.md`) plus metric summary vs. `2025-10-23_tsuge_md_validation_metrics` (`reports/md_gpt5_1_tsuge10_summary.md`).
- Optional `reports/format_counts_update.md` if the results flow into the manuscript “Counts (overall/main/abstract)” table.

## Status checklist
- [x] Create issue scaffold (plan, script, directories, reproducibility notes).
- [ ] Execute GPT-5.1 reasoning-none run via script and archive evaluator output.
- [ ] Draft run log summary and metrics comparison report.
- [ ] Update manuscript tables/scripts if the reasoning-none baseline is adopted for publication.

## Quickstart
```bash
cd test/issues/2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval
scripts/run_gpt5_1_tsuge10_md.sh
```

Post-run, point manuscript references to this issue and re-run the 2025-09-27 format-count scripts when any `Counts` tables need refresh.
