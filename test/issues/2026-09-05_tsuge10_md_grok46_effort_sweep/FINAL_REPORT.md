# FINAL REPORT: Grok-4.6 reasoning-effort sweep（low / medium、Tsuge 10論文 MD validation）

- 実施日: 2026-09-05
- モデル: `x-ai/grok-4.6`（xAI ネイティブAPI直接、`XAIDirectEvaluator`。API上のモデル名は `grok-4.6`）
- 条件: Tsuge PRISMA 10論文 / md / simple / eande-first / section-mode off / max_completion_tokens 128,000
- 分母: 両effortとも530項目（main 410 + abstract 120）、`check_validation_counts.py` 全パス
- 記録モデル名: `cli_target_model_id` / `actual_model_id_to_use` / 各論文とも `x-ai/grok-4.6` で一致
- 第一指標: **recall（感度）**。取りこぼし（FN）の少なさを主眼に評価した

## 主要指標（Overall, 10論文 / 530項目）

| effort | Rec | Prec | F1 | Acc | Spec | κ | FN | FP | mean t/SR (s) | $/SR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **low** | **85.19** | 85.19 | 85.19 | 83.40 | 81.12 | 0.6630 | **44** | 44 | 59.2 | 0.0545 |
| medium | 83.84 | 88.30 | 86.01 | **84.72** | 85.84 | 0.6920 | 48 | 33 | 153.3 | 0.0897 |

95%信頼区間（Wilson）:
- Recall（陽性297項目ベース）: low 85.19%（80.7–88.8）、medium 83.84%（79.2–87.6）
- Accuracy（530項目ベース）: low 83.40%（80.0–86.3）、medium 84.72%（81.4–87.5）

内訳（correct/530）: low 442、medium 449。

### セクション別

| effort | main Rec | main Acc | main FN | abstract Rec | abstract Acc | abstract FN |
|---|---:|---:|---:|---:|---:|---:|
| low | 82.68 | 81.22 | 44 | 100.00 | 90.83 | 0 |
| medium | 81.10 | 82.20 | 48 | 100.00 | 93.33 | 0 |

FNはすべて本文（main）側で発生し、抄録側は両effortとも取りこぼしゼロ（43/43）。

## コスト計上

xAI は reasoning トークンを `output_tokens` の外で報告するため、
`prisma_evaluator.analysis.costs.calculate_run_cost` の `billed_output_tokens`
（= `max(output_tokens, total_tokens - input_tokens)`）で課金対象を復元している。

| effort | 入力 | 出力（報告値） | 出力（課金対象） | うち reasoning | $/SR |
|---|---:|---:|---:|---:|---:|
| low | 162,781 | 16,781 | 36,650 | 19,869 | 0.0545 |
| medium | 162,781 | 18,462 | 95,320 | 76,858 | 0.0897 |

素の `output_tokens` で計算すると low で約2.2倍、medium で約5.2倍コストを過小評価する。
料金は `data/pricing/model_pricing.toml` の `xai/grok-4-6`（prompt < 200k: $2.00 / $6.00 per MTok）。
キャッシュ入力割引は未反映のため、実請求はこれより安くなりうる。

## 所見

1. **recall優先なら `low` が最良**。low 85.19% / FN 44 に対し medium は 83.84% / FN 48 で、
   effort を上げると取りこぼしが4件増える。信頼区間は大きく重なるので有意差とは言えないが、
   少なくとも「effort を上げれば感度が上がる」という関係は成り立たない。
2. **effort の効き方は Specificity 側**。low → medium で Spec 81.12 → 85.84%（FP 44 → 33）、
   Precision 85.19 → 88.30% と改善し、その分 Recall が下がる。
   つまり medium は判定が保守的になる方向に動いており、感度と特異度のトレードオフになっている。
3. **Accuracy と κ は medium が上**（84.72% / 0.6920 対 83.40% / 0.6630）。
   FP削減幅（-11）が FN増加幅（+4）を上回るため。
   指標の優先順位で推奨設定が割れるケースで、accuracy基準なら medium、recall基準なら low。
4. **コストとレイテンシは low が明確に有利**。medium は reasoning トークンが3.9倍
   （19,869 → 76,858）に膨らみ、$/SR 1.6倍、処理時間 2.6倍。
   recall が下がるうえに高く遅いので、感度重視の運用で medium を選ぶ理由はない。
5. **同一ベンダーの Grok-4.20 には及ばない**。Grok-4.20 は Acc 86.04% / Recall 89.23% /
   FN 32 / 55.2s/SR / $0.0665/SR で、精度・感度・速度のすべてで Grok-4.6 を上回る
   （コストのみ Grok-4.6 low が $0.0545/SR とわずかに安い）。
   cohort 全体でも Recall 89.23% の Grok-4.20 が依然トップ。
6. それでも Grok-4.6 の Recall 85.19% は cohort 上位グループで、
   Gemini 3.8 Flash medium（86.20%）とほぼ同水準、GPT-6 Astra（77.44%）を大きく上回る。

## 推奨

- **感度（recall）優先の運用: `--gpt5-reasoning low`**（Recall 85.19%、FN 44、$0.0545/SR、59.2s/SR）。
  xAI既定の high は本スイープでは未検証だが、low → medium で recall が下がる方向であることから、
  感度目的でさらに effort を上げる合理性は低い。
- accuracy / κ を優先する場合のみ `medium`（84.72%、κ 0.6920）。ただしコスト1.6倍・時間2.6倍。
- xAIモデルで感度を最優先するなら、Grok-4.6 ではなく **Grok-4.20**（Recall 89.23%、FN 32）が第一候補。

## 成果物

- 統合JSON（effort別、`cli_parameters.gpt5_reasoning` で識別）: `results/md_x-ai_grok-4.6_*.json`
  - low: `results/md_x-ai_grok-4.6_20260905_110737.json`
  - medium: `results/md_x-ai_grok-4.6_20260905_113311.json`
- raw 3点セット（ai_evaluations / accuracy_summary / comparison_details）: `results/` 配下（effort別）
- 集計レポート: `reports/effort_comparison.md` / `reports/effort_comparison.csv`
- 実行ログ: `logs/run_<effort>_20260905_*.log`、`logs/full_sweep_console.log`
- スモーク（1論文×2 effort、全パス）: `results/smoke/`、`reports/smoke_effort_comparison.md`

## 再現方法

```bash
bash test/issues/2026-09-05_tsuge10_md_grok46_effort_sweep/scripts/run_effort_sweep.sh --smoke
bash test/issues/2026-09-05_tsuge10_md_grok46_effort_sweep/scripts/run_effort_sweep.sh
```

## 論文への反映について

不要。論文は出版済みのため、新モデルの成果はリポジトリルート `README.md` の
ベンチマーク表の更新のみで運用する。
