# 治理条款变更记录

> 本文件专门记录项目**治理红线**的变更。所有修改都要带授权来源、日期和影响范围。

## 2026-11-04 · 治理 V3：选定图像模型 FLUX.1 schnell（art-style.md 第 10 条红线解禁）

**授权来源**：项目所有者 cavin 在 [Issue #20](https://github.com/leapunion/guanxiangwudao/issues/20) 中明确回复 "approve V3"（2026-11-04）。

**依据**：[RFC #001 图像模型选型](rfc/001-art-model-selection.md)。12 候选对比后选 FLUX.1 schnell via MFLUX，核心理由——唯一同时满足 (a) Apache 2.0 无限制商用 (b) Mac Apple Silicon 本地可跑 (c) 零 API 成本 (d) shuimo 风格可用 四条硬约束。

### 变更

| # | 位置 | 原文 | 修订为 | 性质 |
|---|---|---|---|---|
| 1 | `.claude/rules/art-style.md` 第 12 行 | 本轮未选定图像模型 | 本轮选定 **FLUX.1 schnell via MFLUX**（Apache 2.0，可商用；依据 RFC #001）。生成参数必须记入 `projects/*/art/provenance.json`。对外必须诚实标注"AI 生成艺术" | 解禁 + 补 provenance 要求 |

### 保留的红线（V3 下不降级）

- `art-style.md` 第 8 行"图像模型不得绘制汉字、卦符或印章" **保留**。三层合成器的 Layer 2 卦符 SVG + Layer 3 文字印章继续由程序生成，不走图像模型
- `classics.md` 全部红线 **保留**（经文诚实度）
- `publication.md` 全部红线 **保留**（publisher 硬检查）
- `art-style.md` 五色 palette + 留白 35-45% + 卦象结构精确 **保留**
- 治理 V2 下 Agent 签字条款 **保留**（agent_signed 作品继续合规）

### cavin 接受的代价

- **图像来源权威性**：生成图是 AI 艺术，不是传统名家真迹。对外文案必须诚实标注，不可冒充
- **汉字幻觉风险**：FLUX 家族对汉字有生成幻觉（RFC §9 已记录）。缓解：prompt 加 `no text / no characters / no seals` + composer 的 Layer 2/3 叠加自然遮盖
- **艺术水准**：schnell 对 shuimo 的 native 理解有限。首轮 POC 质量可能粗糙；cavin 对 POC 满意后才铺开 64 卦
- **可复现性要求**：所有 provenance 必须记 (model, prompt, seed, steps, quantization)；同 seed 应产出同图

### 回滚方法

- 删 `projects/*/art/master.png` 替换为 1×1 占位 PNG（保留文件路径，只改内容）
- `art-style.md` 第 12 条还原为"本轮未选定图像模型"
- 本文件不删 V3 条目（保追溯），追加一条 "YYYY-MM-DD · 治理 V3 回滚：原因 XXX"
- 已 PUBLISHED 作品 `release_version` 升级到 vN+1，approval 的 canonical_text_version 和 review_hashes 不变（只是画作换占位）

---

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
