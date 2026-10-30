---
name: extract-visual-symbols
description: Convert a hexagram's cultural symbols and line structure into a ranked list of paintable visual motifs and scene elements for the ink-art pipeline. Use after cultural-symbolism; outputs art-direction seeds only, never final prompts.
---

# 视觉符号提取（extract-visual-symbols）

## 职责
- 将 `cultural-symbolism.json` 中的象征词条转译为可入画的视觉母题（山水、人物姿态、器物、气候、光影）。
- 按"卦义契合度"排序，输出前 5 组候选视觉方案（场景标题 + 母题列表 + 构图方向建议）。
- 只提供视觉语素库，不生成最终 prompt；具体场景由 `compose-hexagram-scene` 决定。

## Input
- `hexagram_id`
- `projects/<id>-<slug>/research/cultural-symbolism.json`
- `projects/<id>-<slug>/research/interpretation.json`
- `docs/art-style-guide.md`（五色体系、留白规范）

## Rules
- 视觉方案必须忠实于卦象结构（上下卦象义）；不得颠倒上下卦关系。
- 不使用现代物品、错误历史服饰；参考 `.claude/rules/art-style.md`。
- 不生成任何汉字、卦符、印章的描述（由程序层处理）。
- 不修改 `data/**` 或 art-style-guide。

## Output
- `projects/<id>-<slug>/art/visual-symbols.json`：字段含 hexagram_id、visual_candidates[]（每项含 scene_title、motifs[]、composition_hint、color_palette_refs[]）
- Skill Contract V1.0 JSON

## Failure
- `cultural-symbolism.json` 缺失或未通过核查 → `BLOCKED`
- 视觉方案与卦象上下卦关系矛盾 → `REVISION_REQUIRED`
- 永不静默修复权威数据

## Implementation
- 半自动 Agent：读取象征数据，遵循艺术红线产出视觉方案；
- 参照 `docs/art-style-guide.md` 五色体系；
- 产出供 `compose-hexagram-scene` 选用，供 `ink-art-direction` 细化。
