# GPT-5.6 Sol reasoning-effort sweep（Tsuge 10論文 MD validation）

- 日付: 2026-07-10
- ステータス: 完了（2026-07-10 実行済み、結果は `FINAL_REPORT.md` 参照）
- テンプレート: `test/issues/2026-07-10_tsuge10_md_gpt56_terra_effort_sweep/`（Terraスイープ）

## 目的

GPT-5.6 Sol（シリーズ最上位、$5/$30 per 1M）を validation cohort（Tsuge PRISMA 10論文、
MDチェックリスト）で評価し、reasoning effort 2水準（`none`, `low`）の精度・時間・コストを
比較する。同日実施の Terra / Luna スイープと直接比較可能な条件。
Terra / Luna で effort 増による精度改善が見られなかったため、Sol は none / low のみ。

## 実験デザイン

| 項目 | 値 |
|---|---|
| モデル | `gpt-5.6-sol`（GPT5Evaluator / Responses API 経由） |
| データセット | tsuge-prisma、10論文（`data/tsuge_selected10.txt`、seed 20250928） |
| チェックリスト形式 | md |
| スキーマ | simple |
| order-mode | eande-first |
| section-mode | off |
| verbosity | low（プロジェクト既定、上書きなし） |
| reasoning effort | none / low（各1ラン、直列実行） |
| reasoning_mode | 未指定（APIに送らない = API既定） |
| 分母チェック | full = 530項目（main 410 + abstract 120） |
| 価格 | 入力 $5.00 / 出力 $30.00 per 1M（公式確認のうえ `model_pricing.toml` に追加） |

## 実行手順

```bash
# 1) スモーク（1論文 × 2 effort）
bash test/issues/2026-07-10_tsuge10_md_gpt56_sol_effort_sweep/scripts/run_effort_sweep.sh --smoke

# 2) 本番（10論文 × 2 effort、完走後に自動集計）
bash test/issues/2026-07-10_tsuge10_md_gpt56_sol_effort_sweep/scripts/run_effort_sweep.sh

# 3) 集計のみ再実行
PYTHONPATH=. venv/bin/python \
  test/issues/2026-07-10_tsuge10_md_gpt56_sol_effort_sweep/scripts/aggregate_effort_sweep.py \
  --model-id gpt-5.6-sol
```

## 成果物

- `results/md_gpt-5.6-sol_<timestamp>.json`（effort別 統合JSON）
- `results/ai_evaluations_* / accuracy_summary_* / comparison_details_*`（raw 3点セット）
- `reports/effort_comparison.{md,csv}`
- `results/smoke/`（スモーク成果物）
- 結果サマリーは `FINAL_REPORT.md` 参照
