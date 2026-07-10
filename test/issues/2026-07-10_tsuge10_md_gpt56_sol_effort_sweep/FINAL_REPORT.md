# FINAL REPORT: GPT-5.6 Sol reasoning-effort sweep（Tsuge 10論文 MD validation）

- 実施日: 2026-07-10
- モデル: `gpt-5.6-sol`（OpenAI Responses API 直接、GPT5Evaluator）
- 条件: Tsuge PRISMA 10論文 / md / simple / eande-first / section-mode off / verbosity low / reasoning_mode 未指定
- 分母: 全effortで530項目（main 410 + abstract 120）、`check_validation_counts.py` 全パス

## 主要指標（Overall, 10論文）

| effort | Acc | Prec | Rec | F1 | Spec | κ | mean t/SR (s) | tokens | $/SR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| none | 80.00 | 80.71 | 84.51 | 82.57 | 74.25 | 0.5914 | 23.3 | 153,134 | 0.1204 |
| low | 80.38 | 83.16 | 81.48 | 82.31 | 78.97 | 0.6028 | 35.0 | 158,294 | 0.1359 |

コストは `data/pricing/model_pricing.toml` の Sol エントリ（入力 $5.00 / 出力 $30.00 per 1M、
2026-07 に developers.openai.com/api/docs/pricing で確認）による short-context 概算。

## 所見

1. none と low の精度差は +0.38pt（80.00 vs 80.38%）で実質同等。Terra / Luna と同じく
   effort 増で Specificity 改善（74.3→79.0%）、Recall 低下（84.5→81.5%）の入れ替わり。
2. **シリーズ内で価格逆転**: 最上位・最高価格の Sol（$0.120〜0.136/SR）が、
   Terra none（82.08%、$0.059/SR）に精度で 1.7〜2.1pt 負けている。
   Luna（79.81〜80.19%、$0.024/SR）とは同等精度で約5倍のコスト。
3. GPT-5.6 シリーズの序列（このタスク）: **Terra > Sol ≈ Luna**。
   PRISMA適合性評価では Terra none が精度・コスト・速度のすべてで最適。
4. Validation cohort 内では Sol low 80.38% は GPT-OSS-120B / DeepSeek V4 Pro（80.94%）の
   直下、Luna / GPT-5.1 / Opus 4.6（80.19%）の直上に位置する。

## 推奨

Sol をこのタスクで使う理由はない（Terra none が全面的に優位）。
あえて登録設定を選ぶなら、Luna と同じ判断基準（±1pt 以内はコスト・速度優先）で
**`none`（80.00%、$0.120/SR、23.3s/SR）**。

## 成果物

- 統合JSON（effort別、`cli_parameters.gpt5_reasoning` で識別）:
  - none: `results/md_gpt-5.6-sol_20260710_110644.json`
  - low: `results/md_gpt-5.6-sol_20260710_111235.json`
- raw 3点セット（ai_evaluations / accuracy_summary / comparison_details）: `results/` 配下（effort別）
- 集計レポート: `reports/effort_comparison.md` / `reports/effort_comparison.csv`
- 実行ログ: `logs/run_<effort>_20260710_*.log`
- スモーク（1論文×2 effort、全パス）: `results/smoke/`

## 再現方法

```bash
bash test/issues/2026-07-10_tsuge10_md_gpt56_sol_effort_sweep/scripts/run_effort_sweep.sh --smoke  # 確認
bash test/issues/2026-07-10_tsuge10_md_gpt56_sol_effort_sweep/scripts/run_effort_sweep.sh          # 本番
```
