---
name: render-hexagram-svg
description: Deterministically render the hexagram symbol as a standards-compliant SVG file using the gxwd CLI renderer. Use whenever a hexagram SVG is needed; never draw hexagram lines with an image model.
---

# 卦符 SVG 渲染（render-hexagram-svg）

## 职责
- 调用 `gxwd renderer` 生成精确的卦符 SVG（Layer 2）。
- 确保六爻排列（自上而下）、阴阳线型（—— 阳 / — — 阴）与 `binary_bottom_to_top` 编码一致。
- 输出到项目 art 目录，供三层合成使用。

## Input
- `hexagram_id`（1–64）
- `data/hexagrams.json` 中已通过 hexagram-binary-validation 的记录
- 可选：`width`、`height`、`stroke_color`（默认为黑色 #000000）

## Rules
- 卦符由程序生成，禁止由图像模型绘制或手写 SVG 爻线。
- `lines_top_to_bottom` = `binary_bottom_to_top` 的逆序，必须与主数据一致。
- 不修改 `data/**`；不改变卦序或爻位。
- 若主数据与渲染结果不一致，立即 `BLOCKED` 并报告差异。

## Output
- `projects/<id>-<slug>/art/hexagram-symbol.svg`（Layer 2 卦符，无文字）
- `projects/<id>-<slug>/art/hexagram-symbol-metadata.json`：字段含 hexagram_id、binary_bottom_to_top、lines_top_to_bottom、svg_path、rendered_at
- Skill Contract V1.0 JSON

## Failure
- `gxwd render svg` 命令失败或输出 SVG 爻线数量不等于 6 → `BLOCKED`
- 渲染结果与 `binary_bottom_to_top` 不一致 → `BLOCKED`，交人工裁定
- 永不静默修复主数据

## Implementation
- 纯确定性：调用 `.venv/bin/gxwd render svg <id>` 生成 SVG；
- 生成后用 `.venv/bin/gxwd validate binary --id <id>` 二次验证爻线编码；
- 不使用任何 LLM 推理或图像模型。
