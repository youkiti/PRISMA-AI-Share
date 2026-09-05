# Gemini 3.8 Flash — Tsuge 10論文 MD validation（thinking level スイープ）

## 目的

Gemini Flash 系の最新GA版 **Gemini 3.8 Flash**（`gemini-3.8-flash`）を、
既存の validation コホート（Tsuge PRISMA 10論文、MD形式）で評価し、
README のベンチマークリーダーボードに追加する。

## 設定

| 項目 | 値 |
|---|---|
| Model ID | `gemini-3.8-flash`（`--model-id` と `--gemini-model` に同じ値） |
| API | Gemini Direct API（google-genai、`GeminiDirectEvaluator`） |
| thinking level | **low / medium** の2水準 |
| temperature | 1.0（Gemini 3系のGoogle推奨値） |
| schema-type | simple |
| checklist-format | md |
| order-mode | eande-first |
| section-mode | off |
| 論文 | `data/tsuge_selected10.txt`（10本、seed 20250928） |

`minimal` は非対応（`Thinking level MINIMAL is not supported for this model` が返る）。
`high` は本スイープの対象外。

## 実行方法

```bash
bash test/issues/2026-09-05_tsuge10_md_gemini38_flash_level_sweep/scripts/run_level_sweep.sh --smoke
bash test/issues/2026-09-05_tsuge10_md_gemini38_flash_level_sweep/scripts/run_level_sweep.sh
```

本実行の最後に `scripts/aggregate_level_sweep.py` が走り、
`reports/level_comparison.{csv,md}` を生成する。

## 結果サマリー

| thinking level | Acc (%) | κ | mean t/SR (s) | $/SR |
|---|---:|---:|---:|---:|
| low | 81.13 | 0.6146 | 8.5 | 0.0185 |
| **medium** | **82.26** | 0.6380 | 22.5 | 0.0397 |

詳細は `FINAL_REPORT.md` を参照。

## 本実験で判明した実装上の問題（修正済み）

1. **`medium` が `HIGH` に丸められていた**: `GeminiDirectEvaluator` の
   `thinking_level_map` が導入当時のSDK enum（LOW/HIGHのみ）に合わせて
   `medium → HIGH` にマップしていた。2026-09-05 に現行の Gemini 3系
   （3.8 Flash / 3.1 Pro / 3 Flash preview）が `MEDIUM` を受理することを実機確認し、
   素通しするよう修正。修正前に走らせていたら low vs high の比較になっていた。
2. **思考トークンがコスト集計から抜けていた**: Gemini の
   `candidates_token_count`（=output_tokens）には思考トークンが含まれないが、
   Google は思考トークンを出力として課金する。`thoughts_token_count` を
   記録するよう `GeminiDirectEvaluator` を修正し、集計側も課金対象出力に
   加算するようにした。medium の $/SR は $0.018 → $0.040 に訂正。
