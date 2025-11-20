# Plan: GPT-5.1 (Reasoning High) Tsuge 10-paper Markdown Evaluation

## Objective
Quantify the impact of forcing GPT-5.1 into highest reasoning mode on the Tsuge2025 PRISMA 10-paper subset while keeping all other checklist and dataset parameters identical to the reasoning-none baseline, so that manuscript discussions can contrast token-intensive vs. fast routes.

## Scope
- Dataset: `tsuge-prisma`, using the seed-20250928 10-paper list reused from prior Tsuge md validations.
- Model: GPT-5.1 through the unified evaluator, exporting `GPT5_REASONING_EFFORT=high` before invocation (avoid touching `.env`).
- Format: Markdown checklist (`--checklist-format md`), simple schema defaults.
- Deliverables: evaluator JSON, logs, run report, metrics delta vs. reasoning-none issue.

## Tasks
- [ ] Validate paper list presence under `data/tsuge_selected_papers.txt` (copied from reasoning-none issue).
- [ ] Run GPT-5.1 with reasoning effort high via `scripts/run_gpt5_1_tsuge10_md_high.sh`, storing outputs/logs.
- [ ] Draft run description (`reports/md_gpt5_1_tsuge10_high_run.md`) covering runtime/token deltas vs. reasoning-none.
- [ ] Summarize metrics vs. the none-run and earlier Tsuge md baselines in `reports/md_gpt5_1_tsuge10_high_summary.md`.
- [ ] If manuscript tables need both extremes, document update commands (e.g., `test/issues/2025-09-27_gpt_oss_single_paper_formats/scripts/update_format_table.py`) in `reports/format_counts_update.md`.

## CLI sketch
```bash
PAPERS=$(grep -v '^#' data/tsuge_selected_papers.txt | paste -sd, -)
GPT5_REASONING_EFFORT=high \
PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run \
  --dataset tsuge-prisma \
  --paper-ids "$PAPERS" \
  --model gpt-5.1 \
  --checklist-format md \
  --log-level INFO | tee logs/md_gpt5_1_tsuge10_high.log
```

## Notes
- Reuse environment toggles from the reasoning-none issue: `ENABLE_SUDA=false`, `ENABLE_TSUGE_PRISMA=true`, `STRUCTURED_DATA_SUBDIRS_OVERRIDE="supplement/data/tsuge2025/structured_prisma"`.
- Never edit `.env`; export reasoning overrides per-shell or inside the run script.
- Capture any observable changes in completion latency/token usage to inform manuscript narrative.

<!--
canonical: results/md_gpt5_1_tsuge10_high.json
finalized: test/issues/2025-11-19_gpt5_1_thinking_high_tsuge10_md_eval/
regen: GPT5_REASONING_EFFORT=high PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run --dataset tsuge-prisma --paper-ids $(paste -sd, data/tsuge_selected_papers.txt) --model gpt-5.1 --checklist-format md --log-level INFO | tee logs/md_gpt5_1_tsuge10_high.log
consistency: Compare against reasoning-none results (2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval) and prior Tsuge md baselines; refresh Counts tables via 2025-09-27 scripts if adopted
notes: Requires OPENAI_API_KEY in environment; maintain same structured data overrides as earlier runs.
-->
