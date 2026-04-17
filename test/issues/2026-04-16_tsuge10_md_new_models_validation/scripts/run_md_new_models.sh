#!/usr/bin/env bash
set -euo pipefail

# Serial driver that runs the 5 new-generation LLMs through the issue-local
# runner (scripts/run_validation_model.py).  Each model writes raw evaluator
# outputs to results/evaluator_output, then the runner copies them into this
# issue's results/ directory and emits md_<slug>_<ts>.json.
#
# Usage:
#   bash test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_md_new_models.sh [--smoke]
#
# --smoke  : run on a single paper (Tsuge2025_PRISMA2020_120) for pre-flight check.

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ISSUE_DIR=$(cd "${SCRIPT_DIR}/.." && pwd)
PROJECT_ROOT=$(cd "${ISSUE_DIR}/../../.." && pwd)

MODE="full"
if [[ "${1:-}" == "--smoke" ]]; then
  MODE="smoke"
fi

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

REQUIRED_KEYS=(OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY OPENROUTER_API_KEY)
for key in "${REQUIRED_KEYS[@]}"; do
  if [[ -z "${!key:-}" ]]; then
    echo "${key} が設定されていません" >&2
    exit 1
  fi
done

if [[ -z "${PRISMA_AI_DRIVE_PATH:-}" || "${PRISMA_AI_DRIVE_PATH}" == "/path/to/data/directory" ]]; then
  export PRISMA_AI_DRIVE_PATH="${PROJECT_ROOT}"
  echo "[info] PRISMA_AI_DRIVE_PATH auto-set to project root: ${PRISMA_AI_DRIVE_PATH}"
fi
export ANNOTATION_DATA_PATH="${ANNOTATION_DATA_PATH:-${PROJECT_ROOT}/supplement/data}"
export STRUCTURED_DATA_SUBDIRS_OVERRIDE="supplement/data/tsuge2025/structured_prisma"
export ENABLE_SUDA=false
export ENABLE_TSUGE_PRISMA=true
export ENABLE_TSUGE_OTHER=false
export MAX_CONCURRENT_PAPERS=1

PAPERS_FILE="${ISSUE_DIR}/data/tsuge_selected10.txt"
if [[ ! -f "${PAPERS_FILE}" ]]; then
  echo "paper ID list not found: ${PAPERS_FILE}" >&2
  exit 1
fi

LOG_DIR="${ISSUE_DIR}/logs"
mkdir -p "${LOG_DIR}" "${ISSUE_DIR}/results"
STAMP=$(date +%Y%m%d_%H%M%S)
SESSION_LOG="${LOG_DIR}/session_${MODE}_${STAMP}.log"

RUNNER="${SCRIPT_DIR}/run_validation_model.py"

# Model specs: label | model-id | extra-args-space-separated
MODELS=(
  "claude-opus-4-6|claude-opus-4-6|"
  "gpt-5.4|gpt-5.4|--gpt5-reasoning none"
  "gemini-3.1-pro-preview|gemini-3.1-pro-preview|--gemini-model gemini-3.1-pro-preview --gemini-thinking-level high --gemini-temperature 1.0"
  "x-ai/grok-4.20|x-ai/grok-4.20|"
  "qwen/qwen3.6-plus|qwen/qwen3.6-plus|"
)

SMOKE_PAPER_IDS="Tsuge2025_PRISMA2020_120"

run_one() {
  local label="$1"
  local model_id="$2"
  local extra="$3"
  local run_label="md_${label//\//_}_${STAMP}"
  local run_log="${LOG_DIR}/${run_label}.log"

  echo "[info] model=${model_id} label=${label} mode=${MODE}" | tee -a "${SESSION_LOG}" "${run_log}"

  local cmd=(
    PYTHONPATH="${PROJECT_ROOT}"
    "${PYTHON_BIN}" "${RUNNER}"
    --model-id "${model_id}"
    --run-label "${run_label}"
  )
  if [[ "${MODE}" == "smoke" ]]; then
    cmd+=(--paper-ids "${SMOKE_PAPER_IDS}" --expected-size smoke)
  else
    cmd+=(--paper-ids-file "${PAPERS_FILE}" --expected-size full)
  fi
  # shellcheck disable=SC2206
  if [[ -n "${extra}" ]]; then
    local extra_args=(${extra})
    cmd+=("${extra_args[@]}")
  fi

  echo "[cmd] ${cmd[*]}" | tee -a "${SESSION_LOG}" "${run_log}"
  if ! env "${cmd[@]}" >> "${run_log}" 2>&1; then
    echo "[warn] run failed for model=${model_id}; see ${run_log}" | tee -a "${SESSION_LOG}"
    return 1
  fi
  echo "[info] run OK for model=${model_id}" | tee -a "${SESSION_LOG}"
  return 0
}

FAILED_MODELS=()
for spec in "${MODELS[@]}"; do
  label="${spec%%|*}"
  rest="${spec#*|}"
  model_id="${rest%%|*}"
  extra="${rest#*|}"
  if ! run_one "${label}" "${model_id}" "${extra}"; then
    FAILED_MODELS+=("${label}")
  fi
done

echo "[info] session=${SESSION_LOG}"
if [[ ${#FAILED_MODELS[@]} -gt 0 ]]; then
  echo "[warn] failed models: ${FAILED_MODELS[*]}"
  exit 2
fi
echo "[info] all models completed"
