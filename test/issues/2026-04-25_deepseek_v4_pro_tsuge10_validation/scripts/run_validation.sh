#!/usr/bin/env bash
# Full Tsuge 10-paper validation for DeepSeek V4 Pro.
# Reuses the canonical runner at
#   test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_validation_model.py
# (which calls run_evaluation_pipeline directly so order_mode / section_mode
# can still be set even though those flags were removed from the public CLI),
# then moves all artifacts produced by that runner into this issue's results/.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ISSUE_DIR=$(cd "${SCRIPT_DIR}/.." && pwd)
PROJECT_ROOT=$(cd "${ISSUE_DIR}/../../.." && pwd)

CANONICAL_RUNNER="${PROJECT_ROOT}/test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_validation_model.py"
CANONICAL_RESULTS="${PROJECT_ROOT}/test/issues/2026-04-16_tsuge10_md_new_models_validation/results"

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
fi
export ANNOTATION_DATA_PATH="${ANNOTATION_DATA_PATH:-${PROJECT_ROOT}/supplement/data}"
export STRUCTURED_DATA_SUBDIRS_OVERRIDE="supplement/data/tsuge2025/structured_prisma"
export ENABLE_SUDA=false
export ENABLE_TSUGE_PRISMA=true
export ENABLE_TSUGE_OTHER=false
export MAX_CONCURRENT_PAPERS=1

LOG_DIR="${ISSUE_DIR}/logs"
RESULT_DEST="${ISSUE_DIR}/results"
mkdir -p "${LOG_DIR}" "${RESULT_DEST}"

MODEL_ID="${MODEL_ID:-deepseek/deepseek-v4-pro}"
SAFE_MODEL="${MODEL_ID//\//_}"
PAPERS_FILE="${ISSUE_DIR}/data/tsuge_selected10.txt"
STAMP=$(date +%Y%m%d_%H%M%S)
RUN_LABEL="md_${SAFE_MODEL}_${STAMP}"
RUN_LOG="${LOG_DIR}/${RUN_LABEL}.log"

cat <<HDR | tee "${RUN_LOG}"
[info] DeepSeek V4 Pro Tsuge 10-paper validation
  model        : ${MODEL_ID}
  papers_file  : ${PAPERS_FILE}
  run_label    : ${RUN_LABEL}
  result_dest  : ${RESULT_DEST}
  canonical    : ${CANONICAL_RUNNER}
HDR

# Snapshot canonical results dir BEFORE the run so we only move newly-created files.
BEFORE_FILE=$(mktemp)
ls -1 "${CANONICAL_RESULTS}" 2>/dev/null | sort > "${BEFORE_FILE}"

PYTHONPATH="${PROJECT_ROOT}" \
  "${PYTHON_BIN}" "${CANONICAL_RUNNER}" \
    --model-id "${MODEL_ID}" \
    --paper-ids-file "${PAPERS_FILE}" \
    --schema-type simple \
    --checklist-format md \
    --order-mode eande-first \
    --section-mode off \
    --run-label "${RUN_LABEL}" \
    --expected-size full \
    --log-level INFO \
    >> "${RUN_LOG}" 2>&1 || {
      echo "[warn] validation run exited non-zero; see ${RUN_LOG}" | tee -a "${RUN_LOG}"
      rm -f "${BEFORE_FILE}"
      exit 1
    }

AFTER_FILE=$(mktemp)
ls -1 "${CANONICAL_RESULTS}" 2>/dev/null | sort > "${AFTER_FILE}"
mapfile -t NEW_FILES < <(comm -13 "${BEFORE_FILE}" "${AFTER_FILE}")
rm -f "${BEFORE_FILE}" "${AFTER_FILE}"

moved=0
for fname in "${NEW_FILES[@]}"; do
  if [[ "${fname}" != *.json ]]; then continue; fi
  if [[ "${fname}" != *"${SAFE_MODEL}"* ]]; then continue; fi
  mv "${CANONICAL_RESULTS}/${fname}" "${RESULT_DEST}/"
  echo "[info] moved ${fname} -> ${RESULT_DEST}/" | tee -a "${RUN_LOG}"
  moved=$((moved + 1))
done

if [[ "${moved}" -eq 0 ]]; then
  echo "[warn] no DeepSeek V4 Pro artifacts moved; check ${CANONICAL_RESULTS} and ${RUN_LOG}" | tee -a "${RUN_LOG}"
  exit 2
fi

echo "[info] validation complete (${moved} files moved)" | tee -a "${RUN_LOG}"
ls -1 "${RESULT_DEST}" | tee -a "${RUN_LOG}"
