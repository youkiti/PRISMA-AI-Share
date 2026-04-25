#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <run_timestamp: YYYYMMDD_HHMMSS>" >&2
  exit 1
fi

RUN_TIMESTAMP="$1"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
ISSUE_DIR="$ROOT_DIR/test/issues/2026-04-22_kimi_k2_6_moonshot_tsuge10_validation"
RESULTS_DIR="$ISSUE_DIR/results"

mkdir -p "$RESULTS_DIR"

if [[ ! -x "$ROOT_DIR/venv/bin/python" ]]; then
  echo "Missing Python interpreter: $ROOT_DIR/venv/bin/python" >&2
  exit 1
fi

cd "$ROOT_DIR"

for prefix in ai_evaluations accuracy_summary comparison_details; do
  src="results/evaluator_output/${prefix}_moonshotai_kimi-k2.6_md_${RUN_TIMESTAMP}.json"
  if [[ ! -f "$src" ]]; then
    echo "Missing raw output: $src" >&2
    exit 1
  fi
  cp "$src" "$RESULTS_DIR/"
done

PYTHONPATH=. "$ROOT_DIR/venv/bin/python" \
  test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/build_unified_validation_json.py \
  --model-id moonshotai/kimi-k2.6 \
  --format-type md \
  --run-timestamp "$RUN_TIMESTAMP" \
  --source-dir results/evaluator_output \
  --output-dir "$RESULTS_DIR"

PYTHONPATH=. "$ROOT_DIR/venv/bin/python" \
  test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/check_validation_counts.py \
  "$RESULTS_DIR/md_moonshotai_kimi-k2.6_${RUN_TIMESTAMP}.json" \
  --expected-size full \
  --skip-pricing-check
