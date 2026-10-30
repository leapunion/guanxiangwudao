---
name: assemble-art-card
description: Merge the three independent layers (ink painting, hexagram SVG, calligraphy-and-seal layer) into a final composite art card with version metadata. Use after all three layers are approved; never modifies source layers.
---

# 艺术图卡合成（assemble-art-card）

## 职责
- 将三个独立图层合成为最终艺术图卡：Layer 1 国画主图 + Layer 2 卦符 SVG + Layer 3 文字与印章。
- 生成含版本信息的合成元数据，确保三层引用版本一致。
- 不修改任何源图层；合成失败则报告，不静默降级。

## Input
- `hexagram_id`
- `projects/<id>-<slug>/art/main-painting.*`（Layer 1，`ink-image-production` 产出）
- `projects/<id>-<slug>/art/hexagram-symbol.svg`（Layer 2，`render-hexagram-svg` 产出）
- `projects/<id>-<slug>/art/calligraphy-seal-layer.*`（Layer 3，`compose-seal-layer` 产出）
- `projects/<id>-<slug>/reviews/g2-<slug>.json`（艺术审查通过记录）

## Rules
- 前置条件：G2 通过记录存在且为 pass。
- 三层必须版本一致；版本号记录在 `artwork-versions.json` 中。
- 合成后图卡不得含有裁切溢出、图层位移或颜色模式不一致的缺陷。
- 不修改源图层文件；合成出错时保留错误日志，交人工处理。
- 经文仍为 SOURCE_PENDING 的作品合成后标记 `text_status: pending`，不得进入 PUBLISHED 流程。

## Output
- `projects/<id>-<slug>/art/art-card-composite.*`（最终合成图卡）
- `projects/<id>-<slug>/art/art-card-metadata.json`：字段含 hexagram_id、layer1_version、layer2_version、layer3_version、composite_size、color_mode、text_status、assembled_at
- Skill Contract V1.0 JSON

## Failure
- G2 审查记录缺失或为 fail → `BLOCKED`
- 任一源图层缺失或版本不一致 → `BLOCKED`
- 合成输出含明显视觉缺陷 → `REVISION_REQUIRED`
- 永不静默修复源图层

## Implementation
- 半自动：CLI 工具（ImageMagick / 项目合成脚本）执行像素合成；
- 调用 `.venv/bin/gxwd status <id>` 确认各图层状态；
- 合成后产出送 `publication-qa`（G3 审查）。
