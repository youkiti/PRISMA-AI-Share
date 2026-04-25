#!/usr/bin/env bash
# Shared bootstrap for DeepSeek V4 Pro Tsuge validation runs.
# Mirrors test/issues/2025-10-23_tsuge_md_validation_metrics/scripts/run_md_all_models.sh
# so that the data path / annotation path / dataset toggles match prior validation runs.

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

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "OPENROUTER_API_KEY is not set" >&2
  exit 1
fi

if [[ -z "${PRISMA_AI_DRIVE_PATH:-}" || "${PRISMA_AI_DRIVE_PATH}" == "/path/to/data/directory" ]]; then
  export PRISMA_AI_DRIVE_PATH="${PROJECT_ROOT}"
  echo "[info] PRISMA_AI_DRIVE_PATH auto-set to project root: ${PRISMA_AI_DRIVE_PATH}"
fi

export ANNOTATION_DATA_PATH="${PROJECT_ROOT}/supplement/data"
export STRUCTURED_DATA_SUBDIRS_OVERRIDE="supplement/data/tsuge2025/structured_prisma"
export ENABLE_SUDA=false
export ENABLE_TSUGE_PRISMA=true
export ENABLE_TSUGE_OTHER=false
export PRISMA_EVALUATOR_MAX_WORKERS=1

LOG_DIR="${ISSUE_DIR}/logs"
RESULT_DEST="${ISSUE_DIR}/results"
RESULT_SOURCE="${PROJECT_ROOT}/results/evaluator_output"
mkdir -p "${LOG_DIR}" "${RESULT_DEST}"

SELECTED_FILE="${ISSUE_DIR}/data/tsuge_selected10.txt"
PAPERS_ALL=$(grep -v '^#' "${SELECTED_FILE}" | tr '\n' ',' | sed 's/,$//')

MODEL_ID="${MODEL_ID:-deepseek/deepseek-v4-pro}"
SAFE_MODEL="${MODEL_ID//\//_}"
