# 2025-10-26 — GPT-5 reasoning effort ablation (Suda simple schema)

## Purpose
Evaluate how GPT-5 reasoning effort (`minimal`, `medium`, `high`) affects PRISMA checklist performance when using the simple Markdown prompt on the five-paper Suda development subset (Suda2025_15, _17, _18, _5, _7).

## Setup
- CLI: `venv/bin/python -m prisma_evaluator.cli.main run`
- Common flags: `-m gpt-5 -d suda -st simple --order-mode paper-first --section-mode minimal --checklist-format md`
- Environment: `PRISMA_AI_DRIVE_PATH=/home/prisma-ai-data`, `ANNOTATION_DATA_PATH=/home/prisma-ai-data/annotation`, `STRUCTURED_DATA_SUBDIRS_OVERRIDE="Suda2025-SR文献"`, `ENABLE_SUDA=true`, others disabled.
- Runs executed serially with `--gpt5-reasoning {minimal,medium,high}`; logs saved under `logs/`, unified outputs copied to `results/`.

Replication template:
```bash
PAPERS="Suda2025_15,Suda2025_17,Suda2025_18,Suda2025_5,Suda2025_7"
PRISMA_AI_DRIVE_PATH=/home/prisma-ai-data \
ANNOTATION_DATA_PATH=/home/prisma-ai-data/annotation \
STRUCTURED_DATA_SUBDIRS_OVERRIDE="Suda2025-SR文献" \
ENABLE_SUDA=true ENABLE_TSUGE_PRISMA=false ENABLE_TSUGE_OTHER=false \
PYTHONPATH=. venv/bin/python -m prisma_evaluator.cli.main run \
  -m gpt-5 -d suda --paper-ids "$PAPERS" \
  -st simple --order-mode paper-first --section-mode minimal \
  --checklist-format md --gpt5-reasoning <minimal|medium|high>
```

## Results (overall metrics)
| Reasoning | Accuracy | Sensitivity | Specificity | F1 | Tokens / paper (mean) | Total tokens | File |
| --- | --- | --- | --- | --- | --- | --- | --- |
| minimal | 0.7547 | 0.8653 | 0.4583 | 0.8371 | 18,836 | 94,181 | `results/20251026_112029_gpt5_reasoning_minimal.json` |
| medium | 0.7132 | 0.7358 | 0.6528 | 0.7889 | 26,047 | 130,234 | `results/20251026_112431_gpt5_reasoning_medium.json` |
| high | 0.6906 | 0.7306 | 0.5833 | 0.7747 | 35,263 | 176,314 | `results/20251026_112932_gpt5_reasoning_high.json` |

Notes:
- Accuracy and F1 peak at the minimal reasoning setting, but specificity collapses (45.8%) because false positives rise (39 FP vs. 25–30 for higher efforts).
- Medium reasoning recovers specificity (65.3%) with a modest accuracy drop and ~1.4× token cost over minimal.
- High reasoning increases cost to ~3.1×10⁴ tokens/paper without improving accuracy or sensitivity relative to medium.
- All runs completed the full 265-item evaluation; no retries failed.

## Artifacts
- Logs: `logs/20251026_gpt5_reasoning_{minimal,medium,high}.log`
- Unified outputs: see `results/` files listed above.
