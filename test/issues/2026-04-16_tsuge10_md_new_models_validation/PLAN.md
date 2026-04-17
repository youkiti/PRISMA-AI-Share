# Tsuge Markdown Validation 追加実験 計画

- 起票日: 2026-04-16
- 対象: Tsuge 2025 PRISMA データセット 10 論文 × Markdown 形式チェックリスト
- 目的: 2026 年春以降に公開された新世代 LLM 5 モデルを validation cohort に追加し、Figure 4 / Table 2 / validation 本文を更新する
- 継承元: `test/issues/2025-10-23_tsuge_md_validation_metrics/`
- 出力方針: 生の `ai_evaluations_*.json` / `accuracy_summary_*.json` / `comparison_details_*.json` を残しつつ、Figure 4 と Table 2 が直接参照できる統合 JSON `md_<model>_<timestamp>.json` を本 issue と 2025-10-23 issue の両方に配置する

## 実行前提

現行の `prisma_evaluator.cli.main run` には `--use-claude-native`, `--order-mode`, `--section-mode` がない。したがって本 issue では CLI 直打ちを増やすのではなく、issue 配下の Python ランナーから `run_evaluation_pipeline()` を直接呼び出して共通設定を注入する。`show-metrics` は placeholder のため検証に使わない。paper-level 並列数は `PRISMA_EVALUATOR_MAX_WORKERS` ではなく `MAX_CONCURRENT_PAPERS=1` で制御する。

---

## 0. 対象モデル

| Provider | モデル ID | アクセス経路 | 現時点で必要な変更 | スモーク時の重点確認 |
|---|---|---|---|---|
| Anthropic | `claude-opus-4-6` | Anthropic Native | `prisma_evaluator/llm/claude_evaluator.py` の `CLAUDE_MODEL_DEFAULTS` 追加 | thinking budget / timeout |
| OpenAI | `gpt-5.4` | OpenAI Direct | repo-wide 変更は必須ではない。runner 側で `reasoning_effort='none'` を明示 | reasoning / unified JSON 構造 |
| Google | `gemini-3.1-pro-preview` | Gemini Direct | `--model` と `--gemini-model` を同じ ID で渡す。ダミー `gemini-2.5-pro` は使わない | metadata の model_id 一致 |
| xAI | `x-ai/grok-4.20` | OpenRouter | 必須変更なし。長文 truncation 時のみ `openrouter_evaluator.py` を調整 | tool calling / finish_reason |
| Qwen | `qwen/qwen3.6-plus` | OpenRouter | 必須変更なし。truncation 時のみ `OPENROUTER_MAX_TOKENS` か evaluator 側上限を調整 | tool calling / max_tokens |

補足:

- 5 モデルとも現行 repo には実績ファイルがないため、1 論文スモークを通すまで本実行に進まない。
- コスト集計を行うため、`data/pricing/model_pricing.toml` に 5 モデル分の pricing alias / rate を追加する。単価は実行時点の公式 pricing を確認してから反映する。

---

## 1. 本 issue のディレクトリ構成

```text
test/issues/2026-04-16_tsuge10_md_new_models_validation/
├── PLAN.md
├── README.md
├── FINAL_REPORT.md
├── data/
│   └── tsuge_selected10.txt
├── scripts/
│   ├── run_validation_model.py
│   ├── run_md_new_models.sh
│   ├── build_unified_validation_json.py
│   └── check_validation_counts.py
├── logs/
├── reports/
└── results/
```

運用ルール:

1. `data/tsuge_selected10.txt` は `test/issues/2025-10-23_tsuge_md_validation_metrics/data/tsuge_selected10.txt` を複製して固定する。
2. `results/` には raw 3 ファイルと統合 JSON の両方を残す。
3. 本 issue 完了後、統合 JSON のみを `test/issues/2025-10-23_tsuge_md_validation_metrics/results/` にコピーし、Figure 4 / validation CI / runtime-cost 集計の入力を更新する。

