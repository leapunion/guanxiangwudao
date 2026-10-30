---
name: plan-hexagram-production
description: Orchestrate and schedule the full single-hexagram production pipeline — from research through art, review gates, and publication readiness — generating a task plan with dependencies, status and blockers. Use as the entry point for any new hexagram work.
---

# 单卦生产总控（plan-hexagram-production）

## 职责
- 为指定卦（或批量多卦）生成完整生产任务计划，列出所有 Skill 的执行顺序、依赖关系和当前状态。
- 检测阻断点（BLOCKED / REVISION_REQUIRED）并汇报给人工编辑。
- 不执行具体生产任务；只规划、监控和报告。

## Input
- `hexagram_id`（单卦）或 `hexagram_ids[]`（批量，最多 64）
- `data/hexagrams.json`（全卦状态）
- 各卦 `projects/<id>-<slug>/reviews/`（G1/G2/G3 状态）
- 各卦 `projects/<id>-<slug>/approval.json`（人工批准状态）

## Rules
- 生产顺序不可颠倒：研究层 → G1 审校 → 艺术层 → G2 审校 → G3 出版审查 → 人工批准 → 出版。
- 任何 Skill 返回 BLOCKED 时，该卦整条流水线暂停；任务计划标记该卦为 `BLOCKED`，并注明原因。
- 不得绕过审查关卡；不得将未通过 G1 的卦推进到艺术层。
- 任何 AI 角色无权在任务计划中将卦状态标记为 APPROVED 或 PUBLISHED；该权限只属于人工。
- 不修改 `data/**` 或任何审查报告。

## Output
- `projects/<id>-<slug>/production-plan.json`（单卦）或 `output/batch-production-plan.json`（批量）：
  字段含 hexagram_id、pipeline_status（PENDING/IN_PROGRESS/BLOCKED/G1_PASS/G2_PASS/G3_PASS/AWAITING_APPROVAL/PUBLISHED）、tasks[]（每项含 task_name、skill_slug、depends_on[]、status、blocker_note）
- `output/production-dashboard.md`（批量时：各卦状态一览表，含阻断点汇总）
- Skill Contract V1.0 JSON

## Failure
- 数据目录结构异常（缺少 `projects/<id>-<slug>/` 目录）→ `BLOCKED`，报告缺失路径
- 检测到循环依赖 → `BLOCKED`，交人工裁定
- 永不静默修复权威数据

## Implementation
- 半自动：调用 `.venv/bin/gxwd status` 和 `.venv/bin/gxwd validate binary --all` 获取当前状态；
- Agent 解析状态、识别阻断点、生成任务计划；
- 定期（人工触发）重新运行以更新 `production-dashboard.md`；
- 本 Skill 是整个生产系统的入口点和调度面板，不替代任何具体 Skill。
