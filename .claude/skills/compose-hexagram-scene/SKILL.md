---
name: compose-hexagram-scene
description: Select one visual candidate from extract-visual-symbols and compose a detailed scene brief (composition, ink-wash density, figures, atmosphere) for the image-generation pipeline. Never generates the image itself.
---

# 构图意境设计（compose-hexagram-scene）

## 职责
- 从 `visual-symbols.json` 中选定一套视觉方案，细化为完整场景简报：构图分区、笔墨密度、人物比例与姿态、气候与光影、留白位置。
- 确保场景与卦义立意一致（一卦一象，一象一境，一境一理）。
- 不生成最终图像；场景简报是 `ink-image-production` 的输入。

## Input
- `hexagram_id`
- `projects/<id>-<slug>/art/visual-symbols.json`
- `projects/<id>-<slug>/research/interpretation.json`
- `docs/art-style-guide.md`

## Rules
- 构图必须符合三层合成原则：Layer 1 无字主图 / Layer 2 卦符 SVG（程序层）/ Layer 3 文字印章（独立层）；场景简报只针对 Layer 1。
- 留白参考 35%–45%，具体比例依叙事灵活调整。
- 五色体系：青黛 #273F52、石青 #547A83、石绿 #A2B4A1、赭石 #B58C69、朱砂 #A74439（朱砂少量）。
- 不描述汉字、卦符、印章位置（由程序层决定）。
- 不颠倒上下卦象征方位；自然景物可艺术化，卦象结构须精确。

## Output
- `projects/<id>-<slug>/art/scene-brief.json`：字段含 hexagram_id、selected_candidate_id、composition_zones[]（foreground/midground/background 各含 elements[]、ink_density）、figures[]（count、posture、scale）、atmosphere、whitespace_ratio、color_emphasis[]
- `projects/<id>-<slug>/art/scene-brief.md`：人可读场景描述（中文）
- Skill Contract V1.0 JSON

## Failure
- `visual-symbols.json` 缺失 → `BLOCKED`
- 场景构图与卦象上下卦关系矛盾 → `REVISION_REQUIRED`
- 留白比例超出 15%–65% 极端范围 → `REVISION_REQUIRED`
- 永不静默修复权威数据

## Implementation
- 半自动 Agent：在 `visual-symbols.json` 候选中选优，写场景简报；
- 遵循 `docs/art-style-guide.md` 与 `.claude/rules/art-style.md`；
- 产出交 `ink-art-direction` 审核，再送 `ink-image-production` 生产。
