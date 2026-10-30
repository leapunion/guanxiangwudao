#!/usr/bin/env bash
# autopilot-all.sh — 治理 V2 下批量跑全部 64 卦（或子集）到 PUBLISHED。
#
# 用法：
#   ./scripts/autopilot-all.sh              # 跑 1..64
#   ./scripts/autopilot-all.sh 1 8          # 跑 1..8（试点）
#   ./scripts/autopilot-all.sh --dry-run    # 全部模拟，不改任何文件
#
# 每一卦都走 scripts/autopilot.py 的 5 步 pipeline。失败则停止并打印
# 已完成的卦清单。

set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
PY="$REPO/.venv/bin/python"
GXWD="$REPO/.venv/bin/gxwd"

DRY=""
START=1
END=64

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY="--dry-run"; shift ;;
    [0-9]*)
      START="$1"; shift
      if [ $# -gt 0 ] && [[ "$1" =~ ^[0-9]+$ ]]; then
        END="$1"; shift
      else
        END="$START"
      fi
      ;;
    *) echo "未知参数: $1" >&2; exit 2 ;;
  esac
done

ok=0; fail_list=()

for id in $(seq "$START" "$END"); do
  slug=$("$PY" -c "from gxwd.domain import get_hexagram; print(get_hexagram($id)['slug'])")
  echo
  echo "═══ 第 $id 卦 $slug ═══"
  if "$PY" "$REPO/scripts/autopilot.py" "$id" "$slug" $DRY; then
    ok=$((ok + 1))
  else
    fail_list+=("$id-$slug")
    echo "✗ 第 $id 卦失败，停止批量" >&2
    break
  fi
done

echo
echo "═══ 批量汇总 ═══"
echo "成功: $ok / $((END - START + 1))"
if [ ${#fail_list[@]} -gt 0 ]; then
  printf '失败:\n'; printf '  - %s\n' "${fail_list[@]}"
  exit 1
fi

if [ -z "$DRY" ]; then
  echo
  "$GXWD" status | tail -15
fi
