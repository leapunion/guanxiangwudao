#!/usr/bin/env bash
# import-and-gate.sh：单卦经文录入 + G1（卦符二进制门禁）产出的一键脚本。
#
# 流程：
#   1. 从 inputs/human/<id:02d>-<slug>-canonical.csv 读经文
#   2. .venv/bin/gxwd texts import   —— 写入 data/canonical-texts.json
#   3. .venv/bin/gxwd texts validate —— 对整个 canonical-texts.json 跑 schema 校验
#   4. .venv/bin/gxwd validate binary <id> --json --out
#      projects/<id:02d>-<slug>/reviews/g1-binary-validation.json
#
# 用法：
#   ./scripts/import-and-gate.sh 37 jiaren
#   ./scripts/import-and-gate.sh 1  qian
#
# 该脚本本身只操作已允许写入的目录（data/、projects/*/reviews/）。
# inputs/human/ 的 CSV 必须由国学主编人工填好；脚本不会修改它。

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "用法: $0 <hexagram_id> <slug>" >&2
  echo "例:   $0 37 jiaren" >&2
  exit 2
fi

ID_RAW="$1"
SLUG="$2"
PADDED_ID=$(printf "%02d" "$ID_RAW")

REPO_ROOT=$(cd "$(dirname "$0")/.." && pwd)
GXWD="$REPO_ROOT/.venv/bin/gxwd"
CSV="$REPO_ROOT/inputs/human/${PADDED_ID}-${SLUG}-canonical.csv"
REVIEWS_DIR="$REPO_ROOT/projects/${PADDED_ID}-${SLUG}/reviews"
G1_REPORT="$REVIEWS_DIR/g1-binary-validation.json"

if [ ! -x "$GXWD" ]; then
  echo "gxwd 不可执行：$GXWD（先 \`uv pip install -e .\`）" >&2
  exit 1
fi

if [ ! -f "$CSV" ]; then
  echo "CSV 不存在：$CSV" >&2
  echo "先把 templates/canonical-input/${PADDED_ID}-${SLUG}-canonical.csv.template 拷贝到 inputs/human/，由国学主编填好经文再跑本脚本。" >&2
  exit 1
fi

mkdir -p "$REVIEWS_DIR"

echo "==> [1/3] texts import"
"$GXWD" texts import "$CSV" --hexagram-id "$ID_RAW"

echo "==> [2/3] texts validate"
"$GXWD" texts validate

echo "==> [3/3] G1 二进制门禁 → $G1_REPORT"
"$GXWD" validate binary "$ID_RAW" --json --out "$G1_REPORT"

echo "完成。接下来由 independent-verifier 补 interpretation-review / g2 / g3，再走 publisher.request_publication。"
