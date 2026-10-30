#!/usr/bin/env bash
# prepack.sh — 构建 wheel/sdist 前把 data/、assets/hexagram-svg/、schemas/
# 复制到 src/gxwd/_bundled/，让装到 site-packages 的 wheel 也能找到数据。
#
# 流程：
#   ./scripts/prepack.sh    # 复制
#   python -m build         # 构建；pyproject 已把 _bundled/** 列入 package-data
#   ./scripts/postpack.sh   # 清理 _bundled（可选）
#
# _bundled/ 已被 .gitignore 排除，不会入库。
# domain.get_data_dir() 会在 repo data/ 不存在时自动 fallback 到 _bundled/data。

set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
BUNDLED="$REPO/src/gxwd/_bundled"

rm -rf "$BUNDLED"
mkdir -p "$BUNDLED"

cp -R "$REPO/data" "$BUNDLED/data"
cp -R "$REPO/schemas" "$BUNDLED/schemas"
mkdir -p "$BUNDLED/assets"
cp -R "$REPO/assets/hexagram-svg" "$BUNDLED/assets/hexagram-svg"
mkdir -p "$BUNDLED/templates"
cp -R "$REPO/templates/card" "$BUNDLED/templates/card" 2>/dev/null || true

# 空 __init__.py 让 setuptools 当它是 package 的一部分
touch "$BUNDLED/__init__.py"

echo "✓ bundled: $BUNDLED"
du -sh "$BUNDLED"
