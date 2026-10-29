#!/usr/bin/env bash
# scripts/pipeline.sh — 单卦全流程 orchestrator。
#
# 用法：
#   ./scripts/pipeline.sh 37 jiaren
#
# 它会按 AGENTS.md 的 DAG 顺序跑能自动化的步骤，遇到必须人工的点就
# 停下并打印下一步该做什么。不会越过任何红线：不写 inputs/human/、
# 不把 verification_status 自动置 verified、不走到 PUBLISHED。
#
# 要跑『Agent 自己做』的那些中间产出（义理研究、艺术 Brief、G2、G3、
# 义理审查），请在 Claude Code 会话里用 Task tool 调三个子 Agent：
#   - classics-researcher
#   - ink-art-director
#   - independent-verifier
# 本脚本不替你调它们；它只跑确定性的 CLI 命令。

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "用法: $0 <hexagram_id> <slug>" >&2
  exit 2
fi

ID_RAW="$1"
SLUG="$2"
ID=$(printf "%02d" "$ID_RAW")
REPO=$(cd "$(dirname "$0")/.." && pwd)
GXWD="$REPO/.venv/bin/gxwd"
PROJ="$REPO/projects/${ID}-${SLUG}"
INPUT_CSV="$REPO/inputs/human/${ID}-${SLUG}-canonical.csv"
PREFILL_CSV="$REPO/output/canonical-input-prefilled/${ID}-${SLUG}-canonical.csv"

say() { printf '\n\033[1;36m[%s]\033[0m %s\n' "$1" "$2"; }
hint() { printf '    \033[0;33m→\033[0m %s\n' "$1"; }

say "step 1" "读取主数据"
"$GXWD" hexagram show "$ID_RAW" | sed 's/^/    /'

say "step 2" "G1 卦符二进制门禁"
mkdir -p "$PROJ/reviews"
"$GXWD" validate binary "$ID_RAW" --json --out "$PROJ/reviews/g1-binary-validation.json"
hint "报告: $PROJ/reviews/g1-binary-validation.json"

say "step 3" "L0 经文录入（人工点）"
if [ -f "$INPUT_CSV" ]; then
  hint "找到 $INPUT_CSV，跑 import-and-gate.sh"
  "$REPO/scripts/import-and-gate.sh" "$ID_RAW" "$SLUG"
elif [ -f "$PREFILL_CSV" ]; then
  cat <<EOF
    尚未录入。预填 CSV 已就位，主编需要：
      cp "$PREFILL_CSV" "$INPUT_CSV"
      \$EDITOR "$INPUT_CSV"
      # 填 page 列、改 verification_status=verified
      ./scripts/import-and-gate.sh $ID_RAW $SLUG
    之后重跑本脚本。
EOF
  exit 0
else
  echo "⚠ 既无 $INPUT_CSV 也无 $PREFILL_CSV；检查卦序和 slug" >&2
  exit 1
fi

say "step 4" "义理研究（Agent 点）"
if [ -f "$PROJ/research/interpretation.md" ]; then
  hint "已有研究稿: $PROJ/research/interpretation.md"
else
  cat <<EOF
    尚无研究稿。在 Claude Code 会话里跑：
      Task(subagent_type: classics-researcher,
           description: '第 $ID_RAW 卦 $SLUG 研究稿',
           prompt: '按 .claude/skills/yao-interpretation/SKILL.md 产出 projects/${ID}-${SLUG}/research/interpretation.md + yao-cases.json + business-philosophy.md')
    之后重跑本脚本。
EOF
  exit 0
fi

say "step 5" "义理审查（Agent 点，独立实例）"
INTERP_REVIEW="$PROJ/reviews/interpretation-review.json"
if [ -f "$INTERP_REVIEW" ]; then
  hint "已有审查: $INTERP_REVIEW"
else
  cat <<EOF
    尚无义理审查。在 Claude Code 会话里跑：
      Task(subagent_type: independent-verifier,
           description: '第 $ID_RAW 卦义理审查',
           prompt: '对 projects/${ID}-${SLUG}/research/interpretation.md 独立审查，产出 $INTERP_REVIEW，result: pass|fail')
    之后重跑本脚本。
EOF
  exit 0
fi

say "step 6" "艺术 Brief（Agent 点，H3 授权后才启动）"
if [ -f "$PROJ/art/art-brief.md" ]; then
  hint "已有艺术 Brief: $PROJ/art/art-brief.md"
else
  cat <<EOF
    WP9 艺术 Brief 冻结中。启动条件：H3 完成（图像模型 + 书法/印章授权，
    见 docs/image-and-licensing-decisions.md）。之后在 Claude Code 会话跑：
      Task(subagent_type: ink-art-director, ...)
    本脚本到此停止。
EOF
  exit 0
fi

say "step 7" "三层合成"
MASTER="$PROJ/art/master.png"
if [ ! -f "$MASTER" ]; then
  echo "    无主图 $MASTER；WP9 冻结中无法合成。" >&2
  exit 0
fi
"$GXWD" compose "$ID_RAW" --master "$MASTER" --out "$PROJ/layout"

say "step 8" "G2 + G3（Agent 点）"
cat <<EOF
    在 Claude Code 会话里跑两次 Task(subagent_type: independent-verifier)：
      - G2 卦符与画面 → $PROJ/reviews/g2-visual.json
      - G3 出版与溯源 → $PROJ/reviews/g3-publication.json
EOF

say "step 9" "人工终审 + publish request"
cat <<EOF
    由人工总主编查看全部产出后，在终端运行：
      $GXWD publish request $ID_RAW \\
        --approved-by <approver_id> --approved-at \$(date -u +%Y-%m-%dT%H:%M:%SZ)
    publisher 会重算全部门禁，任一失败即拒。
EOF
