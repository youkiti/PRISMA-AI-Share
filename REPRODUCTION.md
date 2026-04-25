# Manuscript Reproduction Guide

This document is the original PRISMA-AI manuscript reproduction guide. It covers every artifact cited in the manuscript: figures, tables, the licensing filter, the protocol, and the PDF extraction pipeline. The leaderboard table on the front page (`README.md`) is built separately by `analysis/build_leaderboard.py` and is independent from the manuscript-frozen analyses below.

Each directory mirrors the original repository layout so the scripts run in-place without extra dependencies.

## Directory Guide

| Path | Contents / Purpose |
| --- | --- |
| `analysis/` | Table generators (`aggregate_table2_runtime_cost.py`, `compute_validation_ci.py`, `item_level_error_profile.py`) and CC licensing helpers |
| `api_pipeline/prisma_evaluator/` | Minimal CLI + config required for cost aggregation and checklist loading |
| `checklists/canonical/` | PRISMA 2020 (main + abstract) in JSON/MD/YAML (canonical source) |
| `data/pricing/` | `model_pricing.toml` referenced by the cost scripts |
| `export/suda_multi_format_scaling/` | Format comparison report + CSV used by Figure?2/3 |
| `figures/` | Source SVG/PNG assets and generation scripts for Figures?1?4 |
| `protocol/` | Study protocol (Markdown/Word), bibliography (`ref.bib`), and citation style (`vancouver.csl`) |
| `pdf_preprocessing/` | Adobe PDF Services extraction pipeline + section splitter |
| `results/license_filter/enriched/` | CC-enriched annotation JSONs |
| `test/issues/.../results` | Unified evaluator outputs for Suda (format comparison), Tsuge validation, and item-level profiling |
| `environment/.env.example` | Placeholder environment variables (copy to `.env` before reruns) |

## Environment Setup

```bash
cd /path/to/extracted/@toExport
python3 -m venv .venv
. .venv/bin/activate
pip install -r ../requirements.txt        # run from the full PRISMA-AI repo if available
cp environment/.env.example .env          # fill in your own keys; keep secrets private
```

Required variables (defined in `.env.example`):

- `PDF_SERVICES_CLIENT_ID`, `PDF_SERVICES_CLIENT_SECRET` (Adobe PDF Services)
- `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY` (LLM providers)
- Optional throttles: `PRISMA_EVALUATOR_MAX_WORKERS`, `GPT_OSS_MAX_TOKENS`

## Reproducing Figures

All commands assume the bundle root as the working directory and `PYTHONPATH=.`.

1. **Figure?1 ? Study overview**
   - Assets: `figures/prisma-ai-figure1*.svg/png`
   - SVG sanitization & PNG export commands are embedded in `manuscript/export_plan.md` (same as manuscript appendix). Re-run those steps if you need to regenerate from the original draw.io files.

2. **Figure?2 ? Format macro metrics**
   ```bash
   PYTHONPATH=. .venv/bin/python figures/make_format_macro_chart.py
   ```
   - Inputs: `export/suda_multi_format_scaling/reports/format_metrics.md`
   - Outputs: `figures/format_macro_metrics.(svg|png)`

3. **Figure?3 ? Model macro metrics**
   ```bash
   PYTHONPATH=. .venv/bin/python figures/make_model_macro_chart.py
   ```
   - Inputs: `export/suda_multi_format_scaling/data/model_macro_metrics.csv`
   - Outputs: `figures/model_macro_metrics.(svg|png)`

4. **Figure?4 ? Validation macro metrics**
   ```bash
   PYTHONPATH=. .venv/bin/python figures/make_validation_macro_chart.py
   ```
   - Inputs: `test/issues/2025-10-23_tsuge_md_validation_metrics/results/*20251023_184404.json`
   - Outputs: `figures/validation_macro_metrics.(svg|png)`

## Reproducing Tables

1. **Table?2 ? Runtime & API cost (Suda Markdown runs)**
   ```bash
   PYTHONPATH=. .venv/bin/python analysis/aggregate_table2_runtime_cost.py \
     --results-dir test/issues/2025-09-27_suda_multi_format_scaling/results \
     --output-json test/issues/2025-10-24_table2_runtime_cost/results/table2_runtime_cost.json \
     --output-csv  test/issues/2025-10-24_table2_runtime_cost/results/table2_runtime_cost.csv
   ```
   - Relies on `data/pricing/model_pricing.toml` via `prisma_evaluator/analysis/costs.py`.

