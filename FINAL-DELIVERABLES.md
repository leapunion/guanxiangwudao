# 《观象悟道》· 最终交付说明

> **性质**：这是整个项目向使用者（学者、工程师、读者、潜在复用者）交付的"验收说明书"。读完它应该能回答三件事：**这是什么 / 能用来做什么 / 边界在哪**。

- **仓库**：`guanxiang-wudao`
- **交付日期**：2026-10-29
- **当前版本**：0.1.0（gxwd 核心包）+ 治理 V2（Agent 可独立出版）
- **git 提交数**：35+
- **测试**：pytest 631 passed、0 skipped、0 xfailed

---

## 一、这是什么

《观象悟道》是一个**六十四卦国学 + 国画 + 企业哲学的 Agentic 创作与出版系统**。它的实际交付面有两个层次：

**第一层：周易六十四卦的数字知识底座 + Agentic 工作流框架**（**本次 100% 交付**）
- 结构化的 64 卦主数据（文王卦序、Unicode 卦符、二进制编码、双盲校验）
- 从"研究 → 校勘 → 艺术 → 合成 → 审查 → 出版"的完整工作流（CLI + Agent + 真人三类执行者分离）
- 可追溯的 provenance 机制（每个产出知道是谁签的、依据什么签的）
- 治理版本机制（V1 真人签字 / V2 Agent 可独立出版，两种模式并存）

**第二层：具体的 64 卦 PUBLISHED 作品集**（**本次未完整交付**，由使用者按路径 A/B/C 决定如何完成）
- L0 卦辞 / 爻辞 / 彖象传正文
- 64 幅国画主画 + 384 幅爻画（可选）
- 企业哲学卡片
- 画册 / DOCX / PDF

**本次交付的核心价值**：**不在于已经出版 64 卦**，而在于**证明了一套可审计的 Agentic 工作流**——它既能承载真人学术权威，也能在用户授权下让 Agent 独立完成全流程，并把两种模式的差异明确地标注给下游。

---

## 二、交付清单

### L1 技术底座 ✅

| 项 | 位置 | 说明 |
|---|---|---|
| Python 包 `gxwd` | `src/gxwd/` | 11 个模块：domain / validator / renderer / yao / workflow / catalog / cli / texts / publisher / composer / web |
| CLI 子命令 | `src/gxwd/cli.py` | `init / status / hexagram show / validate binary / render svg / texts import / texts validate / compose / publish request / web build / web serve` |
| JSON Schema | `schemas/` | 10 份：trigrams / hexagrams / yao-texts / sources / asset-catalog / canonical-texts / approvers / art-style / skill-result / review-report / execution-plan |
| 测试 | `tests/` | 631 passed，含 R1–R10 回归、R6 几何回读、双盲 kingwen 对照 |
| 发布包 | `dist/gxwd-0.1.0-py3-none-any.whl` (~1MB) + `.tar.gz` (~80KB) | wheel 装到 site-packages 后 CLI 可跑；见 `PUBLISHING.md` |

### L2 数据资产 ✅

| 项 | 位置 | 说明 |
|---|---|---|
| 64 卦主数据 | `data/hexagrams.json` | 文王卦序、上下卦、六位编码、Unicode 卦符；经双盲交叉校验 64/64 一致 |
| 八卦规范表 | `data/trigrams.json` | 乾 111 坤 000 … 兑 110；validator 的 CANONICAL_TRIGRAMS 钉死规范值 |
| 384 爻结构 | `data/yao-texts.json` | 爻位、阴阳、爻名（初九/六二…）、乾用九、坤用六；原文 `SOURCE_PENDING`（本次未录入 L0） |
| 64 个 SVG 卦符 | `assets/hexagram-svg/` | 纯程序生成；可嵌入出版物 |
| 底本登记 | `data/sources.json` | ZYZY-RUAN 阮元刻《十三经注疏》本《周易正义》；publisher/isbn/page_system 由主编补 |
| 审批人名单 | `data/approvers.json` | 两类：`cavin`（真人）+ `autopilot`（Agent，治理 V2） |
| 风格候选归属 | `data/art-style.json` | 64 卦 × 4 风格（G 工写青绿 / M 文人水墨 / S 苍润山水 / P 人物故事）；signed_by/signed_at 待艺术主编签字 |
| 64 份 Ching 候选经文 | `projects/*/research/candidate-text-from-ching.json` | 从 Ching 项目通解审校稿第 67 轮抽的通行本经文；带 provenance 但不自动进 L0 |
| 64 份 CSV 预填稿 | `output/canonical-input-prefilled/*.csv` | original_text + edition 已填（Ching 来源）；主编只需填 page + 改 verified |
| 64 份 G1 门禁报告 | `projects/*/reviews/g1-binary-validation.json` | result=pass |

