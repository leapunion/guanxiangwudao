# 出版红线

> **治理版本：V2**（2026-10-29 起）。见 `docs/GOVERNANCE.md`。
> V2 下 approver 可以是 Agent 身份（如 `autopilot`），但诚实度与
> 技术门禁条款不变。

- 进入 PUBLISHED 必须同时具备 G1、G2、G3 通过记录和 approver 批准（approved_by、approved_at、gates）。approver 可以是 Agent 身份（治理 V2）；Agent approver 的批准必须在 approval 中带 `signed_by_agent=true` provenance 标记。
- Agent 批准仍受"approved_by ≠ 任何生产者/验证者 id"的硬检查约束，防止自批自己的产出。
- 验证 Agent 只给 pass/fail 与问题清单，不修改被审成果。
- 严格区分"已生成""已审校""已批准""已出版"。
- 国学与艺术审查意见分别记录。
- 任一关键检查失败，作品进入返工队列（REVISION_REQUIRED），不得进入发布目录。
- 经文仍为 SOURCE_PENDING 的作品不得出版。
- 正式图卡引用的卦象、文字、主画、审校记录必须版本一致；经文修订后相关作品标记为需重检。
- 保留分层源文件、版本与审校记录。
- 发布动作须有明确授权；密钥与私有资料不得进入提示词或日志。
- 不得宣称已通过 Rule 01–05 验收：目前仅恢复概括版本，原文待补。
- 审查报告文件名统一为 `reviews/g1-<slug>.json`、`reviews/g2-<slug>.json`、`reviews/g3-<slug>.json`、`reviews/interpretation-review.json`；approval.gates 的证据必须引用 reviews/ 中的报告文件哈希。
