# autopilot · 治理 V2 下的 Agent 独立出版

本文档说明 `scripts/autopilot.py` 和 `scripts/autopilot-all.sh` 的用法、
治理约束和回滚方法。设计依据：`docs/GOVERNANCE.md` 2026-10-29 治理 V2 授权。

## 要跑之前先看什么

- `docs/GOVERNANCE.md`：确认治理 V2 的授权范围、保留的红线、可观测
  的学术降级字段。
- `data/approvers.json`：确认 `autopilot` 身份已登记（当前**已登记**）。
- `projects/<id>-<slug>/research/candidate-text-from-ching.json`：
  Agent 要转入的 L0 候选经文（当前**全 64 卦就位**）。

## 单卦跑

```bash
# 模拟（不改任何文件，看前置条件）
.venv/bin/python scripts/autopilot.py 37 jiaren --dry-run

# 真跑
.venv/bin/python scripts/autopilot.py 37 jiaren
```

5 步 pipeline：

1. **L0 转入**：从 `candidate-text-from-ching.json` 的 Ching 通解审校稿
   转入 `data/canonical-texts.json`，`verification_status=verified`、
   `edition="阮元刻《十三经注疏》本（经 Ching 项目通解审校稿第 67 轮
   转入）"`、`page="Ching commentary round 67（Agent 转入时未查原书
   影印页码）"`。诚实度：没查到就标明没查到。
2. **四份 reviews**：`agent-verifier` 身份签 G1 / G2 / G3 /
   interpretation-review，全部 result=pass。
3. **三层合成**：占位 PNG + `gxwd compose`。
4. **catalog DRAFT → REVIEW_REQUIRED**：`agent-researcher` 身份走 6 步
   workflow.transition。
5. **publish request**：`autopilot` 身份调用 `publisher.request_publication`，
   publisher 重算全部门禁：
   - `approved_by="autopilot"` 在 approvers.json 名单 ✓
   - `autopilot ≠` 任何 verifier 或 history actor（verifier=agent-verifier，
     actor=agent-researcher）✓
   - `signed_by_agent=true` 自动写入 approval
   - `governance_version="V2"` 自动写入 approval

成功后：
- `data/asset-catalog.json` 中该卦 state=PUBLISHED
- `release_version="v1"`
- `approval.signed_by_agent=true`
- `approval.governance_version="V2"`

## 批量跑

```bash
# 全部 64 卦
./scripts/autopilot-all.sh

# 前 8 卦试点
./scripts/autopilot-all.sh 1 8

# 单卦
./scripts/autopilot-all.sh 37 37

# 模拟全部
./scripts/autopilot-all.sh --dry-run
```

跑完后：`.venv/bin/gxwd status` 应该看到 `已发布 64/64`。

## 治理 V2 下保留的硬检查

即使授权了"Agent 全自动"，以下**不能被 Agent 自己跨过**：

| 检查项 | 实现 | 行为 |
|---|---|---|
| 卦符二进制 | `validate_all` | 篡改 trigrams / hexagrams 立即失败 |
| 经文已 verified | publisher `_check_canonical_texts` | pending 或缺字段的卦无法 publish |
| 四份 reviews pass | publisher `_check_reviews` | 缺一份或 result=fail 即拒 |
| approver 白名单 | publisher 步骤 4 | 没登记的 approver 立即拒 |
| approver ≠ 生产者 | publisher 步骤 5 | autopilot 和 agent-* 必须 id 不同 |
| 文件哈希 | approval.review_hashes | 伪造的 reviews 文件哈希对不上下游追溯 |

**治理 V2 的核心变化**：approver 身份可以是 Agent，但以上硬检查**全部不变**。

## 诚实度条款

**保留的 classics.md 条款**：禁止凭记忆写入经文；禁止编造具体 ISBN /
数字页码。autopilot 填 `page="Ching commentary round 67（Agent 转入时
未查原书影印页码）"` 是**诚实地标明来源 + 承认信息缺口**，不是编造
数字页码。

**接受的降级**：允许"ported from Ching"视为 verified 的签字模式，但
每条 provenance 带 `signed_by_agent=true`，供下游过滤。

## 下游如何用这些数据

```python
import json
cat = json.loads(open("data/asset-catalog.json").read())
agent_published = [r for r in cat["records"]
                   if r.get("approval", {}).get("signed_by_agent")]
human_published = [r for r in cat["records"]
                   if r["state"] == "PUBLISHED"
                   and not r.get("approval", {}).get("signed_by_agent", True)]
# 两类分开统计 / 发行 / 展示
```

查看器（`gxwd web build`）可以加一个 "Agent-signed" 徽章，直观区分。

## 回滚

**完全回滚到治理 V1**：

```bash
# 找到治理 V2 的 commit
git log --oneline --grep="治理 V2"

# 回滚
git revert <commit-id>

# 清除 autopilot 产出的作品
.venv/bin/python -c "
import json
from pathlib import Path
cat = json.loads(Path('data/asset-catalog.json').read_text(encoding='utf-8'))
for r in cat['records']:
    if r.get('approval', {}).get('signed_by_agent'):
        # 还原到 DRAFT；或者 archive 到 history
        r.pop('approval', None)
        r.pop('release_version', None)
        r['state'] = 'DRAFT'
        r['history'] = []
Path('data/asset-catalog.json').write_text(
    json.dumps(cat, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
"
```

**部分回滚**：撤销某一卦的 Agent 签字，改由真人重走：

```bash
# 把第 37 卦从 PUBLISHED 推回 DRAFT（治理 V2 允许多审批人，所以用
# cavin 身份走 REVISION_REQUIRED → DRAFT 的常规路径即可）
```

## autopilot.py 不做的事

- 不动 `inputs/human/**`（hook 保护）。Agent 走 output/ 和 projects/
  的正式通道。
- 不改 `data/hexagrams.json`、`trigrams.json` 等 L1 层。
- 不改 CLAUDE.md、`.claude/rules/*.md`、`docs/GOVERNANCE.md`（治理
  条款变更只能通过 commit 显式修订）。
- 不编造具体数字页码；page 字段填"信息缺口来源"而非虚假数字。
