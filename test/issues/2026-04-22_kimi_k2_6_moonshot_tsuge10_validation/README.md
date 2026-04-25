# 2026-04-22 Kimi K2.6 Moonshot Tsuge10 Validation

This issue tracks the Tsuge2025-PRISMA 10-paper Markdown validation run for
`moonshotai/kimi-k2.6` through Moonshot's direct OpenAI-compatible API. The
goal is to validate whether the direct route can complete the locked Tsuge10
cohort with `thinking.type=enabled` once long-running requests are allowed to
finish, then aggregate the outputs into the same unified JSON shape used by the
existing validation reports.

The paper cohort is fixed to the same ten IDs used by
`test/issues/2025-10-23_tsuge_md_validation_metrics` so the resulting metrics
remain directly comparable with prior validation runs. Raw evaluator outputs are
collected under `results/`, then converted into a unified validation JSON and a
brief markdown summary under `reports/`.

The Moonshot direct path is now also registered as the formal experiment preset
`kimi_k26_moonshot` in `test/experiment_framework/experiment_configs.py`.
Reproduction helpers are stored in `scripts/`: `run_tsuge10_validation.sh`
replays the Tsuge10 validation with `thinking=enabled`, and
`aggregate_tsuge10_validation.sh <timestamp>` copies the raw outputs, builds the
unified JSON, and verifies the expected `530/410/120` comparable counts.
