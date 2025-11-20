## GPT-5.1 reasoning-none Tsuge10 Markdown metrics (95% CIs)
Evaluating the 10-paper Tsuge PRISMA subset yielded 530 comparable checklist decisions (297 positive, 233 negative ground-truth labels). Overall accuracy was 78.30% (415/530, 95% Wilson CI 74.60–81.60%). Sensitivity reached 84.51% (251/297, CI 79.96–88.18%) and specificity 70.39% (164/233, CI 64.23–75.88%). Precision was 78.44% (251/320, CI 73.61–82.59%). Main-section items (410 decisions) achieved 77.56% accuracy with balanced error rates (TP 208, TN 110), whereas abstract-only items (120 decisions) retained 100% sensitivity but 70.13% specificity due to 23 false positives.
Relative to earlier Tsuge md validations (2025-10-23, reasoning minimal), the reasoning-none configuration maintained comparable sensitivity but introduced slightly more false negatives (+46 vs. +38), underscoring that the fast inference mode should be cited as the lower-bound comparator when discussing GPT-5.x checklist behaviour.

<!--
canonical: test/issues/2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval/results/md_gpt5_1_tsuge10_20251119_072534.json
finalized: test/issues/2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval/reports/
regen: python3 analysis/scripts/summarize_metrics.py --input test/issues/2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval/results/md_gpt5_1_tsuge10_20251119_072534.json --out reports/md_gpt5_1_tsuge10_summary.md
consistency: Recompute counts and Wilson intervals; cross-check against 2025-10-23_tsuge_md_validation_metrics
notes: Totals exclude non-comparable checklist entries; confidence intervals calculated via Wilson method (z=1.96).
-->