### L3 治理资产 ✅

| 项 | 位置 | 说明 |
|---|---|---|
| 项目红线 | `CLAUDE.md` | Mission、Principles、Critical Rules、Source of Truth、Publication 要求 |
| Agent 导航 | `AGENTS.md` | 13 Agent 岗位 + 24 Skill 地图 + 9 步 DAG + reviews/ 文件名约定 |
| 领域规则 | `.claude/rules/` | classics.md / art-style.md / publication.md |
| Agent 定义 | `.claude/agents/` | 3 核心（classics-researcher / ink-art-director / independent-verifier）+ `specialists/` 10 骨架 |
| Skill 定义 | `.claude/skills/` | 8 MVP + 19 新增，覆盖 PRD §五 全部 24 Skill |
| 写入权限 hook | `.claude/hooks/guard_write.py` + `settings.json` | PreToolUse hook：`inputs/human/**` 全局禁写；角色子 Agent 只能写各自 `projects/*/{research,art,reviews}/**` |
| **治理版本** | `docs/GOVERNANCE.md` | **V2**（2026-10-29）：Agent 可作为 approver；每条 Agent 签字带 `signed_by_agent=true` provenance；可回滚 |

### L4 工作流 ✅

| 脚本 | 用途 |
|---|---|
| `scripts/pipeline.sh <id> <slug>` | 单卦人工+Agent 混合 orchestrator；每遇到 Agent 点或人工点都提示 |
| `scripts/import-and-gate.sh <id> <slug>` | 单卦 L0 CSV 导入 + G1 产出 |
| `scripts/import-and-gate-all.sh` | 批量扫 `inputs/human/*.csv` 导入 |
| `scripts/autopilot.py <id> <slug> [--dry-run]` | **治理 V2 下 Agent 独立单卦出版**（身份分离：agent-researcher / agent-verifier / autopilot） |
| `scripts/autopilot-all.sh [start] [end] [--dry-run]` | **治理 V2 下批量 64 卦自动出版** |
| `scripts/prepack.sh` | 构建 wheel 前把 data/assets/schemas/templates 复制到 `src/gxwd/_bundled/` |
| `scripts/build-web.py` | 查看器构建（历史兼容 shim；主入口是 `gxwd web build`） |

### L5 展示层 ✅

| 项 | 位置 | 说明 |
|---|---|---|
| 只读 64 卦查看器 | `web/index.html`（派生，`gxwd web build` 生成） | ~300KB self-contained HTML；8×8 卦符网格 + 风格过滤 + 单卦详情（SVG / 候选经文 / WP6 研究稿 / art-style-guide 全文 / Agent-signed 徽章） |
| CLI JSON 输出 | `gxwd status --json` | 结构化数据，含 counts / published / agent_signed / human_signed |

### L6 文档 ✅

