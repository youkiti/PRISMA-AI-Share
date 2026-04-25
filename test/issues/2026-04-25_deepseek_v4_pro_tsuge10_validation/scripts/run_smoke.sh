#!/usr/bin/env bash
# Single-paper smoke test for DeepSeek V4 Pro on Tsuge cohort.
# Reuses the canonical runner at
#   test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_validation_model.py
# (which calls run_evaluation_pipeline() directly so order_mode / section_mode
# can still be set even though those flags were removed from the public CLI),
# then moves the resulting unified JSON + raw trio into this issue's results/.

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
SMOKE_PAPER="${SMOKE_PAPER:-Tsuge2025_PRISMA2020_14}"
STAMP=$(date +%Y%m%d_%H%M%S)
RUN_LABEL="md_${SAFE_MODEL}_smoke_${STAMP}"
RUN_LOG="${LOG_DIR}/${RUN_LABEL}.log"

cat <<HDR | tee "${RUN_LOG}"
[info] DeepSeek V4 Pro smoke test (1 paper)
  model        : ${MODEL_ID}
  paper        : ${SMOKE_PAPER}
  run_label    : ${RUN_LABEL}
  result_dest  : ${RESULT_DEST}
  canonical    : ${CANONICAL_RUNNER}
HDR

PYTHONPATH="${PROJECT_ROOT}" \
  "${PYTHON_BIN}" "${CANONICAL_RUNNER}" \
    --model-id "${MODEL_ID}" \
    --paper-ids "${SMOKE_PAPER}" \
    --schema-type simple \
    --checklist-format md \
    --order-mode eande-first \
    --section-mode off \
    --run-label "${RUN_LABEL}" \
    --expected-size smoke \
    --log-level INFO \
    >> "${RUN_LOG}" 2>&1 || {
      echo "[warn] smoke test exited non-zero; see ${RUN_LOG}" | tee -a "${RUN_LOG}"
      exit 1
    }

# Move artifacts produced by the canonical runner (which writes to its own
# results/ folder) into this issue's results/.
shopt -s nullglob
moved=0
for src in "${CANONICAL_RESULTS}"/*"${SAFE_MODEL}"*"${STAMP}"*; do
  if [[ -f "${src}" ]]; then
    mv "${src}" "${RESULT_DEST}/"
    echo "[info] moved $(basename "${src}") -> ${RESULT_DEST}/" | tee -a "${RUN_LOG}"
    moved=1
  fi
done
if [[ "${moved}" -eq 0 ]]; then
  # The build_unified_validation_json step uses the timestamp from the raw
  # ai_evaluations file rather than ${STAMP}, so fall back to a glob that
  # matches the safe-model token only.
  for src in "${CANONICAL_RESULTS}"/*"${SAFE_MODEL}"*; do
    if [[ -f "${src}" ]]; then
      mv "${src}" "${RESULT_DEST}/"
      echo "[info] moved $(basename "${src}") -> ${RESULT_DEST}/" | tee -a "${RUN_LOG}"
      moved=1
    fi
  done
fi
if [[ "${moved}" -eq 0 ]]; then
  echo "[warn] no artifacts matched safe_model=${SAFE_MODEL} under ${CANONICAL_RESULTS}" | tee -a "${RUN_LOG}"
  exit 2
fi

echo "[info] smoke test complete" | tee -a "${RUN_LOG}"
ls -1 "${RESULT_DEST}" | tee -a "${RUN_LOG}"
