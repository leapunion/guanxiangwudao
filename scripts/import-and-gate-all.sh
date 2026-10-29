#!/usr/bin/env bash
# import-and-gate-all.sh：批量版 import-and-gate。
#
# 扫 inputs/human/*.csv，对每个按文件名解析 <id>-<slug>，依次跑
#   gxwd texts import … + gxwd validate binary <id> --json --out …
#
# 不改 CSV；不触碰 inputs/human/ 以外的目录（除 data/canonical-texts.json
# 由 texts import 更新、projects/<id>-<slug>/reviews/g1-*.json 由
# validate binary 更新）。
#
# 用法：
#   ./scripts/import-and-gate-all.sh
#
# 单卦版入口是 scripts/import-and-gate.sh。

set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
GXWD="$REPO_ROOT/.venv/bin/gxwd"
INPUTS="$REPO_ROOT/inputs/human"

if [ ! -x "$GXWD" ]; then
  echo "gxwd 不可执行：$GXWD（先 \`uv pip install -e .\`）" >&2
  exit 1
fi

if [ ! -d "$INPUTS" ]; then
  echo "inputs/human/ 不存在。先把 templates/canonical-input/ 下的 CSV 模板复制过去并由主编填好。" >&2
  exit 1
fi

shopt -s nullglob
csvs=( "$INPUTS"/*.csv )
shopt -u nullglob

if [ "${#csvs[@]}" -eq 0 ]; then
  echo "inputs/human/ 下没有 .csv 文件；无事可做。" >&2
  exit 0
fi

ok=0; skip=0; fail=0
failed_list=()

for csv in "${csvs[@]}"; do
  base=$(basename "$csv" .csv)
  # 文件名格式：<id:02d>-<slug>-canonical
  if [[ ! "$base" =~ ^([0-9]{2})-([a-z]+)-canonical$ ]]; then
    echo "⚠ 跳过（文件名不匹配 <id:02d>-<slug>-canonical.csv）：$csv" >&2
    skip=$((skip + 1))
    continue
  fi
  id_padded="${BASH_REMATCH[1]}"
  slug="${BASH_REMATCH[2]}"
  id_num=$((10#$id_padded))

  echo "─── 第 $id_padded 卦 $slug ───"
  if "$REPO_ROOT/scripts/import-and-gate.sh" "$id_num" "$slug"; then
    ok=$((ok + 1))
  else
    fail=$((fail + 1))
    failed_list+=("$id_padded-$slug")
  fi
done

echo
echo "═══ 批量导入汇总 ═══"
echo "成功: $ok    跳过: $skip    失败: $fail"
if [ "$fail" -gt 0 ]; then
  printf '失败清单:\n'
  printf '  - %s\n' "${failed_list[@]}"
  exit 1
fi
