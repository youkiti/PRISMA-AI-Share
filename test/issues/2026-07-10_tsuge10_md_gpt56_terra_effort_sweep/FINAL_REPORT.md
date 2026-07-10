# FINAL REPORT: GPT-5.6 Terra reasoning-effort sweep（Tsuge 10論文 MD validation）

- 実施日: 2026-07-10
- モデル: `gpt-5.6-terra`（OpenAI Responses API 直接、GPT5Evaluator）
- 条件: Tsuge PRISMA 10論文 / md / simple / eande-first / section-mode off / verbosity low / reasoning_mode 未指定
- 分母: 全effortで530項目（main 410 + abstract 120）、`check_validation_counts.py` 全パス

## 主要指標（Overall, 10論文）

| effort | Acc | Prec | Rec | F1 | Spec | κ | mean t/SR (s) | tokens | $/SR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| none | 82.08 | 80.42 | 89.90 | 84.90 | 72.10 | 0.6302 | 11.8 | 152,333 | 0.0590 |
| low | 80.75 | 84.95 | 79.80 | 82.29 | 81.97 | 0.6126 | 19.7 | 160,042 | 0.0706 |
| high | 80.38 | 85.09 | 78.79 | 81.82 | 82.40 | 0.6058 | 28.3 | 168,695 | 0.0835 |

コストは `data/pricing/model_pricing.toml` の Terra エントリ（入力 $2.50 / 出力 $15.00 per 1M、
2026-07 に developers.openai.com/api/docs/pricing で確認）による short-context 概算。

## 所見

1. **`none` が最高精度（82.08%）かつ最速・最安**。effort を上げると精度はむしろ低下
   （none 82.08 → low 80.75 → high 80.38%）。
2. Luna と同じく、effort を上げると Specificity が改善（72.1→82.4%）し Recall が低下
   （89.9→78.8%）するトレードオフ。Terra では総合精度も下がる。
3. 同日実施の **Luna スイープ**（`2026-07-10_tsuge10_md_gpt56_luna_effort_sweep`）との比較:
   - 精度は Terra が全効率で上回る（Terra none 82.08% vs Luna 最良 xhigh 80.19%）。
   - コストは Terra none $0.059/SR vs Luna none $0.024/SR（Terra が約2.5倍）。
     ただし絶対額はどちらも安価。
4. **GPT-5.5 スイープ**（2026-04-25、同一コホート・同一条件）との比較:
   Terra none 82.08% は 5.5 最良（low 81.32%）を +0.76pt 上回り、
   コストも半分以下（$0.059 vs $0.124/SR）、速度は約2倍（11.8s vs 24.3s/SR）。
5. Validation cohort 全体での位置づけ（Overall Acc）: Grok-4.20 86.0% >
   **GPT-5.6 Terra (none) 82.1%** ≈ GPT-5.4 82.1% ≈ Opus 4.5 82.1% >
   Gemini 3.1 Pro 81.5% > GPT-5.5(low) 81.3% > GPT-5.6 Luna 80.0〜80.2%。
   OpenAI系ではトップタイの水準。

## 推奨

**Terra の運用既定は `none`（Acc 82.08%、$0.059/SR、11.8s/SR）を推奨**。
最高精度・最速・最安が一致しており、effort を上げる理由がない。
False Positive を抑えたい用途（Spec 重視）に限り `low` を検討。

## 成果物

- 統合JSON（effort別、`cli_parameters.gpt5_reasoning` で識別）:
  - none: `results/md_gpt-5.6-terra_20260710_093129.json`
  - low: `results/md_gpt-5.6-terra_20260710_093507.json`
  - high: `results/md_gpt-5.6-terra_20260710_094015.json`
- raw 3点セット（ai_evaluations / accuracy_summary / comparison_details）: `results/` 配下（effort別）
- 集計レポート: `reports/effort_comparison.md` / `reports/effort_comparison.csv`
- 実行ログ: `logs/run_<effort>_20260710_*.log`
- スモーク（1論文×3 effort、全パス）: `results/smoke/`

## 再現方法

```bash
bash test/issues/2026-07-10_tsuge10_md_gpt56_terra_effort_sweep/scripts/run_effort_sweep.sh --smoke  # 確認
bash test/issues/2026-07-10_tsuge10_md_gpt56_terra_effort_sweep/scripts/run_effort_sweep.sh          # 本番
```

## 論文（Figure 4 / Table 2）への反映について

未実施。反映する場合は採用 effort（推奨: none）の統合JSONを
`test/issues/2025-10-23_tsuge_md_validation_metrics/results/` にコピーし、
CLAUDE.md「新規LLMモデル追加時の論文更新手順」に従うこと。
