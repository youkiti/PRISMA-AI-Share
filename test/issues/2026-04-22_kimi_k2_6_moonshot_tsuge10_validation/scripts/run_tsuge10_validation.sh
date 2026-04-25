#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
ISSUE_DIR="$ROOT_DIR/test/issues/2026-04-22_kimi_k2_6_moonshot_tsuge10_validation"
PAPER_LIST_FILE="$ISSUE_DIR/data/tsuge_selected10.txt"
LOG_DIR="$ISSUE_DIR/logs"

mkdir -p "$LOG_DIR"

if [[ ! -f "$PAPER_LIST_FILE" ]]; then
  echo "Missing paper list: $PAPER_LIST_FILE" >&2
  exit 1
fi

if [[ ! -x "$ROOT_DIR/venv/bin/python" ]]; then
  echo "Missing Python interpreter: $ROOT_DIR/venv/bin/python" >&2
  exit 1
fi

PAPERS="$(grep -v '^#' "$PAPER_LIST_FILE" | sed '/^$/d' | paste -sd, -)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/tsuge10_validation_${TIMESTAMP}.log"

echo "Running Moonshot direct Tsuge10 validation"
echo "papers=$PAPERS"
echo "log=$LOG_FILE"

cd "$ROOT_DIR"
MAX_CONCURRENT_PAPERS=1 PYTHONPATH=. \
  "$ROOT_DIR/venv/bin/python" -m prisma_evaluator.cli.main run \
  --model moonshotai/kimi-k2.6 \
  --dataset tsuge-prisma \
  --paper-ids "$PAPERS" \
  --schema-type simple \
  --checklist-format md \
  --kimi-thinking enabled \
  --log-level INFO \
  2>&1 | tee "$LOG_FILE"
