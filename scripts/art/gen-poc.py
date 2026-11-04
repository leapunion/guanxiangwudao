#!/usr/bin/env python3
"""gen-poc.py — H1 乾 / H29 坎 / H52 艮 三卦艺术层 POC 生成器。

本脚本是 RFC #001 推荐的 FLUX.1 schnell via MFLUX 的 POC 实现。
**只生成到 scratchpad/，不写 projects/*/art/**（art-style.md 第 10 条
"本轮未选定图像模型" 红线仍在，解禁要等 Governance V3 Issue #20
被 cavin 签字批准）。

用法：
    .venv/bin/python scripts/art/gen-poc.py
    MFLUX_BIN=~/.local/bin/mflux-generate python scripts/art/gen-poc.py
    python scripts/art/gen-poc.py --hexagrams 1,29,52 --output scratchpad/poc-art

依据：
- RFC #001 §6 POC plan（docs/rfc/001-art-model-selection.md）
- art-style.md 五色 palette + 留白 35-45% + 禁文字
- mflux-generate 参数见 docs/setup/mflux-local.md

诚实约束：
- 不在 projects/*/art/ 下写 master.png
- 输出默认 scratchpad/poc-art/，git ignored
- 每图伴生 <hexagram>.yaml 记录 model/prompt/seed/steps/quantization
  供未来 Governance V3 批准后正式迁移到 projects/ 时作为 provenance
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# 三卦 POC · prompt 参照 RFC #001 §6 的格式
#   - 五色 palette 用十六进制显式列出
#   - 禁文字 / 卦符 / 印章（三层合成器会另外叠这些）
#   - 留白 35-45%
#   - style 词堆：chinese ink painting + shuimo + literati + minimalist
# ---------------------------------------------------------------------------

POC_HEXAGRAMS: dict[int, dict] = {
    1: {
        "name": "乾",
        "slug": "qian",
        "yi": "天行健·君子以自强不息",
        "scene": (
            "a vast open sky with soaring clouds, a solitary dragon silhouette "
            "half-hidden in mist, towering peaks far below, strong upward vertical "
            "composition, dawn light"
        ),
    },
    29: {
        "name": "坎",
        "slug": "kan",
        "yi": "习坎·君子以常德行",
        "scene": (
            "deep layered mountain gorges with flowing water, a cascading waterfall "
            "into darkness, swirling mist rising between cliffs, a small boat barely "
            "visible, horizontal layered depth, dusk atmosphere"
        ),
    },
    52: {
        "name": "艮",
        "slug": "gen",
        "yi": "兼山·君子以思不出其位",
        "scene": (
            "two parallel mountain peaks in quiet stillness, ancient pine tree in the "
            "foreground, a small meditating figure on a rock ledge, thick low mist "
            "settling in the valley, perfect horizontal balance, evening calm"
        ),
    },
}

# 共享 style prefix / suffix · 严格遵守 art-style.md
STYLE_PREFIX = (
    "traditional Chinese ink painting, literati shuimo style, "
    "minimalist Song dynasty aesthetic, "
)

PALETTE_CONSTRAINT = (
    "muted palette of ink black #273F52, stone blue #547A83, jade green #A2B4A1, "
    "ochre #B58C69, with a touch of cinnabar red #A74439, "
)

LAYOUT_CONSTRAINT = (
    "35-45% white space, elegant brushwork, soft wash gradients, "
    "no hard outlines, "
)

NEGATIVE_PREFIX = (
    "no text, no Chinese characters, no calligraphy, no seals, no stamps, "
    "no writing, no signatures, "
    "no western painting style, no photorealism, no oil painting, "
    "no modern objects, no people wearing modern clothing"
)


def build_prompt(hexagram: dict) -> str:
    """组装一个卦的完整 prompt."""
    return (
        STYLE_PREFIX
        + PALETTE_CONSTRAINT
        + LAYOUT_CONSTRAINT
        + hexagram["scene"]
        + ". "
        + NEGATIVE_PREFIX
    )


def resolve_mflux_bin() -> str:
    """找 mflux-generate 命令。

    优先级：
    1. $MFLUX_BIN 环境变量（最高优先）
    2. PATH 中的 mflux-generate
    3. ~/.local/bin/mflux-generate（uv tool 默认路径）
    4. .venv/bin/mflux-generate（pip 装本项目 venv）
    """
    env = os.environ.get("MFLUX_BIN")
    if env and Path(env).exists():
        return env

    found = shutil.which("mflux-generate")
    if found:
        return found

    for candidate in (
        Path.home() / ".local/bin/mflux-generate",
        Path(__file__).resolve().parents[2] / ".venv/bin/mflux-generate",
    ):
        if candidate.exists():
            return str(candidate)

    print(
        "❌ 找不到 mflux-generate 命令。装法见 docs/setup/mflux-local.md § 二。\n"
        "   或通过 MFLUX_BIN=/path/to/mflux-generate 环境变量显式指定。",
        file=sys.stderr,
    )
    sys.exit(2)


def generate_one(
    *,
    mflux_bin: str,
    hexagram_id: int,
    hexagram: dict,
    out_dir: Path,
    steps: int,
    seed: int,
    quantization: int,
) -> Path:
    """跑一张图并写 provenance yaml."""
    slug = hexagram["slug"]
    out_png = out_dir / f"H{hexagram_id:02d}-{slug}.png"
    out_yaml = out_dir / f"H{hexagram_id:02d}-{slug}.yaml"
    prompt = build_prompt(hexagram)

    print(f"\n━━━━━ H{hexagram_id} {hexagram['name']}（{slug}）━━━━━")
    print(f"输出: {out_png}")
    print(f"prompt (前 120 字): {prompt[:120]}...")

    cmd = [
        mflux_bin,
        "--model", "schnell",
        "--prompt", prompt,
        "--steps", str(steps),
        "--seed", str(seed),
        "-q", str(quantization),
        "--output", str(out_png),
    ]
    start = dt.datetime.now()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed = (dt.datetime.now() - start).total_seconds()

    if result.returncode != 0:
        print(f"❌ mflux-generate 失败（exit {result.returncode}）", file=sys.stderr)
        print(f"stderr:\n{result.stderr[-800:]}", file=sys.stderr)
        sys.exit(result.returncode)

    if not out_png.exists():
        print(f"❌ mflux 跑完但找不到输出文件 {out_png}", file=sys.stderr)
        sys.exit(3)

    size_kb = out_png.stat().st_size / 1024
    print(f"✅ {size_kb:.1f} KB · {elapsed:.1f}s")

    # 伴生 provenance yaml（未来 V3 批准后迁移到 projects/ 的 provenance.json 时参考）
    out_yaml.write_text(
        (
            f"hexagram_id: {hexagram_id}\n"
            f"name: {hexagram['name']}\n"
            f"slug: {slug}\n"
            f"yi: {hexagram['yi']}\n"
            f"model: flux-1-schnell-mflux-{quantization}bit\n"
            f"steps: {steps}\n"
            f"seed: {seed}\n"
            f"quantization: q{quantization}\n"
            f"generated_at: {dt.datetime.now().astimezone().isoformat()}\n"
            f"elapsed_seconds: {elapsed:.1f}\n"
            f"file: {out_png.name}\n"
            f"file_size_bytes: {out_png.stat().st_size}\n"
            f"prompt: |\n"
        ),
        encoding="utf-8",
    )
    # yaml 多行 prompt 要缩进
    with out_yaml.open("a", encoding="utf-8") as f:
        for line in prompt.split(". "):
            f.write(f"  {line}.\n")
    return out_png


def main() -> int:
    p = argparse.ArgumentParser(
        description="FLUX.1 schnell 三卦艺术 POC 生成器（Governance V3 待批准前只写 scratchpad）"
    )
    p.add_argument(
        "--hexagrams",
        type=str,
        default="1,29,52",
        help="逗号分隔的卦序列表，默认 1,29,52（乾/坎/艮，RFC #001 §6 推荐的 POC 三卦）",
    )
    p.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "scratchpad/poc-art",
        help="输出目录，默认 <repo>/scratchpad/poc-art/（被 .gitignore 排除）",
    )
    p.add_argument("--steps", type=int, default=4, help="推理步数（schnell 推荐 2-4）")
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        help="随机种子（同种子应产出同图，便于复现）",
    )
    p.add_argument(
        "-q",
        "--quantization",
        type=int,
        default=8,
        choices=[4, 8],
        help="量化位数（4 最省内存，8 画质更好）",
    )
    args = p.parse_args()

    ids = [int(x) for x in args.hexagrams.split(",") if x.strip()]
    unknown = [i for i in ids if i not in POC_HEXAGRAMS]
    if unknown:
        print(
            f"⚠️ 以下卦序不在 POC 清单里: {unknown}。"
            f"本脚本只覆盖 {sorted(POC_HEXAGRAMS)}；要加别的卦先在 POC_HEXAGRAMS 字典里补 scene 描述。",
            file=sys.stderr,
        )
        return 2

    mflux_bin = resolve_mflux_bin()
    print(f"mflux-generate: {mflux_bin}")

    args.output.mkdir(parents=True, exist_ok=True)
    print(f"输出目录: {args.output}")

    pngs: list[Path] = []
    for i in ids:
        png = generate_one(
            mflux_bin=mflux_bin,
            hexagram_id=i,
            hexagram=POC_HEXAGRAMS[i],
            out_dir=args.output,
            steps=args.steps,
            seed=args.seed,
            quantization=args.quantization,
        )
        pngs.append(png)

    print(f"\n━━━━━ 全部完成 ━━━━━")
    for png in pngs:
        print(f"  {png}")
    print(
        "\n下一步：\n"
        "  1. 用 Preview / Finder 看三张图的艺术效果\n"
        "  2. 满意 → 回报 Agent，等 Governance V3 Issue #20 批准后批量生成 64 卦并替换 projects/*/art/master.png\n"
        "  3. 不满意 → 调 scripts/art/gen-poc.py 的 prompt / steps / seed，或走 RFC #001 的备选模型 SD 3.5 Medium",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
