---
name: design-calligraphy-layout
description: Design the typographic and calligraphic layout for a hexagram publication page — text placement, font selection, column structure and whitespace — producing a layout specification file for the seal and publishing pipeline.
---

# 书法排版设计（design-calligraphy-layout）

## 职责
- 设计单卦出版页的版式：文字分区、字体选择（须有授权确认）、行距、天地间距、栏宽。
- 确定卦名题字、义理摘要、注释三区的位置与比例。
- 输出排版规格文件，供 `compose-seal-layer` 与 `publish-hexagram-collection` 使用。

## Input
- `hexagram_id`
- `projects/<id>-<slug>/research/interpretation.json`（义理摘要源）
- `docs/art-style-guide.md`（版式规范参考）
- 字体授权清单（`data/fonts.json`，若存在）

## Rules
- 字体须有明确授权（开源或已采购商业授权）；未经授权的字体不得进入版式。
- 版面文字不得包含未经审定的经文原文（本轮 SOURCE_PENDING）。
- 版式规格以物理尺寸（mm）与分辨率（dpi）双重标注，适配印刷与屏幕。
- 不修改 `data/**`；不修改 `art-style-guide.md`。

## Output
- `projects/<id>-<slug>/art/calligraphy-layout.json`：字段含 hexagram_id、page_size（mm）、dpi、zones[]（每区含 zone_name、position_mm、font_family、font_size_pt、line_height、text_source_field）、whitespace_top_mm、whitespace_bottom_mm
- Skill Contract V1.0 JSON

## Failure
- 使用的字体无法确认授权 → `BLOCKED`，停止并报告字体名称
- 排版区域溢出页面边界 → `REVISION_REQUIRED`
- 版面包含 SOURCE_PENDING 经文原文 → `BLOCKED`
- 永不静默修复权威数据

## Implementation
- 纯 Agent：基于规格文档生成 JSON 排版规格；
- 如需预览，调用项目排版脚本生成草稿 PDF；
- 产出供 `compose-seal-layer` 定位印章，供 `publish-hexagram-collection` 套用。
