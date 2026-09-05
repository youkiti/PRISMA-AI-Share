# FINAL REPORT: GPT-6 Astra reasoning-effort sweep（Tsuge 10論文 MD validation）

- 実施日: 2026-09-05
- モデル: `gpt-6-astra`（OpenAI Responses API 直接、GPT5Evaluator）
- 条件: Tsuge PRISMA 10論文 / md / simple / eande-first / section-mode off / verbosity low / reasoning_mode 未指定
- 分母: 全effortで530項目（main 410 + abstract 120）、`check_validation_counts.py` 全パス
- 記録モデル名: `cli_target_model_id` / `actual_model_id_to_use` / 各論文とも `gpt-6-astra` で一致

## 主要指標（Overall, 10論文）

| effort | Acc | Prec | Rec | F1 | Spec | κ | mean t/SR (s) | tokens | $/SR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| low | 75.28 | 78.23 | 77.44 | 77.83 | 72.53 | 0.4990 | 30.3 | 157,887 | 0.2470 |
| medium | 75.85 | 78.45 | 78.45 | 78.45 | 72.53 | 0.5098 | 39.9 | 164,277 | 0.2790 |
| **high** | **76.42** | 79.86 | 77.44 | 78.63 | 75.11 | 0.5233 | 99.2 | 204,093 | 0.4781 |

95%信頼区間（Wilson, 530項目）: low 75.28%（71.4–78.8）、medium 75.85%（72.0–79.3）、high 76.42%（72.6–79.8）。

内訳（correct/530）: low 399、medium 402、high 405。

コストは `data/pricing/model_pricing.toml` の Astra エントリ（入力 $10.00 / 出力 $50.00 per 1M、
2026-09 に developers.openai.com で確認）による short-context 概算。
OpenAI は reasoning トークンを `output_tokens` に含めて返すため、追加補正は不要
（effort に応じ出力が 1,790 → 2,206 → 6,264 tokens と増加することを実測で確認）。

`none` は使用不可。実機でも
`Unsupported value: 'none' is not supported with the 'gpt-6-astra' model.
Supported values are: 'low', 'medium', 'high', ...` が返る。

## 所見

1. **effort を上げるほど精度は単調に改善するが、その幅は小さい**（75.28 → 75.85 → 76.42%、
   low→high で +1.14pt）。信頼区間はほぼ完全に重なり、10論文530項目では差とは言えない。
   一方コストは 1.9倍、レイテンシは 3.3倍になる。
2. **このタスクでは既存モデルに対して明確に劣る**。フラッグシップかつ最高価格
   （$10/$50 per MTok）でありながら、最良の high 76.42% は
   Kimi K2.6 77.55%、Qwen3-Max 77.92% を下回り、validation cohort で下位グループに入る。
3. 誤りの内訳を見ると **False Negative が多い**（high で FN 67 / FP 58）。
   Recall 77.44% は上位モデル（Gemini 3.8 Flash medium 86.20%）より約9pt低く、
   「記載あり」を取りこぼす傾向が精度を押し下げている。effort を上げても Recall は改善せず
   （low/high とも 77.44%）、伸びているのは Specificity（72.53 → 75.11%）のみ。
4. GPT-5.6 シリーズの傾向（`2026-07-10_tsuge10_md_gpt56_*`）と整合的。
   Terra は `none` が最良（82.08%）で effort を上げると悪化し、
   最上位・最高価格の Sol も 80.38% と Terra に劣った。
   **OpenAI系はこのタスクで「高価格・高 effort ほど良い」とはならない**傾向が続いている。
5. コスト効率は cohort 内で最も悪い。Astra high $0.478/SR に対し、
   より高精度な Gemini 3.8 Flash (medium) は 82.26% で $0.040/SR（約1/12）。

## 推奨

**このタスクでは GPT-6 Astra を採用する理由がない。**
OpenAI系を使うなら GPT-5.6 Terra（`none`、82.08%、$0.059/SR、11.8s/SR）が
精度・コスト・速度のすべてで上回る。
比較目的で Astra を回す場合の推奨設定は `high`（76.42%、$0.478/SR、99.2s/SR）だが、
effort間の差は誤差範囲であり、コスト優先なら `low` で実質同等。

## 成果物

- 統合JSON（effort別、`cli_parameters.gpt5_reasoning` で識別）: `results/md_gpt-6-astra_*.json`
- raw 3点セット（ai_evaluations / accuracy_summary / comparison_details）: `results/` 配下（effort別）
- 集計レポート: `reports/effort_comparison.md` / `reports/effort_comparison.csv`
- 実行ログ: `logs/run_<effort>_20260905_*.log`、`logs/full_sweep_console.log`
- スモーク（1論文×3 effort、全パス）: `results/smoke/`、`reports/smoke_effort_comparison.md`

## 再現方法

```bash
bash test/issues/2026-09-05_tsuge10_md_gpt6_astra_effort_sweep/scripts/run_effort_sweep.sh --smoke
bash test/issues/2026-09-05_tsuge10_md_gpt6_astra_effort_sweep/scripts/run_effort_sweep.sh
```

## 論文への反映について

不要。論文は出版済みのため、新モデルの成果はリポジトリルート `README.md` の
ベンチマーク表の更新のみで運用する。