| 文档 | 说明 |
|---|---|
| `README.md` | 项目入口、快速开始、项目结构、待人工项 |
| `CHANGELOG.md` | 版本变更记录（0.1.0 + 治理 V2） |
| `PUBLISHING.md` | PyPI 发布流程 + 已知限制 |
| `LICENSE` | MIT |
| `docs/IMPLEMENTATION_PLAN.md` | 落地方案 + 正式审定意见 + V0.5 工作包 |
| `docs/DEVLOG.md` | 开发日志（7 轮，按时间倒序） |
| `docs/GOVERNANCE.md` | **治理条款变更记录（含 V2 授权）** |
| `docs/HOW-TO-RUN-AGENTS.md` | 三类执行者 × 单卦 DAG × 操作手册 |
| `docs/AUTOPILOT.md` | autopilot 治理 V2 下用法 + 保留的硬检查 + 回滚方法 |
| `docs/37-jiaren-walkthrough.md` | 第 37 卦家人试点闭环手册 |
| `docs/CANONICAL-INPUT-GUIDE.md` | 主编经文录入指南 |
| `docs/art-style-guide.md` | 国画艺术规范 |
| `docs/art-style-assignment-candidate.md` | 64 卦风格候选表 |
| `docs/image-and-licensing-decisions.md` | 图像模型 / 书法 / 印章授权冻结记录 |
| `docs/sources-candidate.md` | 底本书目候选草稿 |

### L7 实证产出 ❌（**本次未交付**）

| 项 | 当前 | 完成所需 |
|---|---|---|
| PUBLISHED 作品 | **0 / 64** | 走路径 A / B / C 之一（见下节） |
| 国画主画 | **0 / 64** | 图像模型授权 + 艺术主编签字 |
| 爻画 | **0 / 384** | 可选，PRD 建议 |
| 可发行物（画册 / DOCX / PDF） | **0** | 走完上面 PUBLISHED |

---

## 三、验收标准

| 门 | 要求 | 状态 |
|---|---|---|
| 技术 | pytest 全绿、门禁可阻断、hook 守得住、wheel 可装 | ✅ 631 passed；demo-autopilot 分支证明伪造 PUBLISHED 被拦；wheel 装到干净 venv 后 CLI 跑通 |
| 数据 | 64 卦唯一、校验、双盲对照、Unicode 锚定、锚点断言 | ✅ 全部已过 |
| 治理 | V1 + V2 并存、provenance 完整、下游可过滤 | ✅ `signed_by_agent` 字段贯穿 approval、web 徽章、`status --json` |
| **产出** | 至少 1 卦 PUBLISHED、至少 1 幅主画、1 份可发行物 | ❌ **全部缺** |

**本次交付可过 3/4 门**。第 4 门交给使用者按路径决定。

---

## 四、使用者可选的三条路径

### 路径 A · 学术权威版

**适合**：想做一本可引用、可长期保存、可向学术界展示的《观象悟道》正式著作。

**步骤**：
1. 回滚治理 V2：`git revert <治理 V2 commits>`
2. 真人完成 PRD 第 42 篇 DoD 列的所有人工项（底本签字、经文核对、授权、艺术主编）
3. 走 `docs/37-jiaren-walkthrough.md` 的 11 节单卦手册
4. 完成 8 卦试点（PRD 第 18 篇推荐：乾、坤、屯、蒙、泰、否、家人、革）
5. 批量 56 卦

**时间**：1–3 个月
**产出**：可引用的学术出版物
**学术权威性**：高（每条经文有真人签字、每幅画有艺术主编把关）

### 路径 B · Agentic 实证版

**适合**：验证 Agentic 工作流本身；对外展示"治理可观测的 Agent 独立出版"案例；开源作为参考实现。

**步骤**：
```bash
# 一键跑 64 卦
./scripts/autopilot-all.sh
.venv/bin/gxwd status --json | jq
.venv/bin/gxwd web build && open web/index.html
```

**时间**：5 分钟
**产出**：64 卦 PUBLISHED，全部带 `signed_by_agent=true`
**学术权威性**：低（AI 多重审校，provenance 透明可追溯；下游用 `signed_by_agent` 过滤即可区分）
**开源价值**：高（这套工作流 + 治理机制是业界缺的）

### 路径 C · 混合版（推荐）

**适合**：既要有真人把关的学术基线，又要展示 Agent 工作流能力。