---

## 2. 必須変更

### 2.1 実装

| 区分 | ファイル | 変更内容 |
|---|---|---|
| コード | `prisma_evaluator/llm/claude_evaluator.py` | `CLAUDE_MODEL_DEFAULTS` に `claude-opus-4-6` を追加 |
| コード | `data/pricing/model_pricing.toml` | 5 新モデルの pricing entry または alias を追加 |
| 実験 | `test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_validation_model.py` | `run_evaluation_pipeline()` を直接呼ぶ issue-local ランナー |
| 実験 | `test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_md_new_models.sh` | 5 モデルをシリアル実行し、raw 出力を issue 配下へ移管 |
| 実験 | `test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/build_unified_validation_json.py` | raw 3 ファイルから `md_<model>_<timestamp>.json` を生成 |
| 実験 | `test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/check_validation_counts.py` | overall/main/abstract の分母を機械確認 |
| Figure | `paper/figures/make_validation_macro_chart.py` | `MODEL_DISPLAY_ORDER`, `clean_model_name()`, `valid_timestamps`, `figsize` を更新 |
| 集計 | `test/issues/2025-10-24_validation_ci_update/scripts/compute_validation_ci.py` | 表示名 override と order に 5 モデルを追加 |
| 集計 | `test/issues/2025-10-24_table2_runtime_cost/scripts/aggregate_table2_runtime_cost.py` | 新モデルの display name を追加 |

### 2.2 条件付き変更

| 条件 | ファイル | 対応 |
|---|---|---|
| `gpt-5.4` を repo 全体で `reasoning_effort='none'` にしたい | `prisma_evaluator/core/pipeline.py` | `gpt-5.1/5.2` と同等の autodetect 条件を追加 |
| `x-ai/grok-4.20` が `finish_reason=length` になる | `prisma_evaluator/llm/openrouter_evaluator.py` | Grok 系上限を増やすかモデル別分岐を追加 |
| `qwen/qwen3.6-plus` が tool call を返さない / truncation する | `prisma_evaluator/llm/openrouter_evaluator.py` | 出力上限または transforms 設定を追加 |
| Gemini 3.1 で per-paper `model_id` が別名になる | `prisma_evaluator/llm/gemini_direct_evaluator.py` | unified JSON 生成前に metadata を正規化 |

---

## 3. 実行仕様

### 3.1 共通環境

```bash
export STRUCTURED_DATA_SUBDIRS_OVERRIDE="supplement/data/tsuge2025/structured_prisma"
export ENABLE_SUDA=false
export ENABLE_TSUGE_PRISMA=true
export ENABLE_TSUGE_OTHER=false
export MAX_CONCURRENT_PAPERS=1
export ANNOTATION_DATA_PATH="${ANNOTATION_DATA_PATH:-$(pwd)/supplement/data}"
```

確認事項:

1. `supplement/data/tsuge2025/structured_prisma` が存在すること
2. `.env` は編集せず、`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY` が読み出せること
3. `venv/bin/python -m prisma_evaluator.cli.main validate-config` が通ること

### 3.2 ランナーの責務

`scripts/run_validation_model.py` は以下を担当する。

1. `data/tsuge_selected10.txt` を読み込み、10 論文の `paper_ids` を固定する
2. `run_evaluation_pipeline()` を直接呼ぶ
3. raw 3 ファイルの生成を確認する
4. `build_unified_validation_json.py` を呼び、統合 JSON を作る
5. `check_validation_counts.py` を呼び、分母と model_id を検証する

`gemini_params` の基準値:

```python
{
    "schema_type": "simple",
    "checklist_format": "md",
    "order_mode": "eande-first",
    "section_mode": "off",
}
```

補足:

- 現行 pipeline は `section_mode` を task 実行へ明示伝播していないが、`evaluate_single_paper_processing_task()` の既定値は `off` である。runner ではこの既定に依存しつつ、統合 JSON の `experiment_metadata.cli_parameters` には `section_mode: off` を明示記録する。
- Claude は `order_mode='eande-first'` を evaluator へ実際に渡す。その他モデルでは再現メタデータとして記録する。

