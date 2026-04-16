# Qwen JSON Validity Summary

Paper ID: `Suda2025_15`
Total runs: `100`

## Main Results

- Initial full success: `94/100` (94.0%)
- JSON decode errors: `1/100` (1.0%)
- Retry recovered: `6/100` (6.0%)
- Final failures after retry: `0/100` (0.0%)
- Wrapper validation succeeded: `100/100` (100.0%)


## Interpretation

The rebuttal-facing headline number is the initial full success rate, which measures how often the main checklist evaluation was fully parseable before any item-level retry. Retry recovered runs quantify cases where the first-pass structured output was unstable but the pipeline still salvaged the evaluation. Final failure runs quantify unresolved cases after all retries.

## Files

- JSON summary: `test/issues/2026-04-16_qwen_json_validity_rebuttal/reports/summary.json`
- Raw outputs: `test/issues/2026-04-16_qwen_json_validity_rebuttal/results/raw`
- Logs: `test/issues/2026-04-16_qwen_json_validity_rebuttal/logs`
