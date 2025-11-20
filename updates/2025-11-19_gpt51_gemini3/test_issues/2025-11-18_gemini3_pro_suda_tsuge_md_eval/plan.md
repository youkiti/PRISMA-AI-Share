# Plan: Gemini 3 Pro Suda/Tsuge 10-paper Markdown Evaluation

## Objective
Evaluate the same 10-paper subsets used in the Suda multi-format scaling and Tsuge PRISMA random-10 experiments with Gemini 3 Pro in Markdown checklist format, and summarize accuracy, sensitivity, and specificity for manuscript-facing discussion of Gemini’s behaviour on cc-filtered emergency medicine and rehabilitation reviews.

## Scope
- Datasets: Suda2025 (CC-BY subset, 10 papers from `2025-09-27_suda_multi_format_scaling`) and Tsuge2025-PRISMA (10 papers from `2025-09-28_tsuge_random10_gpt4o_qwen_ensemble`).
- Model route: Google Gemini Direct API with `--model gemini-2.5-pro` and `--gemini-model gemini-3-pro-preview` (thinking level initially left at default `high` for Gemini 3).
- Checklist configuration: `--schema-type simple`, `--section-mode off`, `--checklist-format md`, matching prior Suda multi-format and Tsuge md validation runs.
- Evaluation granularity: unified evaluator outputs with `overall_metrics` plus optional item-level FN/FP profiles via `analysis/item_level_error_profile.py`.

## Tasks
- [ ] Copy the Suda and Tsuge 10-paper ID lists into this issue (for example `data/suda_selected_papers.txt` from `test/issues/2025-09-27_suda_multi_format_scaling/data/selected_papers.txt` and `data/tsuge_selected_papers.txt` from `test/issues/2025-09-28_tsuge_random10_gpt4o_qwen_ensemble/data/selected_papers.txt`), documenting seeds and source paths at the top of each file.
- [ ] Run Gemini 3 Pro on the Suda 10-paper subset with Markdown checklist format, using the Google Direct evaluator (`ENABLE_GEMINI_DIRECT=true`, `GEMINI_API_KEY` set in `.env`) and copy the unified evaluator JSON into `results/md_gemini3_suda10.json` with a short run log summary in `reports/md_gemini3_suda10_run.md`.
- [ ] Run Gemini 3 Pro on the Tsuge PRISMA 10-paper subset with the same CLI settings (only changing `--dataset tsuge-prisma` and the paper list), and store the unified evaluator JSON as `results/md_gemini3_tsuge10.json` plus a brief run note in `reports/md_gemini3_tsuge10_run.md`.
- [ ] Aggregate per-dataset metrics (accuracy, sensitivity, specificity, and confusion matrices) from the unified outputs and write a concise comparison note in `reports/gemini3_md_suda_tsuge10_summary.md`, aligning terminology with existing Tsuge MD validation (`2025-10-23_tsuge_md_validation_metrics`) and Suda multi-format scaling (`2025-09-27_suda_multi_format_scaling`).
- [ ] Optionally run `analysis/item_level_error_profile.py` with `--dataset suda=results/md_gemini3_suda10.json` and `--dataset tsuge=results/md_gemini3_tsuge10.json` to generate FN/FP-prone item lists for each dataset, and record any notable items or patterns that differ from GPT-5 and Qwen in `reports/gemini3_md_item_level_notes.md`.
- [ ] Decide whether these 10-paper Gemini 3 Pro md results should feed into any existing `Counts (overall/main/abstract)` tables; if so, extend the relevant `test/issues/2025-09-27_*` update scripts or add a lightweight wrapper script under `scripts/` and document the integration path for future manuscript updates.

## CLI sketch
The initial Suda 10-paper run is expected to mirror the Suda multi-format scaling settings, with the model parameters adjusted for Gemini 3:

```bash
PAPERS=$(grep -v '^#' data/suda_selected_papers.txt | paste -sd, -)
BASE_CMD=(PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run \
  --schema-type simple --section-mode off --checklist-format md \
  --paper-ids "$PAPERS" \
  --model gemini-2.5-pro \
  --gemini-model gemini-3-pro-preview)

ENABLE_SUDA=true ENABLE_TSUGE_PRISMA=false ENABLE_TSUGE_OTHER=false \
ENABLE_GEMINI_DIRECT=true \
  "${BASE_CMD[@]}" | tee logs/gemini3_suda10_md.log
```

For Tsuge, the same pattern applies, swapping dataset flags:

```bash
PAPERS=$(grep -v '^#' data/tsuge_selected_papers.txt | paste -sd, -)
BASE_CMD=(PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run \
  --schema-type simple --section-mode off --checklist-format md \
  --paper-ids "$PAPERS" \
  --model gemini-2.5-pro \
  --gemini-model gemini-3-pro-preview)

ENABLE_SUDA=false ENABLE_TSUGE_PRISMA=true ENABLE_TSUGE_OTHER=false \
ENABLE_GEMINI_DIRECT=true \
  "${BASE_CMD[@]}" | tee logs/gemini3_tsuge10_md.log
```

## Notes
- Keep `.env` unchanged and rely on existing `GEMINI_API_KEY` and dataset toggles; do not hardcode any API keys in scripts or reports.
- When comparing with previous experiments, use `test/issues/2025-09-11_checklist_format_gemini`, `test/issues/2025-09-27_suda_multi_format_scaling`, and `test/issues/2025-09-28_tsuge_random10_gpt4o_qwen_ensemble` as primary baselines for format, dataset, and ensemble behaviour.
- Once the runs and summaries are stable, consider adding a short English summary paragraph for the manuscript Results section (checklist format experiments) and track its location in this issue’s `reports/` for later integration.

<!--
canonical: results/md_gemini3_suda10.json; results/md_gemini3_tsuge10.json
finalized: test/issues/2025-11-18_gemini3_pro_suda_tsuge_md_eval/
regen: PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run --model gemini-2.5-pro --gemini-model gemini-3-pro-preview --schema-type simple --section-mode off --checklist-format md --paper-ids $(paste -sd, data/suda_selected_papers.txt); PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run --model gemini-2.5-pro --gemini-model gemini-3-pro-preview --schema-type simple --section-mode off --checklist-format md --paper-ids $(paste -sd, data/tsuge_selected_papers.txt)
consistency: Compare overall_metrics and confusion matrices against prior Suda multi-format and Tsuge md validation runs; optionally cross-check item-level FN/FP rankings via analysis/item_level_error_profile.py
notes: Requires ENABLE_GEMINI_DIRECT=true and GEMINI_API_KEY to be set in the environment; do not modify .env from this issue.
-->

