# GPT-5.1 & Gemini 3 Pro Support Update

**Export Date**: 2025-11-19
**Purpose**: GPT-5.1およびGemini 3 Proモデルサポートの追加修正と評価結果

---

## 概要

PRISMA-AIに以下の新機能を追加しました：

1. **GPT-5.1サポート** - reasoning_effort自動設定（デフォルト: none）
2. **Gemini 3 Proサポート** - temperature/thinking_level自動設定

---

## 評価結果サマリ

### GPT-5.1 (Tsuge 10論文, Markdown)

| 指標 | 値 |
|------|-----|
| **Overall Accuracy** | 80.19% (425/530) |
| **Sensitivity** | 87.21% |
| **Specificity** | 71.24% |
| **Cohen's Kappa** | 0.592 |
| **処理時間** | ~127秒/10論文 |

### Gemini 3 Pro (Tsuge 10論文, Markdown)

| 指標 | 値 |
|------|-----|
| **Overall Accuracy** | 81.32% (431/530) |
| **Sensitivity** | 91.25% |
| **Specificity** | 68.67% |
| **Cohen's Kappa** | 0.61 |

---

## ディレクトリ構成

```
2025-11-19_gpt51_gemini3/
├── README.md                    # このファイル
├── code/
│   └── prisma_evaluator/
│       ├── llm/
│       │   ├── gpt5_evaluator.py        # GPT-5.1 reasoning handling
│       │   └── gemini_direct_evaluator.py # Gemini 3 detection
│       ├── core/
│       │   └── pipeline.py              # GPT-5.1自動検出ロジック
│       ├── cli/
│       │   └── main.py                  # --gpt5-reasoning, --gemini-model, --thinking-level
│       └── config/
│           ├── settings.py              # デフォルト設定
│           └── default_settings.toml    # Geminiモデルドキュメント
├── docs/
│   ├── gemini-cli-parameters.md         # Geminiパラメータ完全ガイド
│   └── claude_project_instructions.md   # .claude/CLAUDE.md
├── results/
│   ├── gpt5_1/
│   │   ├── ai_evaluations_gpt-5.1_md_20251119_*.json
│   │   ├── accuracy_summary_gpt-5.1_md_20251119_*.json
│   │   └── comparison_details_gpt-5.1_md_20251119_*.json
│   └── gemini3/
│       ├── ai_evaluations_gemini-2.5-pro_md_20251119_070126.json
│       └── accuracy_summary_gemini-2.5-pro_md_20251119_070126.json
└── test_issues/
    ├── 2025-11-18_gemini3_pro_suda_tsuge_md_eval/
    ├── 2025-11-19_gpt5_1_thinking_none_tsuge10_md_eval/
    └── 2025-11-19_gpt5_1_thinking_high_tsuge10_md_eval/
```

---

## 主な変更点

### GPT-5.1対応

**自動検出ロジック** (`pipeline.py:167-172`):
```python
autodetect_gpt51 = "gpt-5.1" in model_id_to_use.lower()
if autodetect_gpt51 and not cli_overrides_reasoning:
    evaluator_kwargs['reasoning_effort'] = 'none'
```

**CLI使用例**:
```bash
# デフォルト（reasoning=none, 高速）
python -m prisma_evaluator.cli.main run --model gpt-5.1 --num-papers 5

# reasoning有効化
python -m prisma_evaluator.cli.main run --model gpt-5.1 --gpt5-reasoning minimal
```

### Gemini 3 Pro対応

**モデル検出とデフォルト設定** (`gemini_direct_evaluator.py:75-84`):
```python
is_gemini3 = "gemini-3" in model.lower()
if temperature is None:
    self.temperature = 1.0 if is_gemini3 else 0.0

if is_gemini3 and thinking_level is None:
    self.thinking_level = "high"
```

**CLI使用例**:
```bash
# デフォルト（temperature=1.0, thinking_level=high）
python -m prisma_evaluator.cli.main run \
  --model gemini-2.5-pro \
  --gemini-model gemini-3-pro-preview \
  --num-papers 3

# 低レイテンシモード
python -m prisma_evaluator.cli.main run \
  --gemini-model gemini-3-pro-preview \
  --thinking-level low
```

---

## 技術的注意事項

### GPT-5.1
- `reasoning_effort=none`がデフォルト（GPT-5は`minimal`）
- CLI `--gpt5-reasoning`または環境変数`GPT5_REASONING_EFFORT`でオーバーライド可能

### Gemini 3
- `temperature`は必ず1.0（Googleの推奨、変更すると性能低下）
- `--thinking-budget`と`--thinking-level`は排他的（同時使用不可）
- `google.genai` SDKを使用（`google-generativeai`ではない）

---

## 関連ドキュメント

- [gemini-cli-parameters.md](docs/gemini-cli-parameters.md) - 完全なGeminiパラメータリファレンス
- [claude_project_instructions.md](docs/claude_project_instructions.md) - プロジェクト設定ガイド

---

## 前回エクスポートからの差分

**前回エクスポート**: 2025-11-07
**今回エクスポート**: 2025-11-19

主な追加:
- GPT-5.1モデル自動検出とreasoning_effort制御
- Gemini 3 Proモデル検出とtemperature/thinking_level制御
- 新規ドキュメント: gemini-cli-parameters.md (212行)
- 10論文での評価結果（両モデル）
