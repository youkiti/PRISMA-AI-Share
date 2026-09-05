# FINAL REPORT: Gemini 3.8 Flash thinking-level sweep（Tsuge 10論文 MD validation）

- 実施日: 2026-09-05
- モデル: `gemini-3.8-flash`（Gemini Direct API、`GeminiDirectEvaluator`）
- 条件: Tsuge PRISMA 10論文 / md / simple / eande-first / section-mode off / temperature 1.0
- 分母: 両水準とも530項目（main 410 + abstract 120）、`check_validation_counts.py` 全パス
- 記録モデル名: `cli_target_model_id` / `actual_model_id_to_use` / 各論文とも `gemini-3.8-flash` で一致

## 主要指標（Overall, 10論文）

| thinking level | Acc | Prec | Rec | F1 | Spec | κ | mean t/SR (s) | tokens | $/SR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| low | 81.13 | 81.67 | 85.52 | 83.55 | 75.54 | 0.6146 | 8.5 | 172,336 | 0.0185 |
| **medium** | **82.26** | 82.85 | 86.20 | 84.49 | 77.25 | 0.6380 | 22.5 | 229,078 | 0.0397 |

95%信頼区間（Wilson, 530項目）: low 81.13%（77.6–84.2）、medium 82.26%（78.8–85.3）。

内訳（correct/530）: low 430、medium 436。

コストは `data/pricing/model_pricing.toml` の Gemini 3.8 Flash エントリ
（入力 $0.75 / 出力 $3.75 per 1M、2026-12-31 までの暫定レート）による概算。
思考トークンは出力として課金されるため、`thoughts_token_count` を出力側に加算している
（medium は10論文で 56,879 思考トークン）。

## 所見

1. **medium が low を +1.13pt 上回る**（82.26 vs 81.13%）。κ も 0.6146 → 0.6380 と改善。
   Precision / Recall / Specificity すべてで medium が上回っており、一貫した改善。
   ただし信頼区間は大きく重なるため、10論文530項目では有意差とは言えない。
2. **コストは medium が約2.1倍、レイテンシは約2.6倍**（$0.0185 → $0.0397/SR、8.5 → 22.5 s/SR）。
   入力トークンは同一（153,895）で、差は思考トークン（low は実質0、medium は 56,879）。
3. Validation cohort 全体での位置づけ（Overall Acc）: Grok-4.20 86.0% > Grok-4-fast 83.0% >
   **Gemini 3.8 Flash (medium) 82.3%** > GPT-5.6 Terra / GPT-5.4 / Opus 4.5 82.1% >
   Gemini 3.1 Pro 81.5%。**Flash クラスで Pro クラスを上回り、全体3位**。
4. 価格性能比が良い。medium $0.040/SR は、上位の Grok-4.20 $0.067/SR の約6割、
   GPT-5.6 Terra $0.059/SR の約7割（いずれも思考／reasoning トークンを出力として課金した補正後の値）。
   low なら $0.019/SR とさらに安い。
5. Gemini Flash 系の推移: Gemini 3 Flash Preview 81.5%（2025-12-18）→ 3.8 Flash 82.3%。

## 推奨

**運用既定は `medium`（Acc 82.26%、$0.040/SR、22.5s/SR）**。
コストは倍でも絶対額が小さく、精度・κ・Spec すべてで low を上回るため。
大量処理でレイテンシとコストを優先する場合は `low`（81.13%、$0.019/SR、8.5s/SR）も実用範囲。

## 本実験で修正した実装上の問題

1. **`medium` が `HIGH` に丸められていた**（`prisma_evaluator/llm/gemini_direct_evaluator.py`）。
   導入当時のSDK enum が LOW/HIGH のみだったため `medium → HIGH` にマップされていた。
   2026-09-05 に現行の Gemini 3系（3.8 Flash / 3.1 Pro / 3 Flash preview）が `MEDIUM` を
   受理することを実機確認し、素通しするよう修正。修正前に実行していれば本スイープは
   low vs high の比較になっていた。
2. **思考トークンがコスト集計から抜けていた**。`candidates_token_count` に思考トークンが
   含まれないため、修正前の medium のコストは $0.018/SR と過小評価されていた（正: $0.040/SR）。
   `thoughts_token_count` を記録し、集計側で課金対象出力に加算するよう修正。

## 成果物

- 統合JSON（水準別、`cli_parameters.thinking_level` で識別）:
  - low: `results/md_gemini-3.8-flash_20260905_090619.json`
  - medium: `results/md_gemini-3.8-flash_20260905_091031.json`
- raw 3点セット（ai_evaluations / accuracy_summary / comparison_details）: `results/` 配下（水準別）
- 集計レポート: `reports/level_comparison.md` / `reports/level_comparison.csv`
- 実行ログ: `logs/run_<level>_20260905_*.log`、`logs/full_sweep_console.log`
- スモーク（1論文×2水準、全パス）: `results/smoke/`、`reports/smoke_level_comparison.md`

## 再現方法

```bash
bash test/issues/2026-09-05_tsuge10_md_gemini38_flash_level_sweep/scripts/run_level_sweep.sh --smoke
bash test/issues/2026-09-05_tsuge10_md_gemini38_flash_level_sweep/scripts/run_level_sweep.sh
```

## 論文への反映について

不要。論文は出版済みのため、新モデルの成果はリポジトリルート `README.md` の
ベンチマーク表の更新のみで運用する。
