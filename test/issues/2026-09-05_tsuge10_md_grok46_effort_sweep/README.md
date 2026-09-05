# Grok-4.6 — Tsuge 10論文 MD validation（reasoning effort: low / medium）

## 目的

xAI の **Grok-4.6**（`x-ai/grok-4.6`、xAI ネイティブAPI経由）を既存の validation
コホート（Tsuge PRISMA 10論文、MD形式）で評価し、README のベンチマーク
リーダーボードに追加する。

本スイープは **recall（感度）を第一指標**として見る。PRISMA チェックリストの
判定支援としては「報告済み項目の取りこぼし（FN）の少なさ」が実務上の価値に
直結するため、レポートの表も recall を先頭に置いている。

## 設定

| 項目 | 値 |
|---|---|
| Model ID | `x-ai/grok-4.6` |
| API | xAI Direct（`prisma_evaluator/llm/xai_direct_evaluator.py`、`XAI_API_KEY` があれば自動ルーティング） |
| reasoning effort | **low / medium** の2水準（xAI既定は high） |
| max output tokens | 128,000（`GROK_4_6_MAX_TOKENS`。reasoning も同じ枠を消費） |
| schema-type | simple |
| checklist-format | md |
| order-mode | eande-first |
| section-mode | off |
| 論文 | `data/tsuge_selected10.txt`（10本、seed 20250928） |

**`none` / `max` は使用不可**: Grok-4.6 が受け付ける effort は low/medium/high/xhigh のみで、
`none`/`max` は HTTP 400 になる（`prisma_evaluator/cli/main.py` に実行前ガードあり）。

## 実行方法

```bash
# smoke（1論文 × 2水準）
bash test/issues/2026-09-05_tsuge10_md_grok46_effort_sweep/scripts/run_effort_sweep.sh --smoke
# 本実行（10論文 × 2水準）
bash test/issues/2026-09-05_tsuge10_md_grok46_effort_sweep/scripts/run_effort_sweep.sh
```

本実行の最後に `scripts/aggregate_effort_sweep.py` が走り、
`reports/effort_comparison.{csv,md}` を生成する。

## コスト計上について

xAI は reasoning トークンを `output_tokens` に含めずに報告する（課金は出力扱い）。
集計は `prisma_evaluator.analysis.costs.calculate_run_cost` を使い、
`billed_output_tokens = max(output_tokens, total_tokens - input_tokens)` で吸収する。
素の `output_tokens` 合計では実請求を大きく下回るため使わない。

料金は `data/pricing/model_pricing.toml` の `xai/grok-4-6`
（prompt < 200k で $2.00 / $6.00 per MTok。キャッシュ入力割引は未反映）。

## 結果サマリー

| effort | Rec (%) | Acc (%) | κ | FN | mean t/SR (s) | $/SR |
|---|---:|---:|---:|---:|---:|---:|
| **low** | **85.19** | 83.40 | 0.6630 | **44** | 59.2 | 0.0545 |
| medium | 83.84 | **84.72** | 0.6920 | 48 | 153.3 | 0.0897 |

両effortとも分母530項目（main 410 + abstract 120）をパス。
**recall優先なら `low`**（FNが4件少なく、コスト1.6分の1・時間2.6分の1）。
effort を上げて改善するのは specificity 側（81.12 → 85.84%）で感度は下がる。
FNはすべて本文側で発生し、抄録は両effortとも取りこぼしゼロ（43/43）。
詳細は `FINAL_REPORT.md` を参照。

## パラメータ受理状況（2026-09-05 実機確認）

| effort | 結果 |
|---|---|
| low / medium | OK（xAI Direct 経由、10論文完走） |
| none / max | CLI が実行前に拒否（xAI APIは HTTP 400） |
| high / xhigh | 本スイープでは未検証 |
