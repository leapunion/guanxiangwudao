---
name: verify-business-cases
description: Independently verify the evidence grade and factual accuracy of business cases cited in a hexagram's business-decision-map. Acts as a G1-equivalent check for the enterprise philosophy layer; never edits the cases it reviews.
---

# 商业案例核查（verify-business-cases）

## 职责
- 独立核查 `business-decision-map.json` 中每条商业案例的证据等级标注是否合理。
- 标记可疑或无法核实的来源引用（公司名、事件年份、媒体报道）。
- 产出核查报告，不修改被审文件。

## Input
- `hexagram_id`
- `projects/<id>-<slug>/research/business-decision-map.json`
- `projects/<id>-<slug>/research/historical-allusions.json`（交叉参照）

## Rules
- 只给 pass / warn / fail 与问题清单；不修改被审内容。
- 证据等级 D（现代类比）无需核查来源真实性，但须确认未被标注为 A/B 级。
- 对无法确认的来源标注 `UNVERIFIED`；对明确错误的事实标注 `FACTUAL_ERROR`。
- 核查人与映射人必须为独立角色。
- 不修改 `data/**` 或 `business-decision-map.json`。

## Output
- `projects/<id>-<slug>/reviews/business-cases-<slug>.json`：字段含 case_id、check_status（pass/warn/fail）、issues[]、verifier_note
- Skill Contract V1.0 JSON，含总体 `review_status`

## Failure
- 发现 FACTUAL_ERROR 且证据等级为 A 或 B → `BLOCKED`，整批进入 `REVISION_REQUIRED`
- 被审文件缺失 → `BLOCKED`
- 永不静默修复被审成果

## Implementation
- 纯 Agent 核查：对照已知商业史与公开事实；
- 调用 `.venv/bin/gxwd hexagram show <id>` 确认上下文；
- 报告供 `audit-classical-evidence` 汇总时参考。
