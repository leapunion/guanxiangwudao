---
name: generate-business-card
description: Generate a structured business philosophy card for a hexagram — a concise, publication-ready one-pager linking hexagram insight to strategic decision scenarios — after business-decision-map and verify-business-cases pass.
---

# 企业哲学卡片生成（generate-business-card）

## 职责
- 基于 `business-decision-map.json` 和核查通过的案例，生成结构化企业哲学卡片。
- 卡片包含：卦名与象义、核心商业洞察（一句话）、适用决策场景（2–3 条）、行动指引（3 条以内）。
- 输出 JSON + Markdown 双格式，供排版和出版使用。

## Input
- `hexagram_id`
- `projects/<id>-<slug>/research/business-decision-map.json`
- `projects/<id>-<slug>/reviews/business-cases-<slug>.json`（核查通过）
- `projects/<id>-<slug>/research/interpretation.json`（义理摘要）

## Rules
- 前置条件：`business-cases-<slug>.json` 的 `review_status` 为 pass 或 warn（warn 须附说明）。
- 核心洞察须能直接追溯到卦象结构，不得是通用管理语录。
- 行动指引为现代转译（D 层），不得冒充古典原文。
- 不引用经文原文（本轮 SOURCE_PENDING）；引用用 `[[H<id>-guaci]]` 占位。
- 不修改 `data/**`。

## Output
- `projects/<id>-<slug>/research/business-card.json`：字段含 hexagram_id、headline_insight、decision_scenarios[]（取自映射结果，限 3 条）、action_guidelines[]（限 3 条）、evidence_summary、source_status
- `projects/<id>-<slug>/research/business-card.md`：人可读卡片（中文）
- Skill Contract V1.0 JSON

## Failure
- `business-cases-<slug>.json` 缺失或 `review_status` 为 fail → `BLOCKED`
- 核心洞察无法追溯到卦象结构 → `REVISION_REQUIRED`
- 永不静默修复权威数据

## Implementation
- 纯 Agent：综合义理与决策映射撰写卡片；
- 调用 `.venv/bin/gxwd hexagram show <id>` 确认卦名与象义；
- 产出供 `publish-hexagram-collection` 打包，供 `publication-qa` 检查文图匹配。
