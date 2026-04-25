# PRISMA-AI Public Benchmark

This repository is the public companion to the PRISMA-AI manuscript ([arXiv:2511.16707](http://arxiv.org/abs/2511.16707)). It hosts the redistributable systematic-review benchmark, the locked evaluation pipeline, and a **living leaderboard** that grows whenever a new LLM is run through the same Tsuge 10-paper Markdown validation protocol.

The 19-model figures, tables, and analyses cited in the manuscript are frozen and reproducible from the artifacts in this repository; see **[REPRODUCTION.md](REPRODUCTION.md)** for the manuscript-aligned reproduction guide. The leaderboard below extends that frozen evidence with subsequent runs (Kimi K2.6, DeepSeek V4 Pro, and any future additions); it is regenerated from the same unified validation JSONs and is independent from the manuscript.

## Leaderboard

<!-- LEADERBOARD:START -->
**Cohort**: tsuge_md_validation_10 (10 systematic reviews, 530 comparable item decisions = 410 main-body + 120 abstract per cohort). Schema: `simple`. Checklist format: `md`. Reference labels: two-rater consensus PRISMA 2020 from the source publications.

| Rank | Model | Provider | Accuracy % (95% CI) | Sens % | Spec % | F1 % | Cohen κ | Cost / SR | Time / SR (sec) | Schema | Notes |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | Grok-4.20 | xAI | 86.04 (82.83-88.73) | 89.23 | 81.97 | 87.75 | 0.715 | $0.017 | 53.5 | simple | Routed via xAI direct (OpenRouter upstream times out on long tool calls). |
| 2 | Grok-4-fast | xAI (via OpenRouter) | 83.02 (79.59-85.98) | 89.56 | 74.68 | 85.53 | 0.651 | $0.005 | 27.0 | simple |  |
| 3 | GPT-5.4 | OpenAI | 82.08 (78.58-85.11) | 86.87 | 75.97 | 84.45 | 0.633 | $0.060 | 31.6 | simple |  |
| 4 | Gemini 3 Flash | Google | 81.51 (77.98-84.58) | 92.26 | 60.77 | 86.79 | 0.563 | $0.049 | 24.0 | simple |  |
| 5 | Gemini 3.1 Pro | Google | 81.51 (77.98-84.58) | 90.24 | 70.39 | 84.54 | 0.618 | $0.055 | 90.4 | simple |  |
| 6 | Gemini 3 Pro | Google | 81.32 (77.78-84.41) | 91.25 | 68.67 | 84.56 | 0.612 | - | 113.0 | simple | (cost_unavailable:no_input_output_split) |
| 7 | Qwen3.6 Plus | Alibaba (via OpenRouter) | 81.32 (77.78-84.41) | 87.54 | 73.39 | 84.01 | 0.616 | $0.050 | 245.3 | simple | (pricing_flag:variable_rate) |
| 8 | Grok-4 | xAI (via OpenRouter) | 81.13 (77.58-84.23) | 86.20 | 74.68 | 83.66 | 0.614 | $0.111 | 117.8 | simple |  |
| 9 | Grok-4.1-fast | xAI (via OpenRouter) | 81.13 (77.58-84.23) | 88.25 | 67.40 | 86.03 | 0.570 | $0.006 | 58.3 | simple |  |
| 10 | GPT-OSS-120B | OpenAI (via OpenRouter) | 80.94 (77.38-84.06) | 89.56 | 69.96 | 84.04 | 0.606 | $0.002 | 42.8 | simple |  |
| 11 | DeepSeek V4 Pro | DeepSeek (via OpenRouter) | 80.94 (77.38-84.06) | 76.43 | 86.70 | 81.80 | 0.620 | $0.053 | 177.3 | simple | Tool calling via tool_choice=auto (forced rejected upstream); see test/issues/2026-04-25_deepseek_v4_pro_openrouter_capability_check/ for capability probes. |
| 12 | GPT-5.1 | OpenAI | 80.19 (76.58-83.36) | 87.21 | 71.24 | 83.15 | 0.592 | - | 140.4 | simple | (cost_unavailable:no_input_output_split) |
| 13 | Claude Opus 4.7 | Anthropic | 79.81 (76.18-83.01) | 94.28 | 61.37 | 83.96 | 0.576 | $0.183 | 39.2 | simple | Effort level chosen by Tsuge sweep (low/medium/high/xhigh/max); see test/issues/2026-04-17_tsuge10_md_claude47_effort_sweep/. |
| 14 | Qwen3-235B | Alibaba (via OpenRouter) | 79.43 (75.79-82.66) | 93.94 | 60.94 | 83.66 | 0.568 | $0.003 | 53.7 | simple |  |
| 15 | Gemini 2.5 Pro | Google | 79.06 (75.39-82.31) | 84.51 | 72.10 | 81.89 | 0.571 | $0.045 | 76.4 | simple |  |
| 16 | Claude Opus 4.1 | Anthropic | 79.06 (75.39-82.31) | 82.49 | 74.68 | 81.53 | 0.574 | $0.562 | 122.4 | simple |  |
| 17 | GPT-5 | OpenAI | 78.11 (74.40-81.42) | 87.21 | 66.52 | 81.70 | 0.547 | $0.031 | 18.4 | simple |  |
| 18 | Qwen3-Max | Alibaba (via OpenRouter) | 77.92 (74.20-81.25) | 95.96 | 54.94 | 82.97 | 0.532 | $0.027 | 56.1 | simple | 32k output cap; reasoning disabled (provider does not expose it). (pricing_flag:variable_rate) |
| 19 | Kimi K2.6 | Moonshot | 77.55 (73.80-80.89) | 71.04 | 85.84 | 78.00 | 0.555 | $0.048 | 522.9 | simple | Routed via Moonshot direct API; OpenRouter routes hung on long tool calls (see test/issues/2026-04-22_kimi_k2_6_openrouter_structured_output/). |
| 20 | Claude Sonnet 4.5 | Anthropic | 72.64 (68.69-76.26) | 74.75 | 69.96 | 75.38 | 0.446 | $0.163 | 207.8 | simple |  |
| 21 | GPT-4o | OpenAI | 68.49 (64.41-72.30) | 96.97 | 32.19 | 77.52 | 0.313 | $0.043 | 31.8 | simple |  |

<!-- LEADERBOARD:END -->

The leaderboard table is auto-generated. Re-run with `PYTHONPATH=. python3 analysis/build_leaderboard.py --inject-readme` after adding a new entry to `leaderboard/manifest.yaml`.

- Sortable CSV: [`leaderboard/leaderboard.csv`](leaderboard/leaderboard.csv)
- Machine-readable JSON: [`leaderboard/leaderboard.json`](leaderboard/leaderboard.json)
- Per-model experiment logs: [`leaderboard/experiments/`](leaderboard/experiments/) (one Markdown file per model with locked parameters, per-paper metrics, runtime, cost, and reproduction notes)

### Interpreting the columns

- **Accuracy / 95% CI** is the per-model pooled proportion of correct binary item decisions across all 530 comparable items, with a Wilson score 95% confidence interval.
- **Sensitivity** = TP / (TP + FN), the rate at which the model correctly accepts items the human reference also accepted.
- **Specificity** = TN / (TN + FP), the rate at which the model correctly rejects items the human reference also rejected.
- **F1** is the harmonic mean of precision and sensitivity over the same 530 decisions.
- **Cohen κ** measures agreement with the human reference adjusted for chance.
- **Cost / SR** is computed from each paper's `token_usage` against the rates in [`data/pricing/model_pricing.toml`](data/pricing/model_pricing.toml). Variable or provisional rates are flagged in the **Notes** column. Two older unified JSONs (Gemini 3 Pro, GPT-5.1) lack per-paper input/output token splits and therefore do not produce a Cost / SR; they are flagged accordingly.
- **Time / SR** is the per-paper mean of `overall_metadata.processing_time` (or, when per-paper metadata is missing, `experiment_metadata.total_processing_time / num_papers`).

### What is the cohort?

All entries are evaluated under the same locked pipeline:

- **Cohort**: 10 Tsuge systematic reviews (CC-licensed subset of the rehabilitation cohort), seed `20250928`, identical to the validation cohort used by every other model in the manuscript.
- **Items**: 53 comparable PRISMA 2020 decisions per SR (41 main-body + 12 abstract; main-text item 2 is a pointer to the abstract checklist and is excluded to avoid double-counting). Total per model: 530 comparable items.
- **Schema**: `simple` (matches the manuscript validation phase).
- **Checklist format**: `md` (Markdown serialisation of the canonical PRISMA 2020 checklist).
- **Order mode**: `eande-first` (E&E in-context preamble before the user paper).
- **Section mode**: `off` (full-text input, no per-section routing).
- **Concurrency**: `MAX_CONCURRENT_PAPERS=1`.

Reference labels were re-used without modification from the consensus PRISMA 2020 codings published by the source studies; see Methods Section 2.7 in the manuscript for the inter-rater statistics on the underlying corpus.

## Adding a new model to the leaderboard

1. Run the locked Markdown validation on the 10-paper Tsuge cohort and capture the unified `md_<slug>_<ts>.json` under `test/issues/<issue_dir>/results/`. The minimal CLI shape mirrors `test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_validation_model.py` (calling `run_evaluation_pipeline()` directly so `order_mode` and `section_mode` can still be supplied).
2. Append a block to [`leaderboard/manifest.yaml`](leaderboard/manifest.yaml). The fields are:
   - `id`: model identifier sent to the API
   - `display_name`: human-readable label for the leaderboard
   - `provider`: provider / route (e.g. `OpenAI`, `xAI (via OpenRouter)`, `Moonshot`)
   - `pricing_id`: id or alias from `data/pricing/model_pricing.toml`
   - `schema_type`: `simple`, `few-shot-v3`, etc.
   - `unified_json`: path to the `md_<slug>_<ts>.json` (relative to the repo root)
   - `parameters`: optional dict of locked parameters (thinking budget, effort level, reasoning effort, etc.)
   - `notes`: free-form caveats (provider routing quirks, rate limits, etc.)
3. (Optional) add a pricing entry to [`data/pricing/model_pricing.toml`](data/pricing/model_pricing.toml). If you skip this, the leaderboard will show `-` in the Cost / SR column with a `pricing_not_found` note.
4. Re-run the aggregator and inject the new table into the README:

   ```bash
   PYTHONPATH=. python3 analysis/build_leaderboard.py --inject-readme
   ```

5. Commit `leaderboard/manifest.yaml`, `leaderboard/leaderboard.{md,csv,json}`, the new file under `leaderboard/experiments/`, and the updated `README.md`.

## What is in this repository

| Path | Contents |
|---|---|
| [`leaderboard/`](leaderboard/) | Manifest, generated table (md/csv/json), per-model experiment logs |
| [`analysis/build_leaderboard.py`](analysis/build_leaderboard.py) | Aggregator that reads the manifest + each unified JSON + pricing toml |
| [`analysis/`](analysis/) | Manuscript-aligned scripts: `aggregate_table2_runtime_cost.py`, `compute_validation_ci.py`, `item_level_error_profile.py`, license filters |
| [`api_pipeline/prisma_evaluator/`](api_pipeline/prisma_evaluator/) | Minimal CLI + config used by the manuscript-aligned scripts |
| [`checklists/canonical/`](checklists/canonical/) | PRISMA 2020 (main + abstract) in JSON / MD / YAML (canonical source of truth) |
| [`data/pricing/`](data/pricing/) | `model_pricing.toml` consumed by the leaderboard and Table 2 scripts |
| [`figures/`](figures/) | Source SVG/PNG assets and generation scripts for manuscript Figures 1-4 |
| [`pdf_preprocessing/`](pdf_preprocessing/) | Adobe PDF Services extraction pipeline + section splitter |
| [`protocol/`](protocol/) | Study protocol (Markdown / Word), bibliography, citation style |
| [`results/license_filter/enriched/`](results/license_filter/enriched/) | CC-enriched annotation JSONs |
| [`test/issues/.../results/`](test/issues/) | Unified evaluator outputs for the format-comparison cohort, every Tsuge validation run, and item-level profiling |
| [`environment/.env.example`](environment/) | Placeholder environment variables (copy to `.env` before reruns) |

## Environment setup

```bash
cd /path/to/extracted/PRISMA-AI-Share
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp environment/.env.example .env          # fill in your own keys; keep secrets private
```

Required variables (defined in `environment/.env.example`):

- `PDF_SERVICES_CLIENT_ID`, `PDF_SERVICES_CLIENT_SECRET` (Adobe PDF Services)
- `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` (LLM providers)
- Optional throttles: `PRISMA_EVALUATOR_MAX_WORKERS`, `GPT_OSS_MAX_TOKENS`

For the leaderboard regenerator the only requirement is Python with `pyyaml` and `tomllib` (stdlib on 3.11+).

## Raw data access

The raw paper data used for evaluation is available at [https://doi.org/10.5281/zenodo.17547700](https://doi.org/10.5281/zenodo.17547700).

## Manuscript reproduction

The figures, tables, and analyses cited directly in the manuscript are produced by the scripts described in **[REPRODUCTION.md](REPRODUCTION.md)**. The leaderboard above does not modify any manuscript-frozen output; it only ingests the same unified validation JSONs as Figure 4 plus any post-manuscript additions.

## Acknowledgments

This work was supported by a JSPS Grant-in-Aid for Scientific Research (Grant No. 25K13585) provided to Y. Kataoka.

## Paper

Kataoka Y, So R, Banno M, Tsujimoto Y, Takayama T, Yamagishi Y, Tsuge T, Yamamoto N, Suda C, Furukawa TA. Large language models for automated PRISMA 2020 adherence checking. arXiv. 2025. Available from: http://arxiv.org/abs/2511.16707