### 3.3 モデル別の実行引数

| モデル | runner に渡す追加引数 | 備考 |
|---|---|---|
| `claude-opus-4-6` | `--model-id claude-opus-4-6` | Claude Native は model 名で自動選択される |
| `gpt-5.4` | `--model-id gpt-5.4 --gpt5-reasoning none` | repo-wide default は変えず、issue 実験では明示指定 |
| `gemini-3.1-pro-preview` | `--model-id gemini-3.1-pro-preview --gemini-model gemini-3.1-pro-preview --thinking-level high --temperature 1.0` | ダミー model ID を使わない |
| `x-ai/grok-4.20` | `--model-id x-ai/grok-4.20` | truncation 時のみ `OPENROUTER_MAX_TOKENS` を引き上げる |
| `qwen/qwen3.6-plus` | `--model-id qwen/qwen3.6-plus` | 初回は reasoning なし。失敗時のみ個別調整 |

参考コマンド:

```bash
PYTHONPATH=. \
venv/bin/python test/issues/2026-04-16_tsuge10_md_new_models_validation/scripts/run_validation_model.py \
  --model-id gpt-5.4 \
  --paper-ids-file test/issues/2026-04-16_tsuge10_md_new_models_validation/data/tsuge_selected10.txt \
  --run-label "md_gpt-5.4_$(date +%Y%m%d_%H%M%S)" \
  --gpt5-reasoning none
```

### 3.4 スモークテスト

本実行前に 5 モデルすべてで 1 論文スモークを行う。対象は `Tsuge2025_PRISMA2020_120` を優先する。

成功条件:

1. raw 3 ファイルが揃う
2. 統合 JSON が 1 本生成される
3. `overall_metrics.counts.total_comparable == 53`
4. `main_body_metrics.counts.total_comparable == 41`
5. `abstract_metrics.counts.total_comparable == 12`
6. `experiment_metadata.cli_parameters.target_model_id`, `actual_execution.model_id_to_use`, `paper_evaluations[].overall_metadata.model_id` が同じ最終 model ID を指す
7. `pricing_not_found:*` または `cost_not_calculated_missing_pricing` が出ない

スモーク失敗時の分岐:

1. Claude timeout: `MAX_CONCURRENT_PAPERS=1` を再確認し、必要なら thinking budget を縮小
2. OpenRouter truncation: `OPENROUTER_MAX_TOKENS` を引き上げ、必要なら evaluator 側分岐を追加
3. Gemini metadata drift: dummy model ID を使っていないか確認し、必要なら metadata 正規化を実装

---

## 4. 本実行と成果物整備

### 4.1 本実行

`scripts/run_md_new_models.sh` は以下の順で 5 モデルをシリアル実行する。

1. `claude-opus-4-6`
2. `gpt-5.4`
3. `gemini-3.1-pro-preview`
4. `x-ai/grok-4.20`
5. `qwen/qwen3.6-plus`

### 4.2 統合 JSON

`build_unified_validation_json.py` は raw 3 ファイルを入力とし、`UnifiedEvaluationResult` 相当の構造で以下を満たす統合 JSON を生成する。

1. `paper_evaluations[]` に `overall_metadata`, `evaluation_sets`, `metrics` を保持する
2. `overall_metrics`, `main_body_metrics`, `abstract_metrics`, `comparison_details` を統合する
3. `experiment_metadata.cli_parameters` に `target_model_id`, `target_format_type`, `schema_type`, `checklist_format`, `order_mode`, `section_mode` を記録する
4. 出力名は `md_<model_safe>_<timestamp>.json` とする

注意:

