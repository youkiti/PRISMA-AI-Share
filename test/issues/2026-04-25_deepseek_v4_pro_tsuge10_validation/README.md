# 2026-04-25 DeepSeek V4 Pro Tsuge 10-Paper Validation

This issue integrates `deepseek/deepseek-v4-pro` into [prisma_evaluator/llm/openrouter_evaluator.py](/home/devcontainers/PRISMA-AI/prisma_evaluator/llm/openrouter_evaluator.py) and runs the locked Tsuge Markdown validation pipeline (10 SRs, simple schema) so the model can join Figure 4 and Table 2.

The OpenRouter capability check that established the supported request shape (tool calling with `tool_choice="auto"`, hidden reasoning, 60/90/120 s rate-limit backoff) is in `test/issues/2026-04-25_deepseek_v4_pro_openrouter_capability_check/`.

## Fixed defaults

- Model: `deepseek/deepseek-v4-pro`
- Schema: `simple` (matches all other validation-cohort models)
- Checklist format: `md`
- Order mode: `eande-first`
- Section mode: `off`
- Cohort: 10 Tsuge SRs from `data/tsuge_selected10.txt` (seed 20250928, identical to the file used by every other validation-cohort model since 2025-10-23)
- `MAX_CONCURRENT_PAPERS=1` to keep upstream rate-limit pressure manageable
- Locked pipeline: no parameter optimisation; the configuration that worked in the capability check is reused unchanged

## Integration changes

[prisma_evaluator/llm/openrouter_evaluator.py](/home/devcontainers/PRISMA-AI/prisma_evaluator/llm/openrouter_evaluator.py)

1. Added `_is_deepseek_v4_pro_model(model_id)` helper.
2. `evaluate_paper_content`: when the helper matches, `tool_choice` is set to `"auto"` directly (no forced-then-fallback round-trip, since `deepseek-reasoner` rejects forced tool_choice with HTTP 400).
3. `extra_body.reasoning={"exclude": True}` is sent so the visible response stays compact while internal reasoning is preserved.
4. `max_tokens` defaults to 60000 (reasoning shares the output budget on this endpoint).
5. `RateLimitError` handler uses a fixed `[60, 90, 120]` second backoff ladder for DeepSeek V4 Pro (the previous `5 * (attempt + 2)` schedule was too short for the upstream lockouts seen in the capability check).
6. `get_tool_schema` was rewritten to enumerate explicit `properties` for the main checklist (the previous `additionalProperties: { ... }` map was rejected by DeepSeek upstream with `Invalid tool parameters schema : invalid type: map, expected a boolean`). All other OpenRouter providers continue to accept this stricter shape.
7. Fixed a latent argument-order bug in `_create_partial_tool_schema` (`get_tool_schema(checklist, evaluation_type)` -> `get_tool_schema(evaluation_type, prisma_checklist=...)`) that was masked until DeepSeek's stricter validation forced item-level retries.

[prisma_evaluator/core/pipeline.py](/home/devcontainers/PRISMA-AI/prisma_evaluator/core/pipeline.py)

- Added a model-id branch that sets `openrouter_max_tokens = settings.DEEPSEEK_V4_PRO_MAX_TOKENS` (default 60000) when the model id contains `deepseek-v4-pro`.

[prisma_evaluator/config/settings.py](/home/devcontainers/PRISMA-AI/prisma_evaluator/config/settings.py)

- Added `DEEPSEEK_V4_PRO_MAX_TOKENS: int = 60000`.

## Execution

Runs reuse the canonical multi-model runner at `test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_validation_model.py`, which calls `run_evaluation_pipeline()` directly so `order_mode` / `section_mode` can still be supplied even though those flags were removed from the public CLI. The local wrappers below add provenance logging and move artifacts produced by that runner into this issue's `results/` folder.

Smoke test (1 paper):

```bash
bash test/issues/2026-04-25_deepseek_v4_pro_tsuge10_validation/scripts/run_smoke.sh
```

Full validation (10 papers):

```bash
bash test/issues/2026-04-25_deepseek_v4_pro_tsuge10_validation/scripts/run_validation.sh
```

## Smoke result (Tsuge2025_PRISMA2020_14)

53 comparable items (41 main + 12 abstract).

| | Accuracy | Precision | Recall | F1 | Specificity | Cohen κ | counts (TP / TN / FP / FN) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Overall | 90.57 | 100.00 | 81.48 | 89.80 | 100.00 | 0.812 | 22 / 26 / 0 / 5 |
| Main body (41) | 90.24 | 100.00 | 81.82 | 90.00 | 100.00 | 0.807 | 18 / 19 / 0 / 4 |
| Abstract (12) | 91.67 | 100.00 | 80.00 | 88.89 | 100.00 | 0.824 | 4 / 7 / 0 / 1 |

Provider routed by OpenRouter: DeepSeek (only endpoint). Reasoning hidden, temperature=0.0, tool calling via `tool_choice="auto"`. No 429 / parsing errors observed. Conservative behaviour (zero false positives, modest recall) is consistent with `deepseek-reasoner`'s typical bias toward strict yes / no decisions.

## Validation artifacts

After `run_validation.sh` completes, the following files are produced under `results/`:

- `md_deepseek_deepseek-v4-pro_<ts>.json` (unified validation JSON consumed by `paper/figures/make_validation_macro_chart.py` for Figure 4)
- `ai_evaluations_..._<ts>.json` (per-paper raw decisions)
- `accuracy_summary_..._<ts>.json` (overall / main / abstract metrics)
- `comparison_details_..._<ts>.json` (item-level reference vs AI decisions)

The full validation result will be summarised in `FINAL_REPORT.md` after the run completes.
