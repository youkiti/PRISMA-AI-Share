# 2026-04-16 Qwen JSON Validity Rebuttal

This issue records the rebuttal-focused validation experiment for Reviewer 1 Comment 3. The goal is to quantify how often the Qwen model returns a directly parseable structured response under the repository's actual implementation path: OpenRouter function calling, not the native Qwen API.

The experiment fixes the model, prompt settings, dataset, and target paper, then repeats the same single-paper evaluation 100 times. The primary endpoint is the first-pass parseability rate for the main-text PRISMA checklist evaluation. Secondary endpoints are JSON decode errors observed in the OpenRouter evaluator logs, recovery after item-level retry, and residual final failures after all retry attempts.

## Fixed Conditions
The runs use `qwen/qwen3-235b-a22b-2507` through the standard OpenRouter evaluator path with `--schema-type simple --checklist-format md --dataset suda --paper-ids Suda2025_15`. The target paper is intentionally fixed so that the measured variability reflects response-format stability rather than paper-to-paper variation.

## Endpoints
The primary endpoint is the proportion of runs whose main evaluation logs contain `Initial evaluation: 42 success, 0 failed`, which indicates that the initial tool-call payload was fully parsed and validated before item-level retry. Secondary endpoints are the proportion of runs with a main-evaluation `JSON decode error`, the proportion of runs that required retry-based recovery, and the proportion of runs with any final `Failed after ... retry attempts` items in the main evaluation output.

## Artifacts
The raw unified JSON outputs are copied to `results/raw/`. Per-run console and evaluator logs are stored in `logs/`. Aggregated summaries are written to `reports/summary.json` and `reports/summary.md`. Reproducibility helper files, if needed later, should be added under `data/`.

## Execution
Run the wrapper script below from the repository root.

```bash
bash test/issues/2026-04-16_qwen_json_validity_rebuttal/scripts/run_qwen_json_validity.sh
```

After the 100 runs complete, aggregate the results with:

```bash
PYTHONPATH=. venv/bin/python \
  test/issues/2026-04-16_qwen_json_validity_rebuttal/scripts/summarize_qwen_json_validity.py
```

## Notes
This issue is for rebuttal evidence only. It does not imply any manuscript body update. The response should describe the actual implementation as OpenRouter-based function calling and cite OpenRouter documentation accordingly.

<!--
canonical: test/issues/2026-04-16_qwen_json_validity_rebuttal/
finalized: test/issues/2026-04-16_qwen_json_validity_rebuttal/
regen: bash test/issues/2026-04-16_qwen_json_validity_rebuttal/scripts/run_qwen_json_validity.sh && PYTHONPATH=. venv/bin/python test/issues/2026-04-16_qwen_json_validity_rebuttal/scripts/summarize_qwen_json_validity.py
consistency: verify that logs/, results/raw/, and reports/summary.{json,md} agree on run count; if any drift is found, regenerate summaries from raw logs and JSON outputs
notes: Do not edit .env. This experiment depends on OpenRouter credentials already configured in the environment.
-->
