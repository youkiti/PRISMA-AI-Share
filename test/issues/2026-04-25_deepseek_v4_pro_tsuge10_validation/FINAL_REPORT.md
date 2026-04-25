# DeepSeek V4 Pro Tsuge 10-Paper Validation - Final Report

Date: 2026-04-25
Model: `deepseek/deepseek-v4-pro` (routed by OpenRouter to first-party provider DeepSeek; physical model id `deepseek/deepseek-v4-pro-20260423`)
Locked pipeline: schema=`simple`, checklist-format=`md`, order-mode=`eande-first`, section-mode=`off`, MAX_CONCURRENT_PAPERS=1.
Cohort: 10 Tsuge SRs from `data/tsuge_selected10.txt` (seed 20250928, identical to every other validation-cohort model since 2025-10-23).

## Headline metrics

530 comparable item decisions = 10 SRs × 53 items (41 main body + 12 abstract).

| | Accuracy (%) | Precision (%) | Recall (%) | F1 (%) | Specificity (%) | Cohen κ | TP / TN / FP / FN |
|---|---:|---:|---:|---:|---:|---:|---|
| Overall (530) | 80.94 | 87.98 | 76.43 | 81.80 | 86.70 | 0.620 | 227 / 202 / 31 / 70 |
| Main body (410) | 79.76 | 89.40 | 76.38 | 82.38 | 85.26 | 0.589 | 194 / 133 / 23 / 60 |
| Abstract (120) | 85.00 | 80.49 | 76.74 | 78.57 | 89.61 | 0.670 | 33 / 69 / 8 / 10 |

Behavioural pattern: high precision / specificity, moderate recall (consistent with `deepseek-reasoner`'s conservative bias toward rejecting items absent explicit reporting). Smoke test on the first paper alone (Tsuge2025_PRISMA2020_14) showed 100 % precision, 100 % specificity, 81.5 % recall — the full 10-paper run brings precision down to 87.98 % but specificity stays in the high 80s, so the conservative pattern holds.

## Performance and cost (full 10-paper run)

- Mean processing time per SR: **177.33 seconds**
- Median / min / max: 179.57 / 108.39 / 236.59 seconds
- Prompt tokens (10 SRs total): 158 433
- Completion tokens: 71 794 (visible) + 50 238 reasoning = 122 032 charged
- Pricing (OpenRouter / DeepSeek first-party): $1.74 / 1M prompt, $3.48 / 1M completion
- **Total cost: $0.5255 for 10 SRs**
- **Cost per SR: $0.0526**

For Manuscript Table 2 the row would read:

| Model | Mean time per SR (sec) | Cost per SR (USD) |
|---|---:|---:|
| DeepSeek V4 Pro | 177.33 | 0.053 |

## Reliability

- 0 / 10 papers required item-level retry on the main checklist; 0 / 10 on the abstract.
- 0 / 10 final failures.
- 0 HTTP 429 events during the 10-paper run (the 60 / 90 / 120 s backoff ladder added in [openrouter_evaluator.py](/home/devcontainers/PRISMA-AI/prisma_evaluator/llm/openrouter_evaluator.py) was not exercised, but is retained for safety).
- Single-paper smoke test (Tsuge2025_PRISMA2020_14) had identical clean behaviour: 53 / 53 items parsed, 0 retries.

## Integration changes shipped to main code

[prisma_evaluator/llm/openrouter_evaluator.py](/home/devcontainers/PRISMA-AI/prisma_evaluator/llm/openrouter_evaluator.py)

1. Added `_is_deepseek_v4_pro_model(model_id)` helper.
2. `evaluate_paper_content`: when the helper matches, `tool_choice` is set to `"auto"` directly (skipping the forced-then-fallback round-trip, since `deepseek-reasoner` rejects forced tool_choice with HTTP 400).
3. `extra_body.reasoning={"exclude": True}` and `temperature=0.0` for DeepSeek V4 Pro.
4. `max_tokens` raised to 60 000 for this model (reasoning shares the output budget on this endpoint; visible completions seen in the run were ~7 k tokens but reasoning consumed an extra ~5 k per paper, leaving headroom).
5. `RateLimitError` handler uses a fixed `[60, 90, 120]` second backoff ladder for DeepSeek V4 Pro.
6. `get_tool_schema` rewritten to enumerate explicit `properties` for the main checklist. The previous `additionalProperties: { ... }` map was rejected by DeepSeek upstream with `Invalid tool parameters schema : invalid type: map, expected a boolean`. All other OpenRouter providers continue to accept the stricter shape.
7. Fixed a latent argument-order bug in `_create_partial_tool_schema` (`get_tool_schema(checklist, evaluation_type)` -> `get_tool_schema(evaluation_type, prisma_checklist=...)`) that was masked until DeepSeek's stricter validation forced item-level retries.

[prisma_evaluator/core/pipeline.py](/home/devcontainers/PRISMA-AI/prisma_evaluator/core/pipeline.py)

- Added a model-id branch that sets `openrouter_max_tokens = settings.DEEPSEEK_V4_PRO_MAX_TOKENS` (default 60 000) when the model id contains `deepseek-v4-pro`.

[prisma_evaluator/config/settings.py](/home/devcontainers/PRISMA-AI/prisma_evaluator/config/settings.py)

- Added `DEEPSEEK_V4_PRO_MAX_TOKENS: int = 60000`.

## Artifacts

Under `results/`:

- `md_deepseek_deepseek-v4-pro_20260425_094204.json` — unified validation JSON for Figure 4 (`paper/figures/make_validation_macro_chart.py`)
- `accuracy_summary_..._20260425_094204.json` — overall / main / abstract metrics
- `ai_evaluations_..._20260425_094204.json` — per-paper raw decisions
- `comparison_details_..._20260425_094204.json` — item-level reference vs AI decisions
- Plus the smoke-test counterparts (`...smoke_20260425_090742_20260425_091107.json`)

Under `logs/`:

- `md_deepseek_deepseek-v4-pro_20260425_091230.log` — 10-paper run console log
- `md_deepseek_deepseek-v4-pro_smoke_20260425_090742.log` — smoke run log
- Earlier failed run logs (pre-schema-fix) retained for provenance

## Reproduction

```bash
# Smoke (1 paper, ~3 min)
bash test/issues/2026-04-25_deepseek_v4_pro_tsuge10_validation/scripts/run_smoke.sh

# Full validation (10 papers, ~30 min)
bash test/issues/2026-04-25_deepseek_v4_pro_tsuge10_validation/scripts/run_validation.sh
```

Both scripts reuse the canonical multi-model runner at
`test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_validation_model.py`
and move the resulting unified JSON + raw trio into this issue's `results/` folder.

## Next steps for manuscript integration

1. Add `deepseek/deepseek-v4-pro` to `MODEL_DISPLAY_ORDER` in
   `paper/figures/make_validation_macro_chart.py` and to `clean_model_name`
   (display label "DeepSeek V4 Pro"). Append `20260425_094204` to the
   `valid_timestamps` filter. Regenerate Figure 4 via
   `venv/bin/python paper/figures/make_validation_macro_chart.py`.
2. Add a row to Table 2 with the runtime / cost values above.
3. Update Section 2.4 (model roster), Section 2.8 (validation phase), and
   the Abstract to bump the validation roster from 19 → 20 models, listing
   DeepSeek V4 Pro under the rebuttal-period additions.
4. The newly added model does not change any development-phase result
   (DeepSeek V4 Pro was evaluated only in validation under the locked
   pipeline), so Sections 2.7, 3.3, 3.4, Table 1, Figure 2, and Figure 3
   are unaffected.