2. **Table?3 ? Validation metrics with 95?% CIs**
   ```bash
   PYTHONPATH=. .venv/bin/python analysis/compute_validation_ci.py
   ```
   - Reads `test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_*.json`.
   - Emits `test/issues/2025-10-24_validation_ci_update/reports/validation_ci_summary.md` (create directories as needed).

3. **Tables?4a/4b ? Item-level FN/FP profiles**
   ```bash
   PYTHONPATH=. .venv/bin/python analysis/item_level_error_profile.py \
     --dataset Suda=test/issues/2025-09-27_suda_multi_format_scaling/results/20250928_114923_gpt5_md_reasoning_high.json \
     --dataset Tsuge=test/issues/2025-10-23_tsuge_md_validation_metrics/results/md_gpt-5_20251023_184404.json \
     --output-dir test/issues/2025-10-31_item_level_error_profile/reports
   ```
   - Final Markdown summaries live in `test/issues/2025-10-31_item_level_error_profile/reports/item_level_summary.md`.

## PDF Extraction & Licensing

1. **Adobe PDF Services extraction**
   ```bash
   PDF_SERVICES_CLIENT_ID=... PDF_SERVICES_CLIENT_SECRET=... \
   .venv/bin/python pdf_preprocessing/suda_04_pdf_to_json.py --help
   ```
   - Similar scripts exist for the Tsuge datasets. Use the paired `_05_unzip.py` and `_06_integrate_to_structured_data.py` to unpack and merge outputs.

2. **Creative Commons metadata enrichment**
   ```bash
   PYTHONPATH=. .venv/bin/python analysis/filter_cc_license.py
   PYTHONPATH=. .venv/bin/python analysis/apply_cc_license_to_annotations.py
   ```
   - Results land under `results/license_filter/enriched/` (already populated here).

## Checklist Canonical Sources

The PRISMA 2020 main and abstract checklists in JSON/MD/YAML within `checklists/canonical/` are the single sources of truth. Regenerate plain-text or XML derivatives (if needed) using the commands documented in `manuscript/export_plan.md`.

## Protocol

- Location: `protocol/`
- Files:
  - `protocol-english.md`: Study protocol (English, Markdown)
  - `protocol-english.docx`: Pre-built Word export of the protocol
  - `ref.bib`: Bibliography used for citations
  - `vancouver.csl`: Vancouver citation style

Rebuild the protocol document with Pandoc (optional):

```bash
# Generate Word document
pandoc protocol/protocol-english.md \
  --bibliography protocol/ref.bib \
  --csl protocol/vancouver.csl \
  --standalone \
  -o protocol/protocol-english.docx

# Generate PDF (requires a LaTeX engine, e.g., XeLaTeX)
pandoc protocol/protocol-english.md \
  --bibliography protocol/ref.bib \
  --csl protocol/vancouver.csl \
  --pdf-engine=xelatex \
  -o protocol/protocol-english.pdf
```

## Raw Data Access

The raw paper data used for evaluation is available at [https://doi.org/10.5281/zenodo.17547700](https://doi.org/10.5281/zenodo.17547700). Zenodo users can request access to the dataset.

## Notes

- Keep `.env` files private?never commit them. Use `environment/.env.example` as the template.
- All paths above are relative to this bundle root; adjust output destinations if you prefer to keep regenerated artifacts separate.
- For end-to-end evaluator reruns, mount this bundle inside the full PRISMA-AI repository, activate the shared virtual environment, and run `prisma_evaluator/cli/main.py` as described in the manuscript.

## Acknowledgments

This work was supported by a JSPS Grant-in-Aid for Scientific Research (Grant No. 25K13585) provided to Y.K.

## Paper
Kataoka Y, So R, Banno M, Tsujimoto Y, Takayama T, Yamagishi Y, Tsuge T, Yamamoto N, Suda C, Furukawa TA. Large language models for automated PRISMA 2020 adherence checking. arXiv. 2025. Available from: http://arxiv.org/abs/2511.16707
  

