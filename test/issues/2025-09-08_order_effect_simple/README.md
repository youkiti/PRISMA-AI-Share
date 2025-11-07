# 2025-09-08 — Order Effect (simple schema)

- 目的: simpleスキーマ固定のまま、入力順序のみ（論文→E&E vs E&E→論文）で精度影響をA/B比較する。
- 追加検証: A/Bのいいとこ取り（post-hoc ensemble）でスコア改善が得られるか（intersection/union/targeted-union）。

## 条件
- モデル: Claude Opus 4.1（Native API）
- スキーマ: `-st simple`
- データ: Suda2025（5本固定）`Suda2025_15,17,18,5,7`
- セクション: `--section-mode off`
- 仲裁: なし（`--dual-order`/`--arbitrate-opus` 未使用）

## 実行コマンド（A/B）
- A: 論文→E&E
  ```bash
  .venv/bin/python -m prisma_evaluator.cli.main run \
    -m claude-opus-4-1-20250805 --use-claude-native \
    -d suda --paper-ids "Suda2025_15,Suda2025_17,Suda2025_18,Suda2025_5,Suda2025_7" \
    -st simple --order-mode paper-first --log-level INFO
  ```
- B: E&E→論文
  ```bash
  .venv/bin/python -m prisma_evaluator.cli.main run \
    -m claude-opus-4-1-20250805 --use-claude-native \
    -d suda --paper-ids "Suda2025_15,Suda2025_17,Suda2025_18,Suda2025_5,Suda2025_7" \
    -st simple --order-mode eande-first --log-level INFO
  ```

## いいとこ取り（アンサンブル）
- スクリプト: `analysis/ensemble_ab.py`
- ポリシー:
  - `intersection`: 両方YESの時だけYES（Precision↑/Recall↓）
  - `union`: どちらかYESならYES（Recall↑/Precision↓）
  - `targeted-union`: 既知難所（7,10b,13e,13f,14,21,27,16b,24c）のみUnion、他はB優先

## 成果物
- 実行直後の統合結果: `results/evaluator_output/YYYYMMDD_HHMMSS.json`
- 集計: `results/evaluator_output/accuracy_summary_metrics_only_from_ensemble_<policy>_YYYYMMDD_HHMMSS.json`
- 比較詳細: `results/evaluator_output/comparison_details_metrics_only_from_ensemble_<policy>_YYYYMMDD_HHMMSS.json`

