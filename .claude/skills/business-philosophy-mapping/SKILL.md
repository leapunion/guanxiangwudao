---
name: business-philosophy-mapping
description: Translate a hexagram's classical meaning into business-philosophy insights in three separated layers - classical meaning, modern analogy, management suggestion. Never predicts fortune or misfortune. Use after interpretation passes義理审查.
---

# Business Philosophy Mapping

## Input
- hexagram_id
- 通过义理审查的 `projects/<id>-<slug>/research/interpretation.md`（见 `reviews/interpretation-review.json`）
- 案例资料（如有，须标注来源）
- `templates/business-philosophy.md`

## Rules
- 三层严格分开：经典原义 / 现代类比 / 经营建议。
- 现代解释不得冒充古典原文。
- 不预测吉凶，不做必然性断言；建议是可检验的管理思路，不是占断。
- 企业案例标注来源与证据等级；无据不写。
- 本轮不引用经文原文，示例写"（待底本校勘）"。

## Output
- `projects/<id>-<slug>/research/business-philosophy.md`
- Skill Contract V1.0 JSON。

## Failure
- 卦义未通过义理审查（`reviews/interpretation-review.json` 为 pass）→ `BLOCKED`。
- 出现吉凶预测或混层 → `REVISION_REQUIRED`。
- 永不修改 `data/**`。

## Implementation
- 以模板填写；取卦象事实用 `.venv/bin/gxwd hexagram show <id>`。
- 完成后交 independent-verifier 复核。
