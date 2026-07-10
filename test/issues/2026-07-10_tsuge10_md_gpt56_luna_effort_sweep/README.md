# GPT-5.6 Luna reasoning-effort sweep（Tsuge 10論文 MD validation）

- 日付: 2026-07-10
- ステータス: 完了（2026-07-10 実行済み、結果は `FINAL_REPORT.md` 参照）
- テンプレート: `test/issues/2026-04-25_tsuge10_md_gpt5_5_effort_sweep/`（GPT-5.5スイープ）

## 目的

GPT-5.6シリーズ対応（commit `28ff9552`）を受け、GPT-5.6 Luna を validation cohort
（Tsuge PRISMA 10論文、MDチェックリスト）で評価し、reasoning effort 4水準
（`none`, `low`, `high`, `xhigh`）の精度・時間・コストのトレードオフを比較する。

## 実験デザイン

| 項目 | 値 |
|---|---|
| モデル | `gpt-5.6-luna`（GPT5Evaluator / Responses API 経由） |
| データセット | tsuge-prisma、10論文（`data/tsuge_selected10.txt`、seed 20250928） |
| チェックリスト形式 | md |
| スキーマ | simple |
| order-mode | eande-first |
| section-mode | off |
| verbosity | low（プロジェクト既定、上書きなし） |
| reasoning effort | none / low / high / xhigh（各1ラン、直列実行） |
| reasoning_mode | 未指定（APIに送らない = API既定。GPT-5.5スイープとの条件揃え） |
| 分母チェック | full = 530項目（main 410 + abstract 120）、`check_validation_counts.py` で検証 |

GPT-5.5スイープとの違いは effort 水準のみ（5.5は none/low/medium/high、今回は
medium を外し xhigh を追加）。それ以外の条件は完全に揃えてあるため、
`reports/effort_comparison.md` は5.5の同名レポートと直接比較できる。

## 実行手順

```bash
# 1) スモーク（1論文 × 4 effort。新モデル・新effort値のAPI受理確認を兼ねる）
bash test/issues/2026-07-10_tsuge10_md_gpt56_luna_effort_sweep/scripts/run_effort_sweep.sh --smoke

# 2) 本番（10論文 × 4 effort、直列。完走後に自動で集計まで実行）
bash test/issues/2026-07-10_tsuge10_md_gpt56_luna_effort_sweep/scripts/run_effort_sweep.sh

# 3) 集計のみ再実行したい場合
PYTHONPATH=. venv/bin/python \
  test/issues/2026-07-10_tsuge10_md_gpt56_luna_effort_sweep/scripts/aggregate_effort_sweep.py \
  --model-id gpt-5.6-luna
```

想定所要時間: GPT-5.5実績（none 4分 / low 4分 / medium 10分 / high 22分、10論文）から
外挿すると、xhigh は high 超の可能性が高く、全体で 1〜2時間程度を見込む。

## 成果物

- `results/ai_evaluations_* / accuracy_summary_* / comparison_details_*`（effort別、raw 3点セット）
- `results/md_gpt-5.6-luna_<timestamp>.json`（effort別 統合JSON。`cli_parameters.gpt5_reasoning` に effort を記録）
- `reports/effort_comparison.{md,csv}`（Acc/Prec/Rec/F1/Spec/κ/時間/トークン/$per SR）
- `logs/run_<effort>_<timestamp>.log`

## 事前確認事項（実行前チェック）

1. **モデルIDの確定**: 本計画は `gpt-5.6-luna` を仮置き。commit `28ff9552` で追加されたのは
   Terra（`gpt-5.6-terra`）のみなので、Luna の正式なOpenAIモデルIDを実行前に要確認。
   IDに `gpt-5` を含む限り pipeline は GPT5Evaluator へ自動ルーティングし、model IDは
   そのまま Responses API に渡る（コード変更は不要）。IDが異なる場合は
   `scripts/run_effort_sweep.sh` の `MODEL_ID` を修正するだけでよい。
2. **`xhigh` のAPI受理**: CLI/Evaluator側は `xhigh`（と `max`）を受理済み
   （`prisma_evaluator/cli/main.py`, `gpt5_evaluator.py`）。Luna が API側で
   `xhigh` を受けるかはスモークで確認。
3. **`none` のAPI受理**: 5.1/5.2/5.5では動作実績あり。Luna での可否もスモークで確認。
4. **価格エントリ**: `data/pricing/model_pricing.toml` には Terra のみ登録済みで
   Luna のエントリがない。ない場合、集計の $/SR 列は空欄になる（エラーにはならない）。
   コスト列を出すには公式価格を確認して Luna のエントリを追加してから集計を再実行。
5. `.env` に `OPENAI_API_KEY` が設定されていること。

## 判断基準・次アクション

- 最良 effort が既存 validation 上位（Grok-4.20 86.0%、GPT-5.4 82.1% 等）に対して
  どこに位置するかを `FINAL_REPORT.md` に記録。
- 論文（Figure 4 / Table 2）へ追加する場合は、最良（または既定運用に採る）effort の
  統合JSONを `test/issues/2025-10-23_tsuge_md_validation_metrics/results/` にコピーし、
  CLAUDE.md「新規LLMモデル追加時の論文更新手順」に従う。
- effort 間で精度差が ±1pt 以内なら、コスト最小の effort を運用既定として推奨する。
