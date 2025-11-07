#!/usr/bin/env bash

set -Eeuo pipefail

# PRISMA-AI Thinking Ablation Experiment
# Goal: Reduce Claude thinking budget (30k -> 28k -> 24k) and verify metrics stability; also probe 4x and max for reference

ISSUE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

# Auto-activate venv if present
REPO_ROOT="$(cd "$ISSUE_DIR/../../.." && pwd)"
if [[ -f "$REPO_ROOT/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1090
  . "$REPO_ROOT/.venv/bin/activate" || true
fi
REPORT="$ISSUE_DIR/FINAL_REPORT.md"

MODEL="claude-opus-4-1-20250805"
DATASET="suda"
PAPER_IDS="Suda2025_15,Suda2025_17,Suda2025_18,Suda2025_5,Suda2025_7"

BASE_CMD=(python3 -m prisma_evaluator.cli.main run \
  -m "$MODEL" \
  --use-claude-native \
  -d "$DATASET" \
  --paper-ids "$PAPER_IDS" \
  -st eande-incontext \
  --section-mode off)

results_dir="results/evaluator_output"
mkdir -p "$results_dir"

write_header() {
  if [[ ! -f "$REPORT" ]]; then
    cat > "$REPORT" << 'EOF'
# 2025-09-12 実験レポート — Claude thinking アブレーション（E&E in‑context＋感度プレアンブル）

## 目的
- Claudeのthinking予算を段階的に削減しても、main_body_metricsの Acc/Prec/Rec/F1 が実質同等（±0.5pt以内）か検証

## 条件
- モデル: claude-opus-4-1-20250805（Native API, Function Calling）
- スキーマ: eande-incontext（PRISMA 2020 E&E全文 + 感度プレアンブル）
- 入力: section-mode=off（全文）
- データ: Suda固定5本（Suda2025_15, _17, _18, _5, _7）
- 既知の参照（前回）: main Acc 83.90 / Prec 86.36 / Rec 94.41 / F1 90.21

## 判定基準
- baseline対比で main Acc/Prec/Rec/F1 の差が±0.5pt以内 → 合格
- 0.5–1.0pt → 再試行（非決定性の可能性）
- >1.0pt → 不合格

## 実行ログと結果
EOF
  fi
}

latest_unified() {
  ls -1t "$results_dir"/*.json 2>/dev/null | head -n1 || true
}

append_metrics() {
  local label="$1"; shift
  local file="$1"; shift
  local metrics_json="$ISSUE_DIR/metrics_${label}.json"

  echo "\n### ${label}" >> "$REPORT"
  echo "- 統合JSON: \`$file\`" >> "$REPORT"

  # Extract metadata and main_body_metrics and append in compact form
  python - "$file" "$label" "$metrics_json" >> "$REPORT" << 'PY'
import json, sys, os
p=sys.argv[1]
label=sys.argv[2]
out_json=sys.argv[3]
with open(p, encoding='utf-8') as f:
    d=json.load(f)
mb=d.get('main_body_metrics') or {}
overall=d.get('overall_metrics') or {}
counts=mb.get('counts') or {}
pe=d.get('paper_evaluations') or []
meta=(pe[0].get('overall_metadata') if pe and isinstance(pe[0], dict) else {}) if isinstance(pe, list) else {}
think=meta.get('thinking_budget_tokens')
tmult=meta.get('thinking_multiplier')

def r(x):
    try:
        return round(float(x),2)
    except Exception:
        return x

print(f"- thinking_budget_tokens: {think} (multiplier: {tmult})")
if mb:
    print(f"- main: Acc {r(mb.get('accuracy'))}%, Prec {r(mb.get('precision'))}%, Recall {r(mb.get('recall'))}%, F1 {r(mb.get('f1_score'))}")
    if counts:
        print(f"  - counts: TP {counts.get('tp')}, TN {counts.get('tn')}, FP {counts.get('fp')}, FN {counts.get('fn')}")
elif overall:
    print(f"- overall: Acc {r(overall.get('accuracy'))}%, Prec {r(overall.get('precision'))}%, Recall {r(overall.get('recall'))}%, F1 {r(overall.get('f1_score'))}")

# Save compact metrics JSON for later diff summary
main_out={
  'accuracy': mb.get('accuracy'),
  'precision': mb.get('precision'),
  'recall': mb.get('recall'),
  'f1': mb.get('f1_score')
} if mb else None
payload={
  'label': label,
  'unified_path': p,
  'thinking_budget_tokens': think,
  'thinking_multiplier': tmult,
  'main': main_out,
  'overall': {
    'accuracy': overall.get('accuracy'),
    'precision': overall.get('precision'),
    'recall': overall.get('recall'),
    'f1': overall.get('f1_score')
  }
}
with open(out_json, 'w', encoding='utf-8') as o:
    json.dump(payload, o, ensure_ascii=False, indent=2)
PY
}

run_case() {
  local label="$1"; shift
  echo "[RUN] ${label} ..." >&2
  ("${BASE_CMD[@]}" "$@" --format "$label")
  # Capture latest unified file right after run
  local f
  f=$(latest_unified)
  if [[ -z "$f" ]]; then
    echo "[ERROR] Unified results not found." >&2
    exit 1
  fi
  # Append metrics summary to report
  append_metrics "$label" "$f"
  # Also save metrics-only summaries (for record)
  python3 -m prisma_evaluator.cli.main show-metrics --results-file "$f" || true
}

main() {
  write_header

  # 1) Baseline budget (implicit ~30000 tokens)
  run_case "budget_30000"

  # 2) 28000 tokens（multiplier 3x）
  run_case "budget_28000" --thinking-multiplier 3x

  # 3) 24000 tokens（multiplier 2x）
  run_case "budget_24000" --thinking-multiplier 2x

  # 4) 30000 tokens alt（multiplier 4x）
  run_case "budget_30000_alt" --thinking-multiplier 4x

  # 5) 31000 tokens（multiplier max）
  run_case "budget_31000" --thinking-multiplier max

  # Append delta summary vs baseline
  echo "\n## 差分サマリ（baseline=budget_30000, main_body_metrics）" >> "$REPORT"
  ISSUE_DIR="$ISSUE_DIR" python - >> "$REPORT" << 'PY'
import json, os
issue_dir=os.environ.get('ISSUE_DIR')
def load(label):
    p=os.path.join(issue_dir, f'metrics_{label}.json')
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return json.load(f)
base=load('budget_30000')
labels=['budget_28000','budget_24000','budget_30000_alt','budget_31000']
def r(x):
    try:
        return round(float(x),2)
    except Exception:
        return x
if not base or not base.get('main'):
    print('- baseline metrics missing; cannot compute diffs.')
else:
    b=base['main']
    for lab in labels:
        cur=load(lab)
        if not cur or not cur.get('main'):
            print(f"- {lab}: no metrics")
            continue
        m=cur['main']
        diffs={k: (float(m.get(k,0)) - float(b.get(k,0))) for k in ('accuracy','precision','recall','f1')}
        verdict='PASS' if all(abs(diffs[k])<=0.5 for k in diffs) else ('RE-RUN' if any(abs(diffs[k])<=1.0 for k in diffs) else 'FAIL')
        dd = ', '.join([f"{k}:{r(diffs[k]):+}" for k in ('accuracy','precision','recall','f1')])
        print(f"- {lab}: {dd} -> {verdict}")
PY

  echo "\n完了: $REPORT を更新しました。" >&2
}

main "$@"
