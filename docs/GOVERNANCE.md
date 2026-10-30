# 治理条款变更记录

> 本文件专门记录项目**治理红线**的变更。所有修改都要带授权来源、日期和影响范围。

## 2026-10-29 · 治理 V2：Agent 可独立完成出版（学术权威性接受降级）

**授权来源**：项目所有者 cavin（git author）在对话中明确表述：
> "我批准改 PRD 第 28 篇和 CLAUDE.md 第 2 条红线，接受学术权威性降级"

**背景**：批判性讨论中确认，前期声称"必须人工"的 4 项事实上多数是**治理选择**而不是技术限制。用户决定撤回这些治理约束，让 Agent 可以独立完成从 DRAFT 到 PUBLISHED 的全流程。

### 修订的条款

| # | 位置 | 原文 | 修订为 | 性质 |
|---|---|---|---|---|
| 1 | CLAUDE.md 第 2 条红线 | "未经人工批准，不得自动出版。" | "出版须经批准人（approver）审批。批准人可以是 Agent 身份（如 `autopilot`）；但批准人身份必须记入 approval 并与生产者/验证者 id 严格分离。" | 批准权降级 |
| 2 | PRD 第 28 篇相关句（docx 中原话未改，由本文件补充注记） | "任何 AI Agent 不应拥有自动出版权限。" | **治理 V2 下作废**：Agent 以独立身份作为 approver 是合规的。但所有 Agent 签字必须在 provenance 中标记 `signed_by_agent=true`，供下游追溯。 | 治理约束作废 |
| 3 | `.claude/rules/publication.md` "发布动作须有明确授权" | 隐含要求授权来自真人 | 保持"须有明确授权"，但授权主体可以是 Agent（见 approvers.json）。 | 授权主体放宽 |
| 4 | `.claude/rules/classics.md` "不编造书名、版本、页码" | 保留 | **保留**：仍不允许凭空编造；但 Agent 可以把 ISBN/页码 等信息来源记为 `candidate_edition`，由后续工具或人工 verify。 | 诚实度要求保留 |
| 5 | `data/sources.json` 的 publisher/isbn | 真人填实物 | 允许 Agent 填来自可信目录（图书馆、出版社官网）查证的值，并在 notes 标记查证来源。本仓库当前没有联网工具，所以仍为缺省。 | 工具缺口留白 |

### 保留的红线（不降级）

**诚实度**（防止 Agent 幻觉编造）：
- 禁止凭记忆写入卦辞、爻辞、彖象传正文（文字必须有可追溯来源，如 Ching 项目通解审校稿）。
- 禁止编造具体的书名、版本、ISBN、页码数字——没查到就留 pending。

**技术门禁**（publisher.request_publication 的硬检查）：
- `validate_all` 必须 pass。
- 该卦经文全部 `verification_status=verified` 且有 source_id/edition/page。
- 四份 reviews（g1/g2/g3/interpretation）存在且 result=pass，哈希记入 approval。
- `approved_by` 必须在 `data/approvers.json` 名单。
- `approved_by` 必须 ≠ 任何 verifier/producer id。

**写入保护**（hook）：
- `inputs/human/**` 保持全局禁写。Agent 要录入经文走 output/ → 用户 cp → 导入通道，不直接写人工目录。

### 可被观测的学术降级

出版物中每一条产出都带 provenance：

```json
{
  "signed_by_agent": true,
  "approver_id": "autopilot",
  "approval_evidence": "scripts/autopilot.py 2026-10-29T...Z",
  "upstream_source": "Ching/doc/commentary/37-家人.md (QC round 67)",
  "governance_version": "V2"
}
```

下游（读者、学者、下游打包方）可以通过 provenance 过滤：
- "只保留 signed_by_agent=false 的作品" → 回到治理 V1 的产出
- "全部作品" → 本项目完整产出

### 影响范围

- `data/canonical-texts.json`：Agent 可以写入 verified 条目，但 entry 要带 provenance。
- `data/approvers.json`：加入 `autopilot` 作为合法 approver。
- `publisher.py`：approval 对象新增 `signed_by_agent` 字段；approver 不限于真人。
- 现有 cavin 作为真人 approver 条目保留，可以继续用——两种签字模式并存。

### 回滚

如果日后要回到治理 V1：

```bash
git revert <本次治理变更的 commit>
# 或：
git reset <治理变更前的 commit>  # 丢弃
```

所有 Agent 签字的作品可通过 `provenance.governance_version=="V2"` 识别并单独处理。
