---
name: compose-seal-layer
description: Compose the calligraphy text and seal elements into Layer 3 of the art card, following the layout specification. Seal text must be original and human-confirmed; never fabricate seal inscriptions.
---

# 印章与文字图层合成（compose-seal-layer）

## 职责
- 依据 `calligraphy-layout.json` 将书法文字与印章元素合成为 Layer 3 独立图层。
- 验证印章文字原创性与授权（须有人工确认记录）。
- 输出 Layer 3 图层文件，不合并到主图。

## Input
- `hexagram_id`
- `projects/<id>-<slug>/art/calligraphy-layout.json`（`design-calligraphy-layout` 产出）
- 印章素材目录：`projects/<id>-<slug>/art/seals/`（须含 `seal-approval.json` 人工确认记录）
- 书法文字素材：`projects/<id>-<slug>/art/calligraphy/`

## Rules
- 印文须原创且有人工确认记录（`seal-approval.json` 含 `approved_by`、`approved_at`）；无确认记录不得合成。
- 字体与书法素材须有授权确认；无授权标注 `UNVERIFIED_LICENSE`，不得进入出版。
- Layer 3 只含文字与印章，不含卦符线条（卦符属 Layer 2）。
- 不修改 `data/**` 或其他图层源文件。
- 本轮经文为 SOURCE_PENDING：图层内引用的文字不得包含经文原文。

## Output
- `projects/<id>-<slug>/art/calligraphy-seal-layer.*`（Layer 3 独立图层，透明背景）
- `projects/<id>-<slug>/art/calligraphy-seal-metadata.json`：字段含 hexagram_id、seal_ids[]、calligraphy_font、license_status、seal_approval_ref、layer3_version
- Skill Contract V1.0 JSON

## Failure
- `seal-approval.json` 缺失或 approved_by 为空 → `BLOCKED`
- 书法素材授权状态为 `UNVERIFIED_LICENSE` → `BLOCKED`
- 图层含经文原文（非 SOURCE_PENDING 占位）→ `BLOCKED`
- 永不静默修复权威数据

## Implementation
- 半自动：合成脚本（ImageMagick 或 SVG compose）依规格摆放元素；
- Agent 负责核查 `seal-approval.json` 与授权记录；
- 产出为 `assemble-art-card` 的 Layer 3 输入。