- 既存の `md_gpt-5.1_20251119_074132.json` のように `paper_evaluations[].overall_metadata` を欠く compact 形式は新規生成しない。
- runtime/cost 集計と Figure 4 は統合 JSON を直接読むため、ここが壊れると downstream がすべて崩れる。

### 4.3 分母検証

10 論文本実行後の期待値:

- overall: `530`
- main: `410`
- abstract: `120`

`show-metrics` は使わず、`check_validation_counts.py` か `jq` で直接検証する。

---

## 5. 既存 validation 成果物への反映

### 5.1 Figure / CI / runtime-cost

統合 JSON を `test/issues/2025-10-23_tsuge_md_validation_metrics/results/` にコピーした後、以下を再生成する。

```bash
venv/bin/python paper/figures/make_validation_macro_chart.py
venv/bin/python test/issues/2025-10-24_validation_ci_update/scripts/compute_validation_ci.py
venv/bin/python test/issues/2025-10-24_table2_runtime_cost/scripts/aggregate_table2_runtime_cost.py \
  --results-dir test/issues/2025-10-23_tsuge_md_validation_metrics/results \
  --output-json test/issues/2025-10-24_table2_runtime_cost/results/validation_runtime_cost.json \
  --output-csv test/issues/2025-10-24_table2_runtime_cost/results/validation_runtime_cost.csv
```

反映対象:

1. `paper/figures/make_validation_macro_chart.py`
2. `test/issues/2025-10-24_validation_ci_update/scripts/compute_validation_ci.py`
3. `test/issues/2025-10-24_table2_runtime_cost/scripts/aggregate_table2_runtime_cost.py`

### 5.2 原稿

原稿更新先は着手前に固定する。現時点では `manuscript/done/manuscript.md` をそのまま直接編集対象にせず、canonical manuscript を先に確定する。

原則:

1. canonical が `manuscript/manuscript.md` として整備済みなら、それを更新する
2. canonical が未整備なら、`manuscript/done/manuscript-for-submit.md` と `manuscript/done/manuscript.md` のどちらを source-of-truth にするか先に決めてから編集する
3. Table 2, validation 段落, Methods のモデル roster は Figure 4 / runtime-cost / CI と同じ model order と表記に揃える

---

## 6. リスク

1. 現行 CLI 前提の古い運用を流用すると、`--use-claude-native`, `--order-mode`, `--section-mode` で即失敗する。必ず issue-local runner を使う。
2. `MAX_CONCURRENT_PAPERS` を設定しないと OpenAI / Anthropic / OpenRouter で paper-level 並列が走る。`PRISMA_EVALUATOR_MAX_WORKERS` では抑止できない。
3. pricing entry を入れずに本実行すると Table 2 の cost が計算できない。
4. Gemini 系は `--model` と内部 `model_id` がずれると Figure 4 / Table 2 で provenance が壊れる。
5. 統合 JSON を compact 形式で作ると runtime/cost 集計が壊れる。
6. 既存 validation ディレクトリには旧 schema の JSON も混在しているため、`valid_timestamps` と unified JSON の filename を更新しないと Figure 4 が古い入力を拾う。

---

## 7. 着手チェックリスト

- [ ] `data/tsuge_selected10.txt` を 2025-10-23 issue から複製
- [ ] `supplement/data/tsuge2025/structured_prisma` の存在確認
- [ ] `CLAUDE_MODEL_DEFAULTS` に `claude-opus-4-6` を追加
- [ ] `data/pricing/model_pricing.toml` に 5 モデルを追加
- [ ] `scripts/run_validation_model.py` を作成
- [ ] `scripts/build_unified_validation_json.py` を作成
- [ ] `scripts/check_validation_counts.py` を作成
- [ ] 5 モデルの 1 論文スモークを完了
- [ ] 5 モデルの 10 論文本実行を完了
- [ ] 統合 JSON を本 issue と 2025-10-23 issue の両方へ配置
- [ ] Figure 4 / validation CI / runtime-cost を再生成
- [ ] manuscript の canonical target を固定してから本文更新
