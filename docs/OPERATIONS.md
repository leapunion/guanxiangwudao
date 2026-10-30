# 运营手册（Operations）

> **是什么**：本文档回答一个问题——这个项目**日常怎么运转**？
> 不是"怎么跑一次 autopilot"，是"每周、每月、长期，什么会发生、谁来做什么"。
>
> **治理前提**：本手册在治理 V2（2026-10-29 项目所有者授权）下有效。
> 条款见 `docs/GOVERNANCE.md`。

---

## 一、角色

| 角色 | 身份 | 职责 | 签字标记 |
|---|---|---|---|
| **cavin（项目所有者）** | 真人 | 变更治理条款、选底本、做真人签字、合入 PR | `signed_by_agent=false` |
| **agent-researcher** | Agent | 生成候选经文、研究稿、yao-cases | — |
| **agent-verifier** | Agent | 独立验证 G1/G2/G3 reviews | — |
| **autopilot** | Agent approver | 治理 V2 下的 Agent 批准人 | `signed_by_agent=true` |
| **读者** | 真人 | 通过 Issue 提交异议、功能请求、bug | — |

三类 Agent id 严格分离，`publisher.request_publication` 硬检查
`approved_by ≠ 任何生产者/验证者 id`，防止自批自己。

---

## 二、消费者看什么

| 入口 | 内容 | 需真人 |
|---|---|---|
| GitHub Pages（web viewer） | 64 卦只读查看器，含卦符 SVG + 候选经文 + 研究稿 | ❌ 不需，公开可访问 |
| GitHub Issues | 读者异议、功能请求、bug、治理提案、经文/底本修订 | ❌ 不需 |
| GitHub Releases | 每个版本的 wheel + sdist + CHANGELOG | ❌ 不需 |
| PyPI（规划中） | `pip install gxwd`，CLI + 数据底座 | ❌ 不需 |

读者在 web viewer 每张卦卡上有两个按钮：
- 📝 **指正此卡**：跳 `classical_text_issue.yml` 模板，预填 `hexagram_id`
- ✨ **建议改进**：跳 `feature_request.yml` 模板

---

## 三、一周运作周期（示意）

| 时刻 | 事件 | 触发源 | 产出 |
|---|---|---|---|
| 周一 09:00 Asia/Shanghai | Dependabot 扫依赖 | `.github/dependabot.yml` | 若有可升级依赖 → 开 PR，带 `dependencies` label |
| 周一 09:00 Asia/Shanghai | 周度健康检查 | `.github/workflows/periodic.yml` | pytest + validate + status 跑一遍；回退 → 开 `[health-check]` Issue |
| 任意时刻（读者触发） | 读者 Issue | web viewer 按钮或 GitHub 原生 | Issue 开到仓库，走对应模板的 required 字段校验 |
| PR 开启时 | CI | `.github/workflows/ci.yml` | pytest + build smoke 必须绿才能 merge |
| PR merge 时 | GH Pages 重建 | `.github/workflows/pages.yml` | 公开 viewer 自动刷新 |
| Tag `v*` push 时 | Release | `.github/workflows/release.yml` | 自动构 wheel + sdist + GitHub Release，notes 从 CHANGELOG.md 抽取 |

---

## 四、读者如何参与

### 发现经文有误 / 底本标注不准

1. 在 GH Pages viewer 打开对应卦
2. 点 "📝 指正此卡"（会跳到 `classical_text_issue.yml` 预填模板）
3. 必填：当前文本、建议文本、异议依据（哪个底本/校勘记）、问题类型
4. 选择处理方式：修正 original_text / 加 variant_readings / 替换为真人签字
5. 提交

→ cavin 看到后决定走哪条路径（见 "五、修订如何合入"）。

### 提功能请求

- 延展方向参考 `FINAL-DELIVERABLES.md` §六 A/B/C/D/E
- Issue 模板会要求填 "对已 PUBLISHED 作品的影响" + 4 条红线自检

### 发现 bug

- `bug_report.yml` 模板必填：版本、复现步骤、预期/实际行为、影响范围勾选

---

## 五、修订如何合入

读者提了一个经文修订 Issue 之后，cavin 的三种选择：

**路径 1 — 快修（Agent 替补签字）**

```bash
# cavin 在本地：
.venv/bin/python scripts/autopilot.py <id> <slug>  # 重跑该卦，带新修订
# → provenance.signed_by_agent=true，release_version 自动升
git add . && git commit -m "fix(H<id>): 应 #<issue>" && git push
```

