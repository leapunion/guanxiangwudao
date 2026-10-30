---
name: historical-evidence-check
description: Independently verify the evidence grade and source references of historical allusions produced by research-historical-allusions. Acts as G1 historical sub-check; never edits the allusions it reviews.
---

# 历史证据核查（historical-evidence-check）

## 职责
- 独立核查 `historical-allusions.json` 中每条典故的证据等级标注是否合理。
- 标记来源引用中可疑的书名、版本、页码（疑为编造）。
- 产出核查报告，不修改被审文件。

## Input
- `hexagram_id`
- `projects/<id>-<slug>/research/historical-allusions.json`
- `data/sources.json`（已登记底本）

## Rules
- 只给 pass / fail / warn 与问题清单，不修改被审内容。
- 对无法确认真实性的书名标注 `UNVERIFIED`；对明确虚假的标注 `FABRICATED`。
- 不得自行降级或升级证据等级；差异交人工裁定。
- 不编造书名或版本来"补全"引用。
- 永不修改 `data/**` 或 `research/historical-allusions.json`。

## Output
- `projects/<id>-<slug>/reviews/historical-evidence-<slug>.json`：字段含 allusion_id、check_status（pass/warn/fail）、issues[]、verifier_note
- Skill Contract V1.0 JSON，含总体 `review_status`（pass/fail）

## Failure
- 发现 FABRICATED 来源 → `BLOCKED`，整批典故进入 `REVISION_REQUIRED`
- 被审文件缺失或格式错误 → `BLOCKED`
- 永不静默修复被审成果

## Implementation
- 纯 Agent 核查（对照已知文献知识）；
- 调用 `.venv/bin/gxwd hexagram show <id>` 确认上下文；
- 核查人与研究人必须为独立角色，禁止同一 Agent 既产出又核查同一条目。
