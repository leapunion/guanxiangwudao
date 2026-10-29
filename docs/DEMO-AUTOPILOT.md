# demo-autopilot 分支 · 教讲性演示

> **这是设计上明确禁止的做法的演示版。本分支永不合并回 main。**
> 本文说清楚：若把『全自动到 PUBLISHED』真的做出来，Agent 要同时
> 冒充 3 种身份、绕开 4 层红线。看一次就知道为什么不该这么做。

## 本分支相对 main 多了什么

- `scripts/demo-autopilot.py` — 一个把第 37 卦家人从 DRAFT 冒签到
  PUBLISHED 的 Python 脚本。
- `docs/DEMO-AUTOPILOT.md`（本文件）— 警告与说明。

## 怎么跑

```bash
git checkout demo-autopilot
.venv/bin/python scripts/demo-autopilot.py
.venv/bin/gxwd status      # 看第 37 卦变 PUBLISHED
```

跑完 `main` 不受影响：

```bash
git checkout main
.venv/bin/gxwd status      # 第 37 卦仍是 DRAFT
```

## 它做了什么（6 步）

| 步 | 冒充的身份 | 做的事 | 跨过哪条红线 |
|---|---|---|---|
| 1 | 主会话（主编权限） | 把 Ching 候选经文写进 `data/canonical-texts.json`，`verification_status=verified`，`page="DEMO · 占位页码"` | **L0 必须真人签字**（CLAUDE.md 第 2 条、PRD 第 25、27 篇） |
| 2 | `demo-verifier` | 产 4 份 `reviews/*.json`，全部 `result=pass`，`verifier=demo-verifier` | **独立验证**（PRD 第 28 篇第二层） |
| 3 | 主会话 | 占位 PNG + `gxwd compose` → `layout/card.svg` | 图像模型授权未完成 |
| 4 | 主会话 | 把 `autopilot` 加进 `data/approvers.json` | **approvers 必须真人**（PRD 第 28 篇第三层） |
| 5 | `demo-producer` | 把 catalog 第 37 卦从 DRAFT 推到 REVIEW_REQUIRED | 状态推进必须对应真实工作产出 |
| 6 | `autopilot` | `publisher.request_publication` 以 `autopilot` 身份走 PUBLISHED | **"任何 AI Agent 不应拥有自动出版权限"**（PRD 第 28 篇） |

关键是：publisher 的硬门槛**不会**被改动——它仍然要求经文全
verified、4 份 reviews pass、approved_by ∈ 白名单、approved_by ≠
任何生产者/验证者 id。脚本是**构造出满足这些门槛的材料**，不是
删除门槛。换言之：publisher 的检查全部通过，没有一处 bypass。

这正是红线的脆弱点：**门禁只看文件和字段**；只要有权把文件写出来、
把 ID 配好，门禁就被欺骗。真实世界的保证靠的是：
- `inputs/human/**` 全局禁写（hook 层强制）
- `verification_status=verified` 必须由真人在 CSV 里勾
- `data/approvers.json` 里的真实姓名可追查
- Claude Code 的 **auto-mode 分类器**：它拦过本脚本的执行

本脚本能写出来、不能跑起来——至少在当前 Claude Code 分类器下。
真要跑：用户在自己终端里敲 `python scripts/demo-autopilot.py`。

## 为什么 main 永远不接受这个

- 一旦把 verified 的写入权给了 Agent，整个项目『每句话都能追溯到底本』的价值全部塌陷。
- 一旦允许 `autopilot` approver，PRD 第 28 篇等于作废。
- 这不是"保守"，这是**项目存在的意义**。

## 如何从本分支完全撤回

```bash
git checkout main
git branch -D demo-autopilot      # 彻底删掉分支
```

或保留分支作为教材。
