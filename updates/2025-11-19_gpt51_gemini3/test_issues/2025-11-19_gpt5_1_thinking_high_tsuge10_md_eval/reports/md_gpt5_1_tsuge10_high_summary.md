## GPT-5.1 reasoning-high Tsuge10 Markdown metrics (95% CIs)
High reasoning effort increased overall accuracy to 80.19% (425/530, 95% Wilson CI 76.58–83.36%), sensitivity to 87.21% (259/297, CI 82.93–90.53%), and specificity to 71.24% (166/233, CI 65.13–76.67%). Precision also rose to 79.45% (259/326, CI 74.73–83.48%). Main-section accuracy improved to 80.73% (331/410) while abstract sensitivity remained saturated at 100% but specificity dipped slightly to 66.23% because of 26 false positives.
Compared with the reasoning-none baseline (accuracy 78.30%, sensitivity 84.51%, specificity 70.39%), the high-effort run delivered +1.89 pp accuracy and +3.10 pp sensitivity while trimming false negatives from 46 to 38. Specificity gains were modest (+0.85 pp) because high reasoning also generated two extra false positives. Confidence-interval overlap indicates the improvements are directional but not yet statistically definitive; nevertheless, the larger reasoning budget demonstrably reduced misses on the positive class at the cost of an ~6.4× runtime increase (8 min 37 s vs. 83 s).

<!--
canonical: test/issues/2025-11-19_gpt5_1_thinking_high_tsuge10_md_eval/results/md_gpt5_1_tsuge10_high_20251119_073254.json
finalized: test/issues/2025-11-19_gpt5_1_thinking_high_tsuge10_md_eval/reports/
regen: python3 analysis/scripts/summarize_metrics.py --input test/issues/2025-11-19_gpt5_1_thinking_high_tsuge10_md_eval/results/md_gpt5_1_tsuge10_high_20251119_073254.json --compare test/issues/2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval/results/md_gpt5_1_tsuge10_20251119_072534.json --out reports/md_gpt5_1_tsuge10_high_summary.md
consistency: Validate Wilson intervals against manual recomputation; ensure deltas align with reasoning-none summary
notes: Totals exclude non-comparable items; deltas quoted in percentage points relative to the reasoning-none baseline.
-->
