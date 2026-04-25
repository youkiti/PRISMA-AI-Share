# Moonshot Kimi K2.6 Tsuge10 Validation Summary

Validation run for `moonshotai/kimi-k2.6` on the locked Tsuge 10-paper set completed successfully through the direct Moonshot endpoint with `thinking=enabled`, `schema-type=simple`, and `checklist-format=md`. The direct evaluator was switched from OpenRouter to `https://api.moonshot.ai/v1`, and the Moonshot parser was hardened to accept markdown-fenced JSON payloads that occasionally appear when thinking is enabled.

The final unified result is `results/md_moonshotai_kimi-k2.6_20260422_192742.json`. Validation counts were confirmed with `overall=530`, `main=410`, and `abstract=120`, and model identifiers were consistent across CLI metadata, execution metadata, and per-paper outputs.

Overall performance was `77.55%` accuracy (`411/530`), with precision `86.48%`, recall `71.04%`, specificity `85.84%`, and F1 `78.00%`. Main-body performance was `74.39%` accuracy (`305/410`), with precision `89.42%`, recall `66.54%`, specificity `87.18%`, and F1 `76.30%`. Abstract performance was `88.33%` accuracy (`106/120`), with precision `76.36%`, recall `97.67%`, specificity `83.12%`, and F1 `85.71%`.

Per-paper end-to-end processing time averaged `522.92s` with median `515.96s`, minimum `403.40s`, maximum `723.76s`, and total wall-clock processing time `5229.20s`. Token usage averaged `28,480.4` tokens per paper, with `121,334` input tokens, `163,470` output tokens, and `284,804` total tokens across the full run.

Artifacts produced for this issue are the raw pipeline outputs `results/ai_evaluations_moonshotai_kimi-k2.6_md_20260422_192742.json`, `results/accuracy_summary_moonshotai_kimi-k2.6_md_20260422_192742.json`, and `results/comparison_details_moonshotai_kimi-k2.6_md_20260422_192742.json`, together with the unified validation file `results/md_moonshotai_kimi-k2.6_20260422_192742.json`.

<!--
canonical: prisma_evaluator/llm/moonshot_direct_evaluator.py, prisma_evaluator/core/pipeline.py, prisma_evaluator/cli/main.py, prisma_evaluator/config/settings.py
finalized: test/issues/2026-04-22_kimi_k2_6_moonshot_tsuge10_validation/results/, test/issues/2026-04-22_kimi_k2_6_moonshot_tsuge10_validation/reports/validation_summary.md
regen: MAX_CONCURRENT_PAPERS=1 PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run --model moonshotai/kimi-k2.6 --dataset tsuge-prisma --paper-ids "$(grep -v '^#' test/issues/2026-04-22_kimi_k2_6_moonshot_tsuge10_validation/data/tsuge_selected10.txt | sed '/^$/d' | paste -sd, -)" --schema-type simple --checklist-format md --kimi-thinking enabled --log-level INFO && PYTHONPATH=. venv/bin/python test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/build_unified_validation_json.py --model-id moonshotai/kimi-k2.6 --format-type md --run-timestamp 20260422_192742 --source-dir results/evaluator_output --output-dir test/issues/2026-04-22_kimi_k2_6_moonshot_tsuge10_validation/results && PYTHONPATH=. venv/bin/python test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/check_validation_counts.py test/issues/2026-04-22_kimi_k2_6_moonshot_tsuge10_validation/results/md_moonshotai_kimi-k2.6_20260422_192742.json --expected-size full --skip-pricing-check
consistency: confirm unified JSON exists, counts match 530/410/120, and observed model ids are all moonshotai/kimi-k2.6
notes: thinking=enabled was used against the native Moonshot endpoint; parser normalization strips markdown fences before json.loads
-->