**步骤**：
1. **真人走第 37 卦家人**（PRD 推荐试点，`docs/37-jiaren-walkthrough.md`）
2. **autopilot 其余 63 卦**：`./scripts/autopilot-all.sh 1 36; ./scripts/autopilot-all.sh 38 64`
3. **汇总**：
   - 1 卦 `signed_by_agent=false`（真人学术基线）
   - 63 卦 `signed_by_agent=true`（Agent 工作流证明）

**时间**：第 37 卦 1–2 周（真人节奏） + 批量 5 分钟
**产出**：
- 学术基线作品 × 1：可引用、可展示权威出版
- 工程证据 × 63：展示工作流 + 治理机制
**学术权威性**：**双轨**，供下游按需过滤

---

## 五、技术规格

### 安装

```bash
# 从源码（当前）
git clone <repo>
cd guanxiang-wudao
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"

# 从 wheel（0.1.0+）
./scripts/prepack.sh
python -m build
pip install dist/gxwd-0.1.0-py3-none-any.whl
```

### 依赖

- Python 3.12+
- `jsonschema>=4.20`
- 开发：`pytest>=8`、`build>=1.0`、`twine>=4.0`

### 环境变量

- `GXWD_DATA_DIR`：覆盖 data 目录（默认仓库根 `data/` 或 wheel bundled `_bundled/data/`）
- `CLAUDE_AGENT_ROLE`：Agent 角色（classics-researcher / ink-art-director / independent-verifier），影响 hook 的写入权限

### 查看器嵌入

查看器是 self-contained HTML（约 300KB）。可以：
- 直接嵌到网站 iframe
- 分发给单个读者
- 作为教学 / 展示工具

---

## 六、延展方向

本项目的架构可以**完全复用**于其他场景。

### A. 同构国学数字化

| 经典 | 复用度 | 需要改的 |
|---|---|---|
| 《论语》 | ~95% | L0 schema 换成章节 × 条目；无"卦符"；主数据改为 20 篇 |
| 《道德经》 | ~90% | 81 章，无爻结构；底本约定清晰（王弼本） |
| 《孟子》《大学》《中庸》 | ~90% | 类似《论语》 |
| 《坛经》《庄子》 | ~85% | 需要定义自己的 L0 结构 |

**可复用的核心**：publisher 的门禁、hook 的权限层、provenance 机制、治理版本模型、web 查看器模板。

### B. 国画艺术生成系统

本项目的"4 种风格 × 艺术 Brief × 三层合成"模型可以直接用于：
- 山海经图系列
- 二十四节气
- 十二生肖
- 唐诗三百首插画
- 道藏 / 佛教艺术

**可复用的核心**：art-style.json 的四分类、composer 的三层合成（master 画 + 卦符/符号层 + 文字层）、ink-art-director Agent 骨架。

### C. 治理 V2 作为"Agent + 人工双模"模板

**本项目的 governance_version 机制**可以搬到任何"AI 建议 + 人工签字"场景：

| 场景 | V1（真人） | V2（Agent 可独立） | provenance 字段 |
|---|---|---|---|
| 医疗诊断 | 医生签字 | AI 建议 + 医生 review 后签字 | `signed_by_physician` + confidence |
| 法律文书 | 律师定稿 | AI 起草 + 律师批准 | `drafted_by_ai` |
| 学术论文 | 作者署名 | AI 整理资料 + 作者审 | `ai_assisted_sections` |
| 新闻稿 | 编辑终审 | AI 初稿 + 编辑 review | `editorial_pass` |

**可复用的核心**：GOVERNANCE.md 的版本记录模型、publisher 的 approved_by ≠ 生产者的硬检查、signed_by_agent 字段 + 下游过滤。

### D. Agentic 工作流可信门禁（纯技术开源）

抽取：
- `src/gxwd/publisher.py` 的"重算验证 + 哈希追溯 + 白名单 + 身份分离"模型
- `.claude/hooks/guard_write.py` 的"全局禁写 + 角色路径 + 分类器"分层
- `docs/GOVERNANCE.md` 的治理版本机制
- `tests/test_publisher.py` 的反例覆盖

可以独立于本项目开源为 "AgentOps 可信门禁模板"。目前 LangChain / AutoGen 生态里**缺这一层**。

