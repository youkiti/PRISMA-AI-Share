# GPT-6 Astra — Tsuge 10論文 MD validation（reasoning effort スイープ）

## 目的

2026-09-03 リリースの OpenAI フラッグシップ **GPT-6 Astra**（`gpt-6-astra`）を、
既存の validation コホート（Tsuge PRISMA 10論文、MD形式）で評価し、
README のベンチマークリーダーボードに追加する。

## 設定

| 項目 | 値 |
|---|---|
| Model ID | `gpt-6-astra` |
| API | Responses API（`prisma_evaluator/llm/gpt5_evaluator.py`） |
| reasoning effort | **low / medium / high** の3水準 |
| reasoning mode | 未指定（API既定。GPT-5.6スイープと同じ扱い） |
| verbosity | low（プロジェクト既定） |
| schema-type | simple |
| checklist-format | md |
| order-mode | eande-first |
| section-mode | off |
| max output tokens | 128,000 |
| 論文 | `data/tsuge_selected10.txt`（10本、seed 20250928） |

**`none` は使用しない**: GPT-6 Astra は `reasoning.effort=none` を受け付けず HTTP 400 を返す。
2026-09-05 の実機確認でも `Unsupported value: 'none' is not supported with the 'gpt-6-astra' model.
Supported values are: 'low', 'medium', 'high', ...` が返った。
このため CLI 側でも実行前に弾くガードを入れてある（`prisma_evaluator/cli/main.py`）。

## 実行方法

```bash
# 疎通・パラメータ確認 → smoke（1論文）→ 本実行（10論文）
bash test/issues/2026-09-05_tsuge10_md_gpt6_astra_effort_sweep/scripts/run_effort_sweep.sh --smoke
bash test/issues/2026-09-05_tsuge10_md_gpt6_astra_effort_sweep/scripts/run_effort_sweep.sh
```

本実行の最後に `scripts/aggregate_effort_sweep.py` が走り、
`reports/effort_comparison.{csv,md}` を生成する。

## 想定コスト

GPT-5.6 Terra の実測（10論文で入力 135,598 / 出力 16.7k〜33.1k トークン）を基準にすると、
$10/$50 per MTok の Astra では **1水準あたり約 $2.2〜$3.0**、3水準で **$7〜9** 程度。
入力は 272k を大きく下回るため短文ティアのみ。

## 結果サマリー

| effort | Acc (%) | κ | mean t/SR (s) | $/SR |
|---|---:|---:|---:|---:|
| low | 75.28 | 0.4990 | 30.3 | 0.2470 |
| medium | 75.85 | 0.5098 | 39.9 | 0.2790 |
| **high** | **76.42** | 0.5233 | 99.2 | 0.4781 |

全effortで分母530項目（main 410 + abstract 120）をパス。
effort間の差は誤差範囲で、cohort 内では下位グループ。詳細は `FINAL_REPORT.md` を参照。

## パラメータ受理状況（2026-09-05 実機確認）

| effort | 結果 |
|---|---|
| low / medium / high | OK |
| none | **400 Unsupported value**（仕様どおり非対応） |
