# GPT-5.6 Terra reasoning-effort sweep（Tsuge 10論文 MD validation）

- 日付: 2026-07-10
- ステータス: 完了（2026-07-10 実行済み、結果は `FINAL_REPORT.md` 参照）
- テンプレート: `test/issues/2026-07-10_tsuge10_md_gpt56_luna_effort_sweep/`（Lunaスイープ）

## 目的

GPT-5.6 Terra を validation cohort（Tsuge PRISMA 10論文、MDチェックリスト）で評価し、
reasoning effort 3水準（`none`, `low`, `high`）の精度・時間・コストを比較する。
同日実施の Luna スイープおよび GPT-5.5 スイープ（2026-04-25）と直接比較可能な条件。

## 実験デザイン

| 項目 | 値 |
|---|---|
| モデル | `gpt-5.6-terra`（GPT5Evaluator / Responses API 経由） |
| データセット | tsuge-prisma、10論文（`data/tsuge_selected10.txt`、seed 20250928） |
| チェックリスト形式 | md |
| スキーマ | simple |
| order-mode | eande-first |
| section-mode | off |
| verbosity | low（プロジェクト既定、上書きなし） |
| reasoning effort | none / low / high（各1ラン、直列実行。xhigh は対象外） |
| reasoning_mode | 未指定（APIに送らない = API既定） |
| 分母チェック | full = 530項目（main 410 + abstract 120） |
| 価格 | `model_pricing.toml` 登録済み（入力 $2.50 / 出力 $15.00 per 1M） |

## 実行手順

```bash
# 1) スモーク（1論文 × 3 effort）
bash test/issues/2026-07-10_tsuge10_md_gpt56_terra_effort_sweep/scripts/run_effort_sweep.sh --smoke

# 2) 本番（10論文 × 3 effort、完走後に自動集計）
bash test/issues/2026-07-10_tsuge10_md_gpt56_terra_effort_sweep/scripts/run_effort_sweep.sh

# 3) 集計のみ再実行
PYTHONPATH=. venv/bin/python \
  test/issues/2026-07-10_tsuge10_md_gpt56_terra_effort_sweep/scripts/aggregate_effort_sweep.py \
  --model-id gpt-5.6-terra
```

## 成果物

- `results/md_gpt-5.6-terra_<timestamp>.json`（effort別 統合JSON）
- `results/ai_evaluations_* / accuracy_summary_* / comparison_details_*`（raw 3点セット）
- `reports/effort_comparison.{md,csv}`
- `results/smoke/`（スモーク成果物）
- 結果サマリーは `FINAL_REPORT.md` 参照
