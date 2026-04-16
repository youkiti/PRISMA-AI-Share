#!/usr/bin/env bash
set -euo pipefail

ISSUE_DIR="test/issues/2026-04-16_qwen_json_validity_rebuttal"
SCRIPT="test/issues/2025-09-25_api_response_schema_alignment/scripts/test_single_paper_eval.py"
PYTHON_BIN="venv/bin/python"
MODEL_ID="${MODEL_ID:-qwen/qwen3-235b-a22b-2507}"
DATASET="${DATASET:-suda}"
PAPER_ID="${PAPER_ID:-Suda2025_15}"
RUNS="${RUNS:-100}"
SLEEP_SECONDS="${SLEEP_SECONDS:-2}"
CLI_EXTRA="${CLI_EXTRA:---schema-type simple --checklist-format md}"

RAW_RESULT_DIR="${ISSUE_DIR}/results/raw"
LOG_DIR="${ISSUE_DIR}/logs"
REPORT_DIR="${ISSUE_DIR}/reports"

mkdir -p "${RAW_RESULT_DIR}" "${LOG_DIR}" "${REPORT_DIR}"

if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "[ERROR] Missing Python executable: ${PYTHON_BIN}" >&2
  exit 1
fi

echo "[INFO] $(date --iso-8601=seconds) : Starting Qwen JSON validity experiment"
echo "[INFO] model=${MODEL_ID} dataset=${DATASET} paper=${PAPER_ID} runs=${RUNS}"

for i in $(seq 1 "${RUNS}"); do
  RUN_ID=$(printf "%03d" "${i}")
  LOG_FILE="${LOG_DIR}/run_${RUN_ID}.log"

  echo "[INFO] $(date --iso-8601=seconds) : Run ${RUN_ID}/${RUNS}" | tee "${LOG_FILE}"
  PYTHONPATH=. "${PYTHON_BIN}" "${SCRIPT}" \
    --model "${MODEL_ID}" \
    --dataset "${DATASET}" \
    --paper-id "${PAPER_ID}" \
    --result-dir "${RAW_RESULT_DIR}" \
    --cli-extra "${CLI_EXTRA}" \
    2>&1 | tee -a "${LOG_FILE}"

  LATEST_RESULT=$(ls -t "${RAW_RESULT_DIR}"/*.json 2>/dev/null | head -n 1 || true)
  if [[ -n "${LATEST_RESULT}" ]]; then
    RUN_RESULT="${RAW_RESULT_DIR}/run_${RUN_ID}_$(basename "${LATEST_RESULT}")"
    cp "${LATEST_RESULT}" "${RUN_RESULT}"
    echo "[INFO] $(date --iso-8601=seconds) : Copied ${LATEST_RESULT} -> ${RUN_RESULT}" | tee -a "${LOG_FILE}"
  else
    echo "[WARN] $(date --iso-8601=seconds) : No copied JSON found under ${RAW_RESULT_DIR}" | tee -a "${LOG_FILE}"
  fi

  if [[ "${i}" -lt "${RUNS}" ]]; then
    sleep "${SLEEP_SECONDS}"
  fi
done

echo "[INFO] $(date --iso-8601=seconds) : Completed ${RUNS} runs"
echo "[INFO] Next step: PYTHONPATH=. ${PYTHON_BIN} ${ISSUE_DIR}/scripts/summarize_qwen_json_validity.py"