### E. 本项目的长期演化（PRD 第 23 篇原设）

- 《观象悟道》数字国画馆（展示型）
- 《周易》交互式研习系统（教学型）
- 企业家易经平台（决策参考型，严禁占卜）
- 国学与国画出版工厂（内容生产线）

---

## 七、学术边界 / 免责声明

**本项目接受的学术降级**（治理 V2 下）：

1. **L0 原文的来源可追溯但不等于真人逐字校勘**：L0 文字从 Ching 项目第 67 轮通解审校稿转入，Ching 以通行本《周易正义》为底本。本项目**没有真人对阮刻实物逐字签字**（除非走路径 A/C 让真人完成）。
2. **具体 ISBN / 影印本页码缺省**：Agent 无联网查证通路；留 TODO 不编造。
3. **历史故事可能"宁可缺不编"**：PRD 第 26 篇要求历史故事按 A/B/C/D 等级标注，没有可靠案例时标"尚无"。
4. **国画作品带 provenance.signed_by_agent 标记**：**治理 V2 下的作品不是真人艺术主编签字**，而是 Agent 多重审校。读者 / 下游可以通过 `signed_by_agent=true` 过滤。

**本项目仍坚持的学术诚实度**：
- **不编造原文**：卦辞 / 爻辞 / 彖象传正文只能从可追溯源头（Ching、将来的真人录入）流入。
- **不编造出版元数据**：publisher / ISBN / 具体数字页码不填就留空。
- **不编造史实**：历史故事允许"尚无案例"而非虚构。
- **每一条产出都有 provenance**：可以反向追溯到源头。

**对读者的建议**：
- 用作研究参考：务必检查每条经文的 `source_id` 和 `signed_by_agent` 字段。
- 用作教学材料：建议标注"本材料含 AI 生成内容"。
- 用作出版物：建议走路径 A / C 让真人把关，不建议纯 B。
- 用作企业哲学参考：严禁作为"预测吉凶"或投资决策依据。本项目的企业哲学卡片是**决策质询工具**，不是预测工具。

---

## 八、许可与致谢

### 许可

MIT License（见 `LICENSE`）。

### 上游致谢

- **Ching 项目**（`/Users/cavinfu/Desktop/devs/Ching`）：64 卦通解审校稿第 67 轮后的通行本经文作为本项目 L0 候选的来源。本项目维护者与 Ching 项目维护者是同一人（cavin），内部授权复用。
- **阮元刻《十三经注疏》本《周易正义》**：王弼、韩康伯注；孔颖达疏。本项目登记的底本（source_id=ZYZY-RUAN）。
- **PRD 原作者**：cavin（见 `docs/《观象悟道》易经六十四卦国学与国画大师 Agent Team.docx`）。
- **治理 V2 授权人**：cavin（见 `docs/GOVERNANCE.md` 2026-10-29 条目）。

### 引用本项目

```bibtex
@software{guanxiang_wudao_2026,
  title  = {观象悟道: Agentic Studio for I Ching's 64 Hexagrams},
  author = {cavin},
  year   = {2026},
  url    = {https://github.com/cavinfu/guanxiang-wudao},
  version = {0.1.0 + Governance V2},
  note   = {Mixed human/agent authorship; see docs/GOVERNANCE.md and provenance.signed_by_agent field}
}
```

---

## 九、如何开始

**读者 / 学者**：
```bash
.venv/bin/gxwd web build && open web/index.html
```

**工程师 / 二次开发**：
- 读 `docs/HOW-TO-RUN-AGENTS.md`
- 读 `docs/AUTOPILOT.md`
- 读 `src/gxwd/publisher.py` 的 `request_publication`（理解门禁模型）
- 读 `.claude/hooks/guard_write.py`（理解权限模型）

**项目维护者**：
- 选路径 A / B / C（见本文第四节）
- 跑 `scripts/autopilot.py 37 jiaren --dry-run` 预检
- 走 `docs/37-jiaren-walkthrough.md` 开始第一卦

---

**项目至此交付。真正的"按按钮"在使用者手里。**
