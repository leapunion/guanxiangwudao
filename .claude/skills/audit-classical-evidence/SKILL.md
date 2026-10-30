---
name: audit-classical-evidence
description: Run gate G1 classical scholarship audit on a hexagram's full research layer — structural validation, text attribution, evidence grades, source references — producing a G1 pass/fail report. Cannot approve its own output.
---

# 国学证据审校（G1）（audit-classical-evidence）

## 职责
- 担任 G1 关卡：对单卦全研究层（义理解释、历史典故、文化象征）做独立审校。
- 核查：卦象结构与编码一致性、经文状态标注（SOURCE_PENDING）、证据等级标注、来源引用可靠性。
- 产出 G1 审查报告，不修改被审成果。

## Input
- `hexagram_id`
- `projects/<id>-<slug>/research/`（全部 JSON 产出）：
  - `lookup.json`、`interpretation.json`、`yao-cases.json`
  - `historical-allusions.json`、`cultural-symbolism.json`、`philosophy-comparison.json`
- `data/hexagrams.json`、`data/yao-texts.json`、`data/sources.json`
- `projects/<id>-<slug>/reviews/historical-evidence-<slug>.json`

## Rules
- 只给 pass / fail 与问题清单；不修改被审文件。
- 必须核查：① 卦象编码与主数据一致；② 所有引用的经文原文状态为 SOURCE_PENDING；③ 证据等级无 A/B 级但缺乏来源支撑的条目；④ 无编造书名。
- 研究 Agent 不得审查自己产出的内容；本 Skill 是独立审查角色。
- 国学审查意见与艺术审查意见分别记录，不混写。
- 永不静默修复被审成果；差异交人工裁定。

## Output
- `projects/<id>-<slug>/reviews/g1-<slug>.json`：字段含 hexagram_id、review_status（pass/fail）、issues[]（每项含 item、severity、description）、auditor_note、audited_at
- Skill Contract V1.0 JSON

## Failure
- 发现卦象编码与主数据不一致 → `BLOCKED`，整卦阻断
- 发现编造经文或书名 → `BLOCKED`
- 被审材料缺失 → `BLOCKED`
- 永不静默修复权威数据

## Implementation
- 纯 Agent 审查 + 确定性 CLI 验证；
- 调用 `.venv/bin/gxwd validate binary --id <id>` 做编码验证；
- 调用 `.venv/bin/gxwd hexagram show <id>` 对照卦名与结构；
- G1 通过后，`yao-interpretation`、`compose-hexagram-scene` 等下游 Skill 方可继续。
