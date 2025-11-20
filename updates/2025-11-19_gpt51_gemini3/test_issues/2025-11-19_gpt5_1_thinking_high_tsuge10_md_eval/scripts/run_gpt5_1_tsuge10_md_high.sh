#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ISSUE_DIR=$(cd "${SCRIPT_DIR}/.." && pwd)
PROJECT_ROOT=$(cd "${ISSUE_DIR}/../../.." && pwd)

PYTHON_BIN="${PROJECT_ROOT}/venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  echo "python executable not found: ${PYTHON_BIN}" >&2
  exit 1
fi

if [[ -f "${PROJECT_ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${PROJECT_ROOT}/.env"
  set +a
fi

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "OPENAI_API_KEY is not set" >&2
  exit 1
fi

if [[ -z "${PRISMA_AI_DRIVE_PATH:-}" || "${PRISMA_AI_DRIVE_PATH}" == "/path/to/data/directory" ]]; then
  export PRISMA_AI_DRIVE_PATH="${PROJECT_ROOT}"
  echo "[info] PRISMA_AI_DRIVE_PATH auto-set to ${PRISMA_AI_DRIVE_PATH}"
else
  echo "[info] PRISMA_AI_DRIVE_PATH=${PRISMA_AI_DRIVE_PATH}"
fi

if [[ -z "${ANNOTATION_DATA_PATH:-}" || ! -d "${ANNOTATION_DATA_PATH}" ]]; then
  export ANNOTATION_DATA_PATH="${PROJECT_ROOT}/supplement/data"
fi

echo "[info] ANNOTATION_DATA_PATH=${ANNOTATION_DATA_PATH}"

SELECTED_FILE="${ISSUE_DIR}/data/tsuge_selected_papers.txt"
if [[ ! -f "${SELECTED_FILE}" ]]; then
  echo "selected paper list not found: ${SELECTED_FILE}" >&2
  exit 1
fi

PAPERS=$(grep -v '^#' "${SELECTED_FILE}" | tr '\n' ',' | sed 's/,$//')
if [[ -z "${PAPERS}" ]]; then
  echo "paper id list is empty" >&2
  exit 1
fi

RESULT_SOURCE="${PROJECT_ROOT}/results/evaluator_output"
RESULT_DEST="${ISSUE_DIR}/results"
LOG_DIR="${ISSUE_DIR}/logs"
mkdir -p "${RESULT_DEST}" "${LOG_DIR}"

STAMP=$(date +%Y%m%d_%H%M%S)
RUN_LABEL="md_gpt5_1_tsuge10_high_${STAMP}"
RUN_LOG="${LOG_DIR}/${RUN_LABEL}.log"

BEFORE_SNAPSHOT=$(mktemp)
AFTER_SNAPSHOT=$(mktemp)
ls -1 "${RESULT_SOURCE}" 2>/dev/null | sort > "${BEFORE_SNAPSHOT}"

export STRUCTURED_DATA_SUBDIRS_OVERRIDE="supplement/data/tsuge2025/structured_prisma"
export ENABLE_SUDA=false
export ENABLE_TSUGE_PRISMA=true
export ENABLE_TSUGE_OTHER=false
export PRISMA_EVALUATOR_MAX_WORKERS=${PRISMA_EVALUATOR_MAX_WORKERS:-1}
export GPT5_REASONING_EFFORT=high

echo "[info] start Tsuge md × GPT-5.1 high-reasoning run (${RUN_LABEL})" | tee "${RUN_LOG}"
PYTHONPATH="${PROJECT_ROOT}" \
  "${PYTHON_BIN}" -m prisma_evaluator.cli.main run \
  --dataset tsuge-prisma \
  --paper-ids "${PAPERS}" \
  --checklist-format md \
  --model gpt-5.1 \
  --format "${RUN_LABEL}" \
  --log-level INFO \
  2>&1 | tee -a "${RUN_LOG}"

ls -1 "${RESULT_SOURCE}" 2>/dev/null | sort > "${AFTER_SNAPSHOT}"
mapfile -t NEW_FILES < <(comm -13 "${BEFORE_SNAPSHOT}" "${AFTER_SNAPSHOT}")

rm -f "${BEFORE_SNAPSHOT}" "${AFTER_SNAPSHOT}"

if [[ ${#NEW_FILES[@]} -eq 0 ]]; then
  echo "[warn] no new evaluator_output files were produced" | tee -a "${RUN_LOG}"
  exit 0
fi

LATEST_FILE="${NEW_FILES[-1]}"
cp "${RESULT_SOURCE}/${LATEST_FILE}" "${RESULT_DEST}/${RUN_LABEL}.json"
echo "[info] copied ${LATEST_FILE} -> ${RESULT_DEST}/${RUN_LABEL}.json" | tee -a "${RUN_LOG}"
