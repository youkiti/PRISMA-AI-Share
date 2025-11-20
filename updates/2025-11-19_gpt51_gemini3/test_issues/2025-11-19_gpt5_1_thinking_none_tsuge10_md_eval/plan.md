# Plan: GPT-5.1 (Reasoning None) Tsuge 10-paper Markdown Evaluation

## Objective
Quantify GPT-5.1 performance on the Tsuge2025 PRISMA 10-paper subset when the OpenAI reasoning effort is explicitly forced to `none` while keeping the Markdown checklist configuration aligned with the manuscript’s multi-format benchmarks. Results will inform whether thinking-free GPT-5.1 runs can be cited as a lower-bound comparator in the checklist-format section.

## Scope
- Dataset: `tsuge-prisma` (10-paper CC-filtered subset reused from the 2025-09-28 random selection).
- Model route: OpenAI GPT-5.1 via the unified evaluator with `--gpt5-reasoning none` (double-check that `GPT5_REASONING_EFFORT` is overridden to avoid defaults, and never edit `.env`).
- Checklist configuration: `--schema-type simple --section-mode off --checklist-format md`, mirroring earlier Tsuge markdown validation runs for comparability.
- Outputs: unified evaluator JSON + log file + Markdown run summary stored under this issue; downstream counts update via the 2025-09-27 scripts if metrics feed into manuscript tables.

## Tasks
- [ ] Verify/refresh `data/tsuge_selected_papers.txt` to ensure the 10-paper list (seed `20250928`) matches the baseline selection and document provenance (already staged, confirm before running).
- [ ] Run GPT-5.1 with reasoning set to none on the Tsuge list, saving the evaluator output to `results/md_gpt5_1_tsuge10.json` and teeing stdout/stderr into `logs/md_gpt5_1_tsuge10.log` for auditability.
- [ ] Produce a short Markdown run note in `reports/md_gpt5_1_tsuge10_run.md` capturing CLI parameters, tokens, runtime, and any anomalies relative to prior GPT-5 md runs.
- [ ] Summarize accuracy/sensitivity/specificity plus confusion-matrix deltas against `2025-10-23_tsuge_md_validation_metrics` in `reports/md_gpt5_1_tsuge10_summary.md`, referencing whether reasoning-none materially drifts from reasoning-minimal baselines.
- [ ] If this run affects manuscript `Counts (overall/main/abstract)`, execute `PYTHONPATH=. venv/bin/python test/issues/2025-09-27_gpt_oss_single_paper_formats/scripts/update_format_table.py --dataset tsuge-prisma --format md --model gpt-5.1` (or extend arguments as needed) and capture the updated table snapshot in `reports/format_counts_update.md`.
- [ ] Archive evaluator outputs (JSON + optional item-level extracts) under `results/` and ensure redundant copies in `results/evaluator_output/` are cleared once linked here, per repository hygiene guidelines.

## CLI sketch
```bash
PAPERS=$(grep -v '^#' data/tsuge_selected_papers.txt | paste -sd, -)
PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run \
  --dataset tsuge-prisma \
  --paper-ids "$PAPERS" \
  --model gpt-5.1 \
  --schema-type simple --section-mode off --checklist-format md \
  --gpt5-reasoning none \
  --log-level INFO \
  | tee logs/md_gpt5_1_tsuge10.log
```
Set `GPT5_REASONING_EFFORT=none` in the shell session (not `.env`) if the CLI flag is unavailable in downstream wrappers. Confirm OpenAI credentials are already configured in `.env` but keep that file untouched.

## Notes
- Coordinate with `test/issues/2025-11-18_gemini3_pro_suda_tsuge_md_eval` and `2025-10-23_tsuge_md_validation_metrics` when framing results; reuse their report templates where possible.
- Any post-processing (e.g., `analysis/item_level_error_profile.py --dataset tsuge=results/md_gpt5_1_tsuge10.json`) should be logged within `reports/` alongside the commands for reproducibility.
- After verification, link manuscript references back to this issue per `AGENTS.md` reproducibility guidance.

<!--
canonical: results/md_gpt5_1_tsuge10.json
finalized: test/issues/2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval/
regen: PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run --dataset tsuge-prisma --paper-ids $(paste -sd, data/tsuge_selected_papers.txt) --model gpt-5.1 --schema-type simple --section-mode off --checklist-format md --gpt5-reasoning none --log-level INFO | tee logs/md_gpt5_1_tsuge10.log
consistency: Compare overall_metrics to 2025-10-23_tsuge_md_validation_metrics and ensure Count tables regenerated via test/issues/2025-09-27_gpt_oss_single_paper_formats/scripts/update_format_table.py when needed
notes: Keep GPT5_REASONING_EFFORT overrides scoped to the shell; never edit .env or expose API secrets in reports.
-->
