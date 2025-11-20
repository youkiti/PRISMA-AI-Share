# 2025-11-18 — Gemini 3 Pro (Direct) Tsuge PRISMA 10-paper Markdown Evaluation

## Setup
We evaluated 10 Tsuge2025-PRISMA systematic reviews with the Google Gemini Direct evaluator using the new `google-genai` SDK and the pipeline-integrated `GeminiDirectEvaluator`. The run used the simple schema with Markdown checklist format to align with prior Tsuge md validation experiments.

- Dataset: Tsuge2025-PRISMA (10-paper random subset; seed 20250928)
- Paper IDs: Tsuge2025_PRISMA2020_14, 20, 22, 26, 68, 74, 76, 80, 89, 120
- Model route: Gemini Direct (`--model gemini-2.5-pro --gemini-model gemini-3-pro-preview`)
- Checklist format: Markdown (`--checklist-format md`)
- Section handling: full-text input (section-mode off via default SectionSplitter bypass)
- Execution: `ENABLE_GEMINI_DIRECT=true`, `PRISMA_AI_DRIVE_PATH=/home/prisma-ai-data`, `ANNOTATION_DATA_PATH=/home/prisma-ai-data/annotation`

The evaluation completed for all 10 main articles and 10 abstracts without item-level retry failures after refactoring `GeminiDirectEvaluator` to use `google-genai`’s `Client`, `Content`, `Part`, and `GenerateContentConfig` APIs.

<!--
canonical: results/evaluator_output/ai_evaluations_gemini-2.5-pro_md_20251119_070126.json; results/evaluator_output/accuracy_summary_gemini-2.5-pro_md_20251119_070126.json
finalized: test/issues/2025-11-18_gemini3_pro_suda_tsuge_md_eval/
regen: PRISMA_AI_DRIVE_PATH=/home/prisma-ai-data ANNOTATION_DATA_PATH=/home/prisma-ai-data/annotation ENABLE_SUDA=false ENABLE_TSUGE_PRISMA=true ENABLE_TSUGE_OTHER=false ENABLE_GEMINI_DIRECT=true PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run --model gemini-2.5-pro --gemini-model gemini-3-pro-preview --checklist-format md --paper-ids $(grep -v '^#' test/issues/2025-11-18_gemini3_pro_suda_tsuge_md_eval/data/tsuge_selected_papers.txt | paste -sd, -) --dataset tsuge-prisma --log-level INFO
consistency: Compare overall_metrics and abstract_metrics in accuracy_summary_gemini-2.5-pro_md_20251119_070126.json with manuscript Tsuge md baselines; verify that paper_ids in ai_evaluations_gemini-2.5-pro_md_20251119_070126.json match data/tsuge_selected_papers.txt
notes: Uses google-genai (from google import genai) rather than google-generativeai; thinking_level=high is mapped to ThinkingConfig(thinkingLevel=\"HIGH\") and checklist_format=\"md\" is passed through from the CLI.
-->

## Results
For the 10-paper Tsuge PRISMA subset, Gemini 3 Pro with Markdown checklists achieved stable performance on both main articles and abstracts.

At the overall level (main plus abstract items pooled), accuracy was 81.32% with sensitivity of 91.25% and specificity of 68.67%, corresponding to 431 correct decisions out of 530 comparable item-level judgements. The confusion matrix contained 271 true positives, 160 true negatives, 73 false positives, and 26 false negatives, yielding a Cohen’s kappa of 0.61 against human annotations; Wilson 95% confidence intervals were 77.78–84.41% for accuracy, 87.48–93.96% for sensitivity, and 62.45–74.28% for specificity.

For abstract-only items, accuracy was 82.50% with perfect recall of 100.00% and specificity of 72.73%, based on 99 correct decisions out of 120 comparable abstract items. The abstract confusion matrix comprised 43 true positives, 56 true negatives, 21 false positives, and no false negatives, with a Cohen’s kappa of 0.66; the corresponding Wilson 95% confidence intervals were 74.72–88.26% for accuracy, 91.80–100.00% for sensitivity, and 61.88–81.42% for specificity. In practice, this pattern indicates that Gemini 3 Pro tends to overcall some abstract items but rarely misses items that human annotators marked as reported.

These results place Gemini 3 Pro’s Markdown performance for Tsuge PRISMA 10 papers in the same accuracy band as previous high-performing models in the md condition, while providing a cleaner integration path via the new google-genai SDK for future real-data and checklist-format experiments.
