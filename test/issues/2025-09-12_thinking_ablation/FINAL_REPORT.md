# 2025-09-12 実験レポート — Claude thinking アブレーション（E&E in‑context＋感度プレアンブル）

## 目的
- Claudeのthinking予算を段階的に削減しても、main_body_metricsの Acc/Prec/Rec/F1 が実質同等（±0.5pt以内）か検証

## 条件
- モデル: claude-opus-4-1-20250805（Native API, Function Calling）
- スキーマ: eande-incontext（PRISMA 2020 E&E全文 + 感度プレアンブル）
- 入力: section-mode=off（全文）
- データ: Suda固定5本（Suda2025_15, _17, _18, _5, _7）
- 既知の参照（前回）: main Acc 83.90 / Prec 86.36 / Rec 94.41 / F1 90.21

## 判定基準
- baseline対比で main Acc/Prec/Rec/F1 の差が±0.5pt以内 → 合格
- 0.5–1.0pt → 再試行（非決定性の可能性）
- >1.0pt → 不合格

## 実行方法
```bash
bash test/issues/2025-09-12_thinking_ablation/run.sh
```

実行後、以下に各runの統合JSONとmain_body_metricsが追記されます。

対象アーム（thinking_budget_tokens 単位: tokens）:
- budget_30000（default）
- budget_28000
- budget_24000
- budget_30000_alt（multiplier=4x）
- budget_31000（max）

## 実行ログと結果


### budget_24000
- 統合JSON: `results/evaluator_output/20250912_112104.json`
- thinking_budget_tokens: 24000 (multiplier: 2x)
- main: Acc 79.02%, Prec 81.38%, Recall 95.03%, F1 87.68
  - counts: TP 153, TN 9, FP 35, FN 8

\n### budget_30000（default）
- 統合JSON: `results/evaluator_output/20250912_111653.json`
- thinking_budget_tokens: 30000 (multiplier: default)
- main: Acc 76.1%, Prec 82.94%, Recall 87.58%, F1 85.2
  - counts: TP 141, TN 15, FP 29, FN 20
\n### budget_28000
- 統合JSON: `results/evaluator_output/20250912_111854.json`
- thinking_budget_tokens: 28000 (multiplier: 3x)
- main: Acc 82.93%, Prec 87.06%, Recall 91.93%, F1 89.43
  - counts: TP 148, TN 22, FP 22, FN 13
\n### budget_24000
- 統合JSON: `results/evaluator_output/20250912_112104.json`
- thinking_budget_tokens: 24000 (multiplier: 2x)
- main: Acc 79.02%, Prec 81.38%, Recall 95.03%, F1 87.68
  - counts: TP 153, TN 9, FP 35, FN 8
\n### budget_30000_alt（multiplier=4x）
- 統合JSON: `results/evaluator_output/20250912_112300.json`
- thinking_budget_tokens: 30000 (multiplier: 4x)
- main: Acc 80.0%, Prec 83.33%, Recall 93.17%, F1 87.98
  - counts: TP 150, TN 14, FP 30, FN 11
\n### budget_31000（max）
- 統合JSON: `results/evaluator_output/20250912_112458.json`
- thinking_budget_tokens: 31000 (multiplier: max)
- main: Acc 80.49%, Prec 83.43%, Recall 93.79%, F1 88.3
  - counts: TP 151, TN 14, FP 30, FN 10
\n## 差分サマリ（baseline=thinking_default, main_body_metrics）
- budget_28000: accuracy:+6.83, precision:+4.12, recall:+4.35, f1:+4.23 -> FAIL
- budget_24000: accuracy:+2.93, precision:-1.56, recall:+7.45, f1:+2.48 -> FAIL
- budget_30000_alt: accuracy:+3.9, precision:+0.39, recall:+5.59, f1:+2.78 -> RE-RUN
- budget_31000: accuracy:+4.39, precision:+0.48, recall:+6.21, f1:+3.11 -> RE-RUN
\n### budget_30000（default）
- 統合JSON: `results/evaluator_output/20250912_112753.json`
- thinking_budget_tokens: 30000 (multiplier: default)
- main: Acc 81.95%, Prec 86.47%, Recall 91.3%, F1 88.82
  - counts: TP 147, TN 21, FP 23, FN 14
\n### budget_28000
- 統合JSON: `results/evaluator_output/20250912_112957.json`
- thinking_budget_tokens: 28000 (multiplier: 3x)
- main: Acc 82.93%, Prec 85.8%, Recall 93.79%, F1 89.61
  - counts: TP 151, TN 19, FP 25, FN 10
\n### budget_24000
- 統合JSON: `results/evaluator_output/20250912_113151.json`
- thinking_budget_tokens: 24000 (multiplier: 2x)
- main: Acc 78.54%, Prec 83.05%, Recall 91.3%, F1 86.98
  - counts: TP 147, TN 14, FP 30, FN 14
\n### budget_30000_alt（multiplier=4x）
- 統合JSON: `results/evaluator_output/20250912_113402.json`
- thinking_budget_tokens: 30000 (multiplier: 4x)
- main: Acc 80.0%, Prec 82.61%, Recall 94.41%, F1 88.12
  - counts: TP 152, TN 12, FP 32, FN 9
\n### budget_31000（max）
- 統合JSON: `results/evaluator_output/20250912_113558.json`
- thinking_budget_tokens: 31000 (multiplier: max)
- main: Acc 80.98%, Prec 85.06%, Recall 91.93%, F1 88.36
  - counts: TP 148, TN 18, FP 26, FN 13
\n## 差分サマリ（baseline=thinking_default, main_body_metrics）
- budget_28000: accuracy:+0.98, precision:-0.68, recall:+2.48, f1:+0.79 -> RE-RUN
- budget_24000: accuracy:-3.41, precision:-3.42, recall:+0.0, f1:-1.84 -> RE-RUN
- budget_30000_alt: accuracy:-1.95, precision:-3.86, recall:+3.11, f1:-0.71 -> RE-RUN
- budget_31000: accuracy:-0.98, precision:-1.41, recall:+0.62, f1:-0.46 -> RE-RUN
