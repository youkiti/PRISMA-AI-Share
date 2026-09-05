#!/usr/bin/env bash
# Serial sweep of Gemini 3.8 Flash across 2 thinking levels (low, medium) on
# the 10-paper Tsuge PRISMA MD validation cohort.
# NOTE: gemini-3.8-flash supports thinking_level low/medium/high only
# ('minimal' returns a validation error). Temperature is pinned to 1.0 per
# Google's guidance for Gemini 3 (other values can cause loops/degradation).
# --model-id and --gemini-model are deliberately the same value so that the
# recorded model name matches the model actually called.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
ISSUE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODE="full"
if [[ "${1:-}" == "--smoke" ]]; then
  MODE="smoke"
fi

if [[ -f "$REPO_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$REPO_ROOT/.env"
  set +a
fi

if [[ -z "${GEMINI_API_KEY:-}" ]]; then
  echo "GEMINI_API_KEY not set" >&2
  exit 1
fi
export ENABLE_GEMINI_DIRECT=true

MODEL_ID="gemini-3.8-flash"
PAPER_FILE="$ISSUE_DIR/data/tsuge_selected10.txt"
LOG_DIR="$ISSUE_DIR/logs"
mkdir -p "$LOG_DIR" "$ISSUE_DIR/results"

LEVELS=("low" "medium")

RUNNER="$ISSUE_DIR/scripts/run_validation_model.py"

run_one() {
  local level="$1"
  local ts="$(date +%Y%m%d_%H%M%S)"
  local log_file="$LOG_DIR/run_${level}_${ts}.log"
  echo "[$(date)] ====== thinking_level=${level} start (mode=${MODE}) ======" | tee -a "$log_file"

  local cmd=(
    PYTHONPATH=.
    ENABLE_GEMINI_DIRECT=true
    venv/bin/python "$RUNNER"
    --model-id "$MODEL_ID"
    --gemini-model "$MODEL_ID"
    --gemini-thinking-level "$level"
    --gemini-temperature 1.0
    --schema-type simple
    --checklist-format md
    --order-mode eande-first
    --section-mode off
    --run-label "md_${MODEL_ID}_${level}_${ts}"
    --log-level INFO
  )
  if [[ "$MODE" == "smoke" ]]; then
    cmd+=(--paper-ids "Tsuge2025_PRISMA2020_120" --expected-size smoke)
  else
    cmd+=(--paper-ids-file "$PAPER_FILE" --expected-size full)
  fi

  if ! env "${cmd[@]}" 2>&1 | tee -a "$log_file"; then
    echo "[$(date)] ====== thinking_level=${level} FAILED ======" | tee -a "$log_file"
    return 1
  fi
  echo "[$(date)] ====== thinking_level=${level} done ======" | tee -a "$log_file"
  return 0
}

FAILED=()
for level in "${LEVELS[@]}"; do
  if ! run_one "$level"; then
    FAILED+=("$level")
  fi
done

if [[ ${#FAILED[@]} -gt 0 ]]; then
  echo "[warn] failed levels: ${FAILED[*]}"
  exit 2
fi

echo "all levels done; aggregating..."
PYTHONPATH=. venv/bin/python "$ISSUE_DIR/scripts/aggregate_level_sweep.py" \
  --model-id "$MODEL_ID"
