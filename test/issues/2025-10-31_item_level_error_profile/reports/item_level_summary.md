# Item-level Error Profile (GPT-5 Markdown checkpoints)

Aggregated false-negative and false-positive patterns were recalculated for the benchmark GPT-5 markdown runs on the Suda (format comparison) and Tsuge (validation) cohorts. Suda totals cover 530 comparable checklist decisions (53 items × 10 papers); Tsuge totals cover the same 530-item denominator. The analysis surfaces persistent blind spots in risk-of-bias reporting and synthesis planning while highlighting where abstract-only expectations inflate false positives.

Suda FN pressure concentrates on Item 19 (62.5% FN over eight human positives) and Item 13a (55.6% FN over nine positives), indicating ongoing gaps in spotting bias assessment discussion and synthesis eligibility procedures. FN rates also remain elevated for Items 8, 13d, and 5 (33–38%), each tied to incomplete capture of information sources or data collection workflows. Tsuge mirrors this pattern with Item 19 at 87.5% FN and Item 13a at 70% FN, demonstrating that the failure to credit risk-of-bias statement and synthesis assignment persists across domains; Item 20a (25% FN) suggests nuance in effect measure reporting is still frequently missed.

False positives are dominated by abstract checklists. In both datasets Item A6 (70–75% FP) and Item A7 (70% FP in Tsuge) show that models over-interpret brief abstract mentions of meta-analysis as sufficient reporting. Item A3 (10% FP in Suda; 20% in Tsuge) and Item A9 (33% FP in Suda, 0–20% elsewhere) reinforce that concise outcome listings or general guidance statements are being misclassified as full adherence. For the main checklist, Suda Item 13b (37.5% FP) and Tsuge Item 13c (50% FP) confirm that sensitivity analyses and result syntheses remain over-called when only partial descriptions are present.

A cross-dataset overlap underscores the most fragile areas: Items 13a and 19 jointly drive false negatives, while the abstract Items A3 and A6 are recurrent false-positive hotspots. These will anchor the next iteration of prompt adjustments and targeted few-shot exemplars. The refreshed outputs replace the prior placeholder snippet and unblock manuscript updates that require concrete item-level figures.

<!--
canonical: test/issues/2025-09-27_suda_multi_format_scaling/results/20250928_114923_gpt5_md_reasoning_high.json; test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gpt-5_20251023_184404.json
finalized: test/issues/2025-10-31_item_level_error_profile/reports/
regen: PYTHONPATH=. venv/bin/python analysis/item_level_error_profile.py --dataset Suda=test/issues/2025-09-27_suda_multi_format_scaling/results/20250928_114923_gpt5_md_reasoning_high.json --dataset Tsuge=test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gpt-5_20251023_184404.json --output-dir test/issues/2025-10-31_item_level_error_profile/reports
consistency: Confirm fnfp_item_support.json total_comparable sums to 530 for both datasets and reconcile Item IDs against prisma_evaluator/resources/formats/PRISMA_2020_checklist.json and ..._abstract_checklist.json
notes: Abstract FP inflation (A6/A7) warrants checklist-specific prompt cues; retain `.env` secrets untouched.
-->
