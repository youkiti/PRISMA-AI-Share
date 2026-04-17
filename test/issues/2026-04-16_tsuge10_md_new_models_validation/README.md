# 2026-04-16 Tsuge10 MD × New-Generation Models

Follow-up validation run that extends the 2025-10-23 cohort with five models
released in spring 2026:

| Provider  | Model ID                      | Evaluator route      |
|-----------|-------------------------------|----------------------|
| Anthropic | `claude-opus-4-6`             | Claude Native        |
| OpenAI    | `gpt-5.4`                     | GPT-5 Responses API  |
| Google    | `gemini-3.1-pro-preview`      | Gemini Direct        |
| xAI       | `x-ai/grok-4.20`              | OpenRouter           |
| Qwen      | `qwen/qwen3.6-plus`           | OpenRouter           |

Dataset: Tsuge2025-PRISMA 10 papers (same IDs as `2025-10-23_tsuge_md_validation_metrics`).
Checklist format: Markdown.
Schema: `simple`, `order-mode eande-first`, `section-mode off`.

See [PLAN.md](PLAN.md) for the full rationale, risks, and downstream reflection
steps into Figure 4 / Table 2 / CI.

## Layout

```
data/tsuge_selected10.txt                 # paper IDs (mirrored from 2025-10-23 issue)
scripts/run_validation_model.py           # issue-local runner (one model at a time)
scripts/build_unified_validation_json.py  # raw 3 files -> md_<slug>_<ts>.json
scripts/check_validation_counts.py        # denominator + model_id + pricing sanity
scripts/run_md_new_models.sh              # serial orchestrator for all 5 models
results/                                  # raw 3 files + unified JSON per model
logs/                                     # per-run stdout/stderr
reports/                                  # analysis markdown (to be written)
```

## Quick start

```bash
cd /home/devcontainers/PRISMA-AI

# One-paper smoke for all 5 models (Tsuge2025_PRISMA2020_120)
bash test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_md_new_models.sh --smoke

# Full 10-paper run after smoke has passed
bash test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_md_new_models.sh
```

Single-model reruns (e.g. after a model-specific fix):

```bash
PYTHONPATH=. \
  venv/bin/python test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_validation_model.py \
  --model-id gpt-5.4 --gpt5-reasoning none
```

## Post-run reflection

Once the full run succeeds, copy the five unified JSONs into
`test/issues/2025-10-23_tsuge_md_validation_metrics/results/` and regenerate:

1. `paper/figures/make_validation_macro_chart.py` (update
   `MODEL_DISPLAY_ORDER`, `clean_model_name`, `valid_timestamps`).
2. `test/issues/2025-10-24_validation_ci_update/scripts/compute_validation_ci.py`.
3. `test/issues/2025-10-24_table2_runtime_cost/scripts/aggregate_table2_runtime_cost.py`.
4. Pricing (`data/pricing/model_pricing.toml`): the five new entries shipped as
   provisional placeholders — verify against each provider's public pricing page
   before Table 2 is finalized.

## Notes

- Pipeline CLI does not expose `--use-claude-native`, `--order-mode`, or
  `--section-mode`; the issue-local runner injects them via `gemini_params`.
- `MAX_CONCURRENT_PAPERS=1` is enforced so Anthropic / OpenAI / OpenRouter do
  not run paper-level concurrency during validation.
