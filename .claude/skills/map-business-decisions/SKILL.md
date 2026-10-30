---
name: map-business-decisions
description: Map a hexagram's philosophical structure (change dynamics, tension-resolution, timing) onto a business decision framework — identifying which decision types the hexagram addresses and what strategic postures it suggests.
---

# 企业决策映射（map-business-decisions）

## 职责
- 将该卦的变卦动态（爻位变化、矛盾结构、时位关系）映射为企业决策框架中的场景类型。
- 识别该卦最适用的决策情境（如：转型时机、组织张力、资源分配、领导力边界等）。
- 产出决策映射卡，为 `generate-business-card` 提供结构化依据。

## Input
- `hexagram_id`
- `projects/<id>-<slug>/research/interpretation.json`（三层义理）
- `projects/<id>-<slug>/research/philosophy-comparison.json`
- `projects/<id>-<slug>/research/cultural-symbolism.json`

## Rules
- 映射须以卦象结构为依据，不得捏造与卦义无关的管理概念。
- 现代商业映射属 D 层（现代类比），不得冒充传统义理。
- 历史商业案例须标注证据等级；无可靠案例写"尚无合适的可靠商业案例"。
- 不引用任何经文原文（本轮 SOURCE_PENDING）。
- 不修改 `data/**`。

## Output
- `projects/<id>-<slug>/research/business-decision-map.json`：字段含 hexagram_id、decision_scenarios[]（每项含 scenario_type、tension_description、strategic_posture、applicable_context、evidence_grade）、key_insight
- Skill Contract V1.0 JSON

## Failure
- `interpretation.json` 或 `philosophy-comparison.json` 缺失 → `BLOCKED`
- 映射场景无法追溯到卦象结构 → `REVISION_REQUIRED`
- 永不静默修复权威数据

## Implementation
- 纯 Agent：基于义理层数据，结合商业管理框架（如：战略时机、组织动态、决策边界）；
- 调用 `.venv/bin/gxwd hexagram show <id>` 确认爻位结构；
- 产出供 `generate-business-card` 与 `business-philosophy-mapping` 消费。
