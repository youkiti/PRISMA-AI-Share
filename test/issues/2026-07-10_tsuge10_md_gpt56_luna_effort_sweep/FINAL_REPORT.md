# FINAL REPORT: GPT-5.6 Luna reasoning-effort sweep（Tsuge 10論文 MD validation）

- 実施日: 2026-07-10
- モデル: `gpt-5.6-luna`（OpenAI Responses API 直接、GPT5Evaluator）
- 条件: Tsuge PRISMA 10論文 / md / simple / eande-first / section-mode off / verbosity low / reasoning_mode 未指定
- 分母: 全effortで530項目（main 410 + abstract 120）、`check_validation_counts.py` 全パス

## 主要指標（Overall, 10論文）

| effort | Acc | Prec | Rec | F1 | Spec | κ | mean t/SR (s) | tokens | $/SR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| none | 79.81 | 79.69 | 85.86 | 82.66 | 72.10 | 0.5858 | 9.9 | 152,829 | 0.0239 |
| low | 80.00 | 82.59 | 81.48 | 82.03 | 78.11 | 0.5948 | 14.0 | 158,568 | 0.0273 |
| high | 79.62 | 82.47 | 80.81 | 81.63 | 78.11 | 0.5876 | 38.0 | 195,381 | 0.0494 |
| xhigh | 80.19 | 83.57 | 80.47 | 81.99 | 79.83 | 0.5999 | 100.7 | 278,136 | 0.0991 |

コストは `data/pricing/model_pricing.toml` の Luna エントリ（入力 $1.00 / 出力 $6.00 per 1M、
2026-07 に developers.openai.com/api/docs/pricing で確認）による short-context 概算。

## 所見

1. **effort間の精度差は ±0.6pt 以内**（79.62〜80.19%）で、実質同等。κも 0.586〜0.600 の狭い帯。
2. コストと時間は effort で大きく変わる: none → xhigh で時間 10倍（9.9→100.7 s/SR）、
   コスト 4.1倍（$0.024→$0.099/SR）。精度リターンはほぼゼロ。
3. effort を上げると Specificity が改善（72.1→79.8%）し Recall が低下（85.9→80.5%）する
   トレードオフ。総合精度は動かない。
4. GPT-5.5 スイープ（同一コホート・同一条件、2026-04-25）との比較:
   - 最良精度は 5.5 low の 81.32% に対し Luna xhigh 80.19% と僅かに下回るが、
     Luna は全効率で 5.5 none/medium/high を上回るか同等。
   - コストは圧倒的に Luna が安い（5.5 low $0.124/SR vs Luna low $0.027/SR、約1/4.5）。
   - 速度も Luna が速い（5.5 low 24.3s vs Luna low 14.0s）。
5. Validation cohort 全体の中での位置づけ（Overall Acc）: Grok-4.20 86.0% > GPT-5.4 82.1%
   ≈ Opus 4.5 82.1% > Gemini 3.1 Pro 81.5% > GPT-5.5(low) 81.3% ≈ Qwen3.6 Plus 81.3%
   > **GPT-5.6 Luna 80.0〜80.2%** > Opus 4.6 80.2% 付近。上位圏だがトップではない。

## 推奨

判断基準（README: effort間 ±1pt 以内ならコスト最小を既定に）に従い、
**Luna の運用既定は `none`（Acc 79.81%、$0.024/SR、9.9s/SR）を推奨**。
バランス重視（Spec 78%、Prec 82.6%）なら `low` が次点で、コスト増も $0.003/SR と僅か。
`high`/`xhigh` は精度リターンがなく推奨しない。

## 成果物

- 統合JSON（effort別、`cli_parameters.gpt5_reasoning` で識別）:
  - none: `results/md_gpt-5.6-luna_20260710_082734.json`
  - low: `results/md_gpt-5.6-luna_20260710_083008.json`
  - high: `results/md_gpt-5.6-luna_20260710_083703.json`
  - xhigh: `results/md_gpt-5.6-luna_20260710_085521.json`
- raw 3点セット（ai_evaluations / accuracy_summary / comparison_details）: `results/` 配下（effort別）
- 集計レポート: `reports/effort_comparison.md` / `reports/effort_comparison.csv`
- 実行ログ: `logs/run_<effort>_20260710_*.log`
- スモーク（1論文×4 effort、全パス）: `results/smoke/`

## 再現方法

```bash
bash test/issues/2026-07-10_tsuge10_md_gpt56_luna_effort_sweep/scripts/run_effort_sweep.sh --smoke  # 確認
bash test/issues/2026-07-10_tsuge10_md_gpt56_luna_effort_sweep/scripts/run_effort_sweep.sh          # 本番
```

## 論文（Figure 4 / Table 2）への反映について

未実施。反映する場合は採用 effort（推奨: none または low）の統合JSONを
`test/issues/2025-10-23_tsuge_md_validation_metrics/results/` にコピーし、
CLAUDE.md「新規LLMモデル追加時の論文更新手順」に従うこと。
