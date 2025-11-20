## GPT-5.1 reasoning-high Tsuge10 Markdown run log
`scripts/run_gpt5_1_tsuge10_md_high.sh` exported `GPT5_REASONING_EFFORT=high` (all other dataset toggles matched the reasoning-none baseline) and called `PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run --dataset tsuge-prisma --paper-ids $(paste -sd, data/tsuge_selected_papers.txt) --model gpt-5.1 --checklist-format md --format md_gpt5_1_tsuge10_high_20251119_073254 --log-level INFO`. After an initial attempt timed out at the CLI wrapper level (log: `logs/md_gpt5_1_tsuge10_high_20251119_073014.log`), the second invocation at 07:32:55 JST ran to completion in ~8 min 37 s (finish 07:41:32), reflecting the longer reasoning traces.
The definitive log is `test/issues/2025-11-19_gpt5_1_thinking_high_tsuge10_md_eval/logs/md_gpt5_1_tsuge10_high_20251119_073254.log`, and the evaluator output copied from `results/evaluator_output/` is `test/issues/2025-11-19_gpt5_1_thinking_high_tsuge10_md_eval/results/md_gpt5_1_tsuge10_high_20251119_073254.json`. All 10 papers were processed without retries or missing items (only expected +1 main-item echo noted by the metrics script).

<!--
canonical: test/issues/2025-11-19_gpt5_1_thinking_high_tsuge10_md_eval/results/md_gpt5_1_tsuge10_high_20251119_073254.json
finalized: test/issues/2025-11-19_gpt5_1_thinking_high_tsuge10_md_eval/
regen: cd test/issues/2025-11-19_gpt5_1_thinking_high_tsuge10_md_eval && scripts/run_gpt5_1_tsuge10_md_high.sh
consistency: Verify log timestamps bracket the 8m37s duration and that the copied JSON hash matches results/evaluator_output/comparison_details_gpt-5.1_md_20251119_074132.json
notes: Preserve the earlier timeout log as reference for CLI-level wall-clock budgeting when reasoning_effort=high.
-->
