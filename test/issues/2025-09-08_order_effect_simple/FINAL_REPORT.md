# FINAL REPORT — 2025-09-08 Order Effect (simple)

## 概要
- 比較: A（paper-first） vs B（eande-first） vs いいとこ取り（intersection / union / targeted-union）。
- 対象: Suda5本（Suda2025_15,17,18,5,7）、Claude Opus 4.1、`-st simple`。

## 実行ログリンク
- A統合JSON: `test/issues/2025-09-08_order_effect_simple/results/20250908_124939.json`
- B統合JSON: `test/issues/2025-09-08_order_effect_simple/results/20250908_132808.json`
- Ensemble-Intersection: `test/issues/2025-09-08_order_effect_simple/results/20250908_133512.json` （summary: `test/issues/2025-09-08_order_effect_simple/results/accuracy_summary_metrics_only_from_ensemble_intersection_20250908_133512.json`）
- Ensemble-Union: `test/issues/2025-09-08_order_effect_simple/results/20250908_133708.json` （summary: `test/issues/2025-09-08_order_effect_simple/results/accuracy_summary_metrics_only_from_ensemble_union_20250908_133708.json`）
- Ensemble-TargetedUnion: `test/issues/2025-09-08_order_effect_simple/results/20250908_133835.json` （summary: `test/issues/2025-09-08_order_effect_simple/results/accuracy_summary_metrics_only_from_ensemble_targeted-union_20250908_133835.json`）

## 主要指標（Overall）
- A (paper-first): Acc 80.38 / Prec 83.10 / Rec 91.71 / F1 87.19 / Spec 50.00 / κ 0.4569（tp/tn/fp/fn=177/36/36/16）
- B (eande-first): Acc 79.62 / Prec 84.58 / Rec 88.08 / F1 86.29 / Spec 56.94 / κ 0.4665（tp/tn/fp/fn=170/41/31/23）
- Intersection: Acc 80.00 / Prec 85.71 / Rec 87.05 / F1 86.38 / Spec 61.11 / κ 0.4880（tp/tn/fp/fn=168/44/28/25）
- Union: Acc 80.00 / Prec 82.11 / Rec 92.75 / F1 87.10 / Spec 45.83 / κ 0.4329（tp/tn/fp/fn=179/33/39/14）
- Targeted‑Union: Acc 79.62 / Prec 83.90 / Rec 89.12 / F1 86.43 / Spec 54.17 / κ 0.4567（tp/tn/fp/fn=172/39/33/21）

## 所見
- Intersection: FP抑制でPrecision↑、FN増でRecall↓の想定どおり。
- Union: Recall改善、Precision悪化のトレードオフ。
- Targeted‑Union: 難所のみUnionによりRecall改善を局所化、全体のPrecision悪化を最小化。

## 次アクション
- Targeted‑Unionで悪化した項目の洗い出し（comparison_details参照）
- 難所リストの更新（7,10b,13e,13f,14,21,27,16b,24c 以外の候補追加/削除）
- 必要に応じて項目別の反証例ヒントを追加してB単体の精度も底上げ
