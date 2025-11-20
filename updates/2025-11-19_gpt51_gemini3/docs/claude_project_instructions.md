# デバッグ
実装中に技術的に詰まったところやわからないところ、解決できないエラーなどがあればgpt5-mcpに英語で相談して。

Rのエラーの場合はr-acquaintに相談。

# Gemini モデル設定

## 利用可能なモデル
- `gemini-2.5-pro`: 安定版（デフォルト）
- `gemini-3-pro-preview`: 新しいプレビュー版

## モデル別デフォルト設定

### Gemini 3 (gemini-3-pro-preview)
- temperature: 1.0（Googleの推奨値、変更非推奨）
- thinking_level: high（デフォルト）
- thinking_levelオプション: low, medium, high

### Gemini 2.5 (gemini-2.5-pro)
- temperature: 0.0（決定論的）
- thinking_budget: -1（無制限）

## CLI使用例

```bash
# Gemini 3を使用（デフォルト設定）
python -m prisma_evaluator.cli.main run \
  --model gemini-2.5-pro \
  --gemini-model gemini-3-pro-preview \
  --num-papers 3

# Gemini 3 低レイテンシモード
python -m prisma_evaluator.cli.main run \
  --gemini-model gemini-3-pro-preview \
  --thinking-level low \
  --num-papers 3
```

## 注意事項
- `--thinking-budget`と`--thinking-level`は同時に使用できない
- Gemini 3ではtemperatureを1.0以外に設定するとループや性能低下が発生する可能性あり
- 詳細は `setup/gemini-cli-parameters.md` を参照