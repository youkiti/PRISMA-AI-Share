**Cohort**: tsuge_md_validation_10 (10 systematic reviews, 530 comparable item decisions = 410 main-body + 120 abstract per cohort). Schema: `simple`. Checklist format: `md`. Reference labels: two-rater consensus PRISMA 2020 from the source publications.

| Rank | Model | Provider | Accuracy % (95% CI) | Sens % | Spec % | F1 % | Cohen κ | Cost / SR | Time / SR (sec) | Schema | Notes |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 1 | Grok-4.20 | xAI | 86.04 (82.83-88.73) | 89.23 | 81.97 | 87.75 | 0.715 | $0.017 | 53.5 | simple | Routed via xAI direct (OpenRouter upstream times out on long tool calls). |
| 2 | Grok-4-fast | xAI (via OpenRouter) | 83.02 (79.59-85.98) | 89.56 | 74.68 | 85.53 | 0.651 | $0.005 | 27.0 | simple |  |
| 3 | GPT-5.4 | OpenAI | 82.08 (78.58-85.11) | 86.87 | 75.97 | 84.45 | 0.633 | $0.060 | 31.6 | simple |  |
| 4 | Gemini 3 Flash | Google | 81.51 (77.98-84.58) | 92.26 | 60.77 | 86.79 | 0.563 | $0.049 | 24.0 | simple |  |
| 5 | Gemini 3.1 Pro | Google | 81.51 (77.98-84.58) | 90.24 | 70.39 | 84.54 | 0.618 | $0.055 | 90.4 | simple |  |
| 6 | Gemini 3 Pro | Google | 81.32 (77.78-84.41) | 91.25 | 68.67 | 84.56 | 0.612 | - | 113.0 | simple | (cost_unavailable:no_input_output_split) |
| 7 | Qwen3.6 Plus | Alibaba (via OpenRouter) | 81.32 (77.78-84.41) | 87.54 | 73.39 | 84.01 | 0.616 | $0.050 | 245.3 | simple | (pricing_flag:variable_rate) |
| 8 | Grok-4 | xAI (via OpenRouter) | 81.13 (77.58-84.23) | 86.20 | 74.68 | 83.66 | 0.614 | $0.111 | 117.8 | simple |  |
| 9 | Grok-4.1-fast | xAI (via OpenRouter) | 81.13 (77.58-84.23) | 88.25 | 67.40 | 86.03 | 0.570 | $0.006 | 58.3 | simple |  |
| 10 | GPT-OSS-120B | OpenAI (via OpenRouter) | 80.94 (77.38-84.06) | 89.56 | 69.96 | 84.04 | 0.606 | $0.002 | 42.8 | simple |  |
| 11 | DeepSeek V4 Pro | DeepSeek (via OpenRouter) | 80.94 (77.38-84.06) | 76.43 | 86.70 | 81.80 | 0.620 | $0.053 | 177.3 | simple | Tool calling via tool_choice=auto (forced rejected upstream); see test/issues/2026-04-25_deepseek_v4_pro_openrouter_capability_check/ for capability probes. |
| 12 | GPT-5.1 | OpenAI | 80.19 (76.58-83.36) | 87.21 | 71.24 | 83.15 | 0.592 | - | 140.4 | simple | (cost_unavailable:no_input_output_split) |
| 13 | Claude Opus 4.7 | Anthropic | 79.81 (76.18-83.01) | 94.28 | 61.37 | 83.96 | 0.576 | $0.183 | 39.2 | simple | Effort level chosen by Tsuge sweep (low/medium/high/xhigh/max); see test/issues/2026-04-17_tsuge10_md_claude47_effort_sweep/. |
| 14 | Qwen3-235B | Alibaba (via OpenRouter) | 79.43 (75.79-82.66) | 93.94 | 60.94 | 83.66 | 0.568 | $0.003 | 53.7 | simple |  |
| 15 | Gemini 2.5 Pro | Google | 79.06 (75.39-82.31) | 84.51 | 72.10 | 81.89 | 0.571 | $0.045 | 76.4 | simple |  |
| 16 | Claude Opus 4.1 | Anthropic | 79.06 (75.39-82.31) | 82.49 | 74.68 | 81.53 | 0.574 | $0.562 | 122.4 | simple |  |
| 17 | GPT-5 | OpenAI | 78.11 (74.40-81.42) | 87.21 | 66.52 | 81.70 | 0.547 | $0.031 | 18.4 | simple |  |
| 18 | Qwen3-Max | Alibaba (via OpenRouter) | 77.92 (74.20-81.25) | 95.96 | 54.94 | 82.97 | 0.532 | $0.027 | 56.1 | simple | 32k output cap; reasoning disabled (provider does not expose it). (pricing_flag:variable_rate) |
| 19 | Kimi K2.6 | Moonshot | 77.55 (73.80-80.89) | 71.04 | 85.84 | 78.00 | 0.555 | $0.048 | 522.9 | simple | Routed via Moonshot direct API; OpenRouter routes hung on long tool calls (see test/issues/2026-04-22_kimi_k2_6_openrouter_structured_output/). |
| 20 | Claude Sonnet 4.5 | Anthropic | 72.64 (68.69-76.26) | 74.75 | 69.96 | 75.38 | 0.446 | $0.163 | 207.8 | simple |  |
| 21 | GPT-4o | OpenAI | 68.49 (64.41-72.30) | 96.97 | 32.19 | 77.52 | 0.313 | $0.043 | 31.8 | simple |  |
