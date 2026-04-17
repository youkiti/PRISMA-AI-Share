#!/usr/bin/env bash
# Serial sweep of Claude Opus 4.7 across 5 effort levels on the
# 10-paper Tsuge PRISMA MD validation cohort.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
ISSUE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MODEL_ID="claude-opus-4-7"
PAPER_FILE="$ISSUE_DIR/data/tsuge_selected10.txt"
LOG_DIR="$ISSUE_DIR/logs"
mkdir -p "$LOG_DIR"

EFFORTS=("low" "medium" "high" "xhigh" "max")

for EFFORT in "${EFFORTS[@]}"; do
  TS="$(date +%Y%m%d_%H%M%S)"
  LOG_FILE="$LOG_DIR/run_${EFFORT}_${TS}.log"
  echo "[$(date)] ====== effort=${EFFORT} start ======" | tee -a "$LOG_FILE"
  PYTHONPATH=. venv/bin/python \
    "$ISSUE_DIR/scripts/run_validation_model.py" \
    --model-id "$MODEL_ID" \
    --paper-ids-file "$PAPER_FILE" \
    --schema-type simple \
    --checklist-format md \
    --order-mode eande-first \
    --section-mode off \
    --claude-effort "$EFFORT" \
    --expected-size full \
    --log-level INFO \
    2>&1 | tee -a "$LOG_FILE"
  echo "[$(date)] ====== effort=${EFFORT} done ======" | tee -a "$LOG_FILE"
done

echo "all done"
