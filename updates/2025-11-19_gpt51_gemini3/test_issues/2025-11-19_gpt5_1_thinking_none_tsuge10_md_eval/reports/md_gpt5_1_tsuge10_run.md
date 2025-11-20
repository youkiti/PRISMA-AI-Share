## GPT-5.1 reasoning-none Tsuge10 Markdown run log
The runner script invoked `PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run --dataset tsuge-prisma --paper-ids $(paste -sd, data/tsuge_selected_papers.txt) --model gpt-5.1 --checklist-format md --format md_gpt5_1_tsuge10_20251119_072534 --log-level INFO` with `GPT5_REASONING_EFFORT=none`, `ENABLE_TSUGE_PRISMA=true`, `STRUCTURED_DATA_SUBDIRS_OVERRIDE="supplement/data/tsuge2025/structured_prisma"`, and `PRISMA_EVALUATOR_MAX_WORKERS=1`. The evaluation started at 07:25:34 JST and the pipeline completed in ~83 s (finish: 07:26:57), producing unified outputs without retries or API faults.
The consolidated log is stored at `test/issues/2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval/logs/md_gpt5_1_tsuge10_20251119_072534.log`, and the copied unified evaluator JSON resides at `test/issues/2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval/results/md_gpt5_1_tsuge10_20251119_072534.json`. No secondary artifacts were generated because the evaluator output already included per-item details.

<!--
canonical: test/issues/2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval/results/md_gpt5_1_tsuge10_20251119_072534.json
finalized: test/issues/2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval/
regen: cd test/issues/2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval && scripts/run_gpt5_1_tsuge10_md.sh
consistency: Compare logs/md_gpt5_1_tsuge10_20251119_072534.log with prior Tsuge md GPT-5 runs to confirm identical CLI options
notes: Runtime ~83s end-to-end at reasoning-none; no API retries recorded.
-->
