#!/usr/bin/env bash
set -euo pipefail

# Simple A/B run + post-hoc ensemble helper
# Requirements: .venv ready, APIキー設定済み、analysis/ensemble_ab.py あり

MODEL=${MODEL:-"claude-opus-4-1-20250805"}
PAPERS=${PAPERS:-"Suda2025_15,Suda2025_17,Suda2025_18,Suda2025_5,Suda2025_7"}
RESULTS_DIR="results/evaluator_output"

latest_unified() {
  ls -t ${RESULTS_DIR}/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_[0-9][0-9][0-9][0-9][0-9][0-9].json 2>/dev/null | head -n1 || true
}

echo "[A] paper-first (simple)"
.venv/bin/python -m prisma_evaluator.cli.main run \
  -m "${MODEL}" --use-claude-native \
  -d suda --paper-ids "${PAPERS}" \
  -st simple --order-mode paper-first --log-level INFO
A_JSON=$(latest_unified)
echo "A_JSON=${A_JSON}"

sleep 1

echo "[B] eande-first (simple)"
.venv/bin/python -m prisma_evaluator.cli.main run \
  -m "${MODEL}" --use-claude-native \
  -d suda --paper-ids "${PAPERS}" \
  -st simple --order-mode eande-first --log-level INFO
B_JSON=$(latest_unified)
echo "B_JSON=${B_JSON}"

if [[ -z "${A_JSON}" || -z "${B_JSON}" ]]; then
  echo "Unified outputs not found. Check runs/logs." >&2
  exit 1
fi

echo "[Ensemble] intersection"
.venv/bin/python analysis/ensemble_ab.py --a "${A_JSON}" --b "${B_JSON}" --policy intersection

echo "[Ensemble] union"
.venv/bin/python analysis/ensemble_ab.py --a "${A_JSON}" --b "${B_JSON}" --policy union

echo "[Ensemble] targeted-union"
.venv/bin/python analysis/ensemble_ab.py --a "${A_JSON}" --b "${B_JSON}" --policy targeted-union

echo "Done. See ${RESULTS_DIR} for outputs."

