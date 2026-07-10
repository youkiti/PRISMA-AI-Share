#!/usr/bin/env bash
# Serial sweep of GPT-5.6 Sol across 2 reasoning-effort levels (none,
# low) on the 10-paper Tsuge PRISMA MD validation cohort.
# Verbosity is fixed to low (project-wide default already "low" in
# prisma_evaluator/config/default_settings.toml and
# environment-inherited GPT5_VERBOSITY, but we do not override here).
# reasoning_mode is intentionally NOT set (API default; parity with the
# GPT-5.5 sweep which predates the parameter).
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

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY not set" >&2
  exit 1
fi

MODEL_ID="gpt-5.6-sol"
PAPER_FILE="$ISSUE_DIR/data/tsuge_selected10.txt"
LOG_DIR="$ISSUE_DIR/logs"
mkdir -p "$LOG_DIR" "$ISSUE_DIR/results"

EFFORTS=("none" "low")

RUNNER="$ISSUE_DIR/scripts/run_validation_model.py"

run_one() {
  local effort="$1"
  local ts="$(date +%Y%m%d_%H%M%S)"
  local log_file="$LOG_DIR/run_${effort}_${ts}.log"
  echo "[$(date)] ====== effort=${effort} start (mode=${MODE}) ======" | tee -a "$log_file"

  local cmd=(
    PYTHONPATH=.
    venv/bin/python "$RUNNER"
    --model-id "$MODEL_ID"
    --schema-type simple
    --checklist-format md
    --order-mode eande-first
    --section-mode off
    --gpt5-reasoning "$effort"
    --log-level INFO
  )
  if [[ "$MODE" == "smoke" ]]; then
    cmd+=(--paper-ids "Tsuge2025_PRISMA2020_120" --expected-size smoke)
  else
    cmd+=(--paper-ids-file "$PAPER_FILE" --expected-size full)
  fi

  if ! env "${cmd[@]}" 2>&1 | tee -a "$log_file"; then
    echo "[$(date)] ====== effort=${effort} FAILED ======" | tee -a "$log_file"
    return 1
  fi
  echo "[$(date)] ====== effort=${effort} done ======" | tee -a "$log_file"
  return 0
}

FAILED=()
for effort in "${EFFORTS[@]}"; do
  if ! run_one "$effort"; then
    FAILED+=("$effort")
  fi
done

if [[ ${#FAILED[@]} -gt 0 ]]; then
  echo "[warn] failed efforts: ${FAILED[*]}"
  exit 2
fi

echo "all efforts done; aggregating..."
PYTHONPATH=. venv/bin/python "$ISSUE_DIR/scripts/aggregate_effort_sweep.py" \
  --model-id "$MODEL_ID"