→ CI 自动跑 → cavin 自己 review 并 merge → pages.yml 自动刷新 viewer。

**路径 2 — 真人签字（最权威，最慢）**

```bash
# cavin 在本地：
# 1. 翻实体底本（阮元刻《十三经注疏》等），对实物核对
# 2. 修改 data/canonical-texts.json 对应条目的 original_text、
#    provenance.source_id / page / signed_by_agent=false
# 3. 修改 data/asset-catalog.json 对应条目，把 state 从 PUBLISHED
#    退回 RESEARCHED（手工编辑；本项目不自动降级，防误操作）
# 4. 跑 publisher 以 cavin 身份重新签字
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
.venv/bin/gxwd publish request <id> \
  --approved-by cavin \
  --approved-at "$NOW" \
  --write
# → provenance.signed_by_agent=false（approver 身份非 Agent），
#   这才算"真人路径走通一卦"
```

> **注意**：当前 gxwd CLI 没有自动的 state transition 子命令，
> catalog state 的手工回退是刻意设计——治理 V2 下真人路径必须要有
> 显式的人类操作痕迹，不是一键完成的。

**路径 3 — 存为异文**

读者的异议并不否定当前文本，只是提供另一个底本的异读：加到
`variant_readings` 不替换 original_text，`release_version` 不升。

---

## 六、生产节奏（谁触发新一轮）

**本项目不自动生产新内容**。周度 `periodic.yml` 只做健康检查（不自动跑
autopilot 批量重出）。原因：

- 内容不是刷流水线能解决的；每一轮生产都应该由"读者提了问题 / cavin
  选了新底本 / 艺术模型选定 / 延展到新经典"这类**事件**触发。
- 自动化定期批量重跑 autopilot 会把 catalog 的 release_version 无
  意义地刷大，污染追溯链。

**真正的触发源**：

| 事件 | 触发什么 |
|---|---|
| 读者提交 `classical-text` Issue | cavin 评估后走路径 1/2/3 |
| cavin 选定了底本 | 走路径 2，重出全部 64 卦 |
| 艺术模型选定（art-style.md 解禁） | 全集 L3 重跑，1×1 占位 PNG 换成真实画作 |
| 延展到论语/道德经等（方向 A） | 新建 `../guanxiang-wudao-lunyu/` 或新 top-level 目录 |
| 任何 PR 合入 | pages.yml + 可选 release.yml |

---

## 七、运维红线

- **不要定期批量 autopilot 重跑**：污染 release_version 追溯链。
- **不要绕过 publisher 硬检查**：id 分离、review hashes、approver 白名单。
- **不要在 Issue 流程之外改 L0 数据**：所有 L0（original_text）变更
  必须有一个对应的 `classical-text` Issue 作为变更记录来源。
- **不要给 autopilot workflow 提升到 `contents: write`**：当前
  periodic.yml 只有 read，只能开 Issue，不能自己 commit。
- **治理条款（CLAUDE.md / .claude/rules）** 任何变更必须走
  `governance_proposal.yml` 的 V3+ 流程。

---

## 八、可观测性 / 看板

```bash
# 看每周运作全貌：
.venv/bin/gxwd status --json

# 看某卦的 approval provenance:
.venv/bin/gxwd hexagram show 37

# 看 CI / release / pages / periodic 的最近 10 次 run:
gh run list --repo leapunion/guanxiangwudao --limit 10

# 看待处理 Issue 分类:
gh issue list --repo leapunion/guanxiangwudao --json title,labels | \
  jq 'group_by(.labels[0].name // "none") | map({label: .[0].labels[0].name // "none", count: length})'
```

---

## 九、扩展方向落地建议

见 `FINAL-DELIVERABLES.md` §六 的 A/B/C/D/E。落地到 Issue：
- 用 `feature_request.yml` 模板的 "延展方向" 下拉选择 A-E
- Issue 一旦被 cavin label 为 `direction-A` ~ `direction-E`，就进入
  对应方向的 roadmap

---

**最后一句**：本项目不是"自动跑完 64 卦就完事"的脚手架，是**一台
由读者和 cavin 共同驱动、每一次修订都带追溯链的发布机器**。它的
生命力来自 Issue 和 PR，不来自定时任务。
