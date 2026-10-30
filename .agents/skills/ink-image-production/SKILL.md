---
name: ink-image-production
description: Produce and record a text-free ink-painting master artwork for a hexagram from an approved art brief, with full provenance. Hexagram symbols come from gxwd.renderer and text/seals are separate layers. Use only after the art brief exists.
---

# Ink Image Production

## Input
- hexagram_id
- `projects/<id>-<slug>/art/art-brief.md`
- 图像模型与参数（**本轮未选定图像模型**）
- 程序生成的卦符：`assets/hexagram-svg/<id:02d>-<slug>.svg`

## Rules
- **只生成无字主图**：不含汉字、卦符、印章。
- 卦符由 `gxwd.renderer` 程序绘制，文字与印章另作独立图层，不让图像模型绘制。
- 必须保存模型、prompt、参数、随机种子（如有）和版本，以便溯源。
- 每次修订保留版本，不覆盖旧图。
- 不得出现现代物品、错误服饰；不颠倒上下卦关系。
- 图像模型选型与授权须人工确认。

## Output
- `projects/<id>-<slug>/art/master/v<N>.png`（模型选定后）
- `projects/<id>-<slug>/art/provenance/v<N>.json`：model、prompt、parameters、seed、created_at、brief 版本、卦符 SVG 路径。
- `projects/<id>-<slug>/art/layers.md`：三层合成说明。
- Skill Contract V1.0 JSON。

## Failure
- 未选定图像模型或缺少授权 → `BLOCKED`；本轮只写 prompt 草稿到 `art/provenance/`，不生成图。
- 缺少溯源信息 → `REVISION_REQUIRED`。
- 永不改动 `data/**`。

## Implementation
- 卦符：只读 `assets/hexagram-svg/<id:02d>-<slug>.svg`；如需复制到 projects，用
  `.venv/bin/gxwd render svg <id> --out projects/<id:02d>-<slug>/art/layers/`
  （CLI 单卦子命令待 V5 集成后启用）。
- 或调用 `gxwd.renderer.render_hexagram_svg(...)` 直接生成到目标路径。
- 主图生成工具待模型选定后在此补充；生成后交 independent-verifier 做 G2。
