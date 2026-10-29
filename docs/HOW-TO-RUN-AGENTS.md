# 如何让 Agent 跑起来 · 如何自动化整条流水线

本项目的 Agentic 系统分三类角色：**确定性 CLI**、**Claude Code 会话内
Agent（Task tool）**、**人工决策点**。本文说清楚每类怎么调用、整条
单卦 pipeline 怎么跑、哪些边界不可越。

## 一、三类执行者

### 1. 确定性 CLI（`gxwd` 命令）

**不需要 LLM**，用标准库和 schema 校验，可以在任何环境跑：

| 命令 | 做什么 | 阻塞点 |
|---|---|---|
| `gxwd init` | 生成 `data/yao-texts.json`、`data/asset-catalog.json` | — |
| `gxwd status` | 打印 64 卦生产状态；检出伪造 PUBLISHED | — |
| `gxwd hexagram show <id>` | 显示单卦结构 | — |
| `gxwd validate binary --all` / `<id>` | G1 卦符二进制门禁；`--json` 产出报告 | — |
| `gxwd render svg --all` / `<id>` | 程序生成 SVG 卦符 | — |
| `gxwd texts import <csv> --hexagram-id <id>` | 把人工录入 CSV 导进 `data/canonical-texts.json` | 需要 CSV 已填 |
| `gxwd texts validate` | 对 `canonical-texts.json` 跑 schema | — |
| `gxwd compose <id> --master <png>` | 三层合成（主图 + 卦符 + 文字） | 需要主图 PNG（WP9 冻结） |
| `gxwd publish request <id> --approved-by <id> --approved-at <iso>` | 请求出版；publisher 重算 G1/G2/G3/经文/审批人白名单 | 任一门禁失败即拒 |
| `gxwd web build` / `gxwd web serve` | 构建 / 本地启动只读查看器 | — |

### 2. Claude Code 会话内 Agent（Task tool）

在 Claude Code 的 CLI 或 IDE 扩展里，Claude 调用这些子 Agent：

```python
# 伪代码：Claude Code 内部的 Task tool
Task(
    subagent_type="classics-researcher",
    description="第 37 卦家人研究稿",
    prompt="按 .claude/skills/yao-interpretation/SKILL.md 产出 "
           "projects/37-jiaren/research/interpretation.md + "
           "yao-cases.json + business-philosophy.md。"
           "本轮底本 ZYZY-RUAN；经文引用用 [[H37-...]] 的 text_id。",
)
```

| Agent | 职责 | 产出路径 | 权限（hook 强制） |
|---|---|---|---|
| `classics-researcher` | 卦义研究、历史故事 A/B/C/D 评级、企业哲学映射 | `projects/*/research/**` | 只读 data/、docs/ |
| `ink-art-director` | 艺术 Brief、主图参数、创作记录 | `projects/*/art/**` | 只读已审定卦义、art-style-guide |
| `independent-verifier` | G1 / G2 / G3 / 义理审查 | `projects/*/reviews/**` | 读全部待审产物 |

**权限由 `.claude/hooks/guard_write.py` 执行**：带 `CLAUDE_AGENT_ROLE`
的 Agent 只能写到各自路径；超出就 block。

### 3. 人工决策点（Agent 不代做）

| 事 | 为什么人工 |
|---|---|
| 选 L0 底本 publisher / isbn / 具体页码 | 看实物版权页；Agent 无可靠途径查证，填就是编 |
| `inputs/human/*.csv` 的 `original_text` 签字 | `verification_status=verified` 等于主编签字；`inputs/human/**` 全局禁写 |
| 图像模型选型与商用授权 | 真实世界合约（服务商条款、版权归属） |
| 书法字体 / 印章篆刻授权 | 版权合约 |
| 艺术主编对国画风格归属签字 | 艺术判断 |
| `publish request` 的 `--approved-by` | PRD 第 28 篇"任何 AI Agent 不应拥有自动出版权限" |

## 二、单卦 pipeline（AGENTS.md DAG）

```
┌─────────────────────────────────────────────────────────────────┐
│  主数据 → G1 → L0 录入 → 义理研究 → 义理审查                     │
│                              ↓                                   │
│  ← G3 ← G2 ← 三层合成 ← 主图生成 ← 艺术 Brief                   │
│                              ↓                                   │
│                        人工终审 → PUBLISHED                      │
└─────────────────────────────────────────────────────────────────┘
```

### 一键跑能自动的部分

```bash
./scripts/pipeline.sh 37 jiaren
```

脚本会：
1. `gxwd hexagram show 37` 验证主数据
2. `gxwd validate binary 37 --json --out ...` 产 G1 报告
3. 若 `inputs/human/37-jiaren-canonical.csv` 存在，跑 `import-and-gate.sh`；否则**停下并打印下一步**
4. 检查研究稿；若无，提示在 Claude Code 会话里 `Task(classics-researcher)`
5. 检查义理审查；若无，提示 `Task(independent-verifier)`
6. WP9 艺术 Brief 冻结中（H3 授权前不启动）
7. 若有主图，跑 `gxwd compose 37 --master ...`
8. 提示在会话里跑 G2 / G3
9. 提示人工终审命令

每个"Agent 点"脚本都打印具体的 `Task(...)` 调用示例，复制到 Claude Code
会话里即可。

### 全链路自动化的边界

- **完全自动的最大边界** = 人工只做 §一·3 列出的 6 件事；其余（研究稿、
  艺术 Brief、G1–G3、合成、哈希、门禁重算）全部 Agent/CLI 做。
- **本项目不支持"全自动"到 PUBLISHED**。这是设计：publisher 要求
  `approved_by` 在白名单里且 ≠ 任何生产者/验证者 id——Agent 不能同时
  当生产者和审批人。
- **64 卦并发自动化**：从结构上可行（每卦项目目录独立），但先把一卦
  跑通再并发。

## 三、第一次跑通的最短路径

**前提**：已经 `uv pip install -e .`，`gxwd` 可执行。

```bash
# 1. 一步看现状
./scripts/pipeline.sh 37 jiaren

# 2. 根据脚本输出的提示，你会卡在"L0 经文录入（人工点）"
cp output/canonical-input-prefilled/37-jiaren-canonical.csv inputs/human/
$EDITOR inputs/human/37-jiaren-canonical.csv
# 对照手头的《周易正义》实物：
#   - page 列填具体页码（如 "19上"）
#   - verification_status 列从 pending 改为 verified
./scripts/pipeline.sh 37 jiaren     # 重跑；它会继续到研究稿这一步

# 3. 启 Claude Code 会话，在里面跑：
#    Task(subagent_type: classics-researcher, ...)
#    Task(subagent_type: independent-verifier, ...)   # 义理审查
# （第 37 卦研究稿第四轮已经做过一次，但没经义理审查）

# 4. H3 完成（图像模型 + 书法印章授权）后：
#    Task(subagent_type: ink-art-director, ...)
#    由主编跑图像模型，把 master.png 放到 projects/37-jiaren/art/
#    ./scripts/pipeline.sh 37 jiaren   # 继续到合成 → G2 → G3

# 5. 终审：
.venv/bin/gxwd publish request 37 \
  --approved-by cavin \
  --approved-at $(date -u +%Y-%m-%dT%H:%M:%SZ)
# publisher 重算全部门禁；通过则 catalog 迁 PUBLISHED
```

## 四、批量 64 卦

主编把全部 64 份 CSV 填好后：

```bash
./scripts/import-and-gate-all.sh      # 批量跑 import + G1
# 剩下步骤（研究稿、Brief、合成、G2/G3、publish）还是一卦一卦
# 走——因为每一步都有可能需要人工介入。
```

要并发跑多卦的研究稿或艺术 Brief，在 Claude Code 会话里一次发多个
`Task` 调用。每个 Agent 独占不同 `projects/<id>-<slug>/` 子目录，不会
冲突（权限 hook 保证）。

## 五、看进度

```bash
.venv/bin/gxwd status                 # 11 态分布：DRAFT/RESEARCHED/.../PUBLISHED
.venv/bin/gxwd web serve              # 浏览器查看 http://127.0.0.1:8000
```

查看器会显示每卦的 G1 徽章、候选经文、研究稿（如有）、国画风格候选、
art-style-guide 全文。

## 六、常见误区

- ❌ 让 Agent 直接写 `data/canonical-texts.json` 跳过 `inputs/human/` —— auto-mode 分类器已拦过多次；破坏 L0 真人签字。
- ❌ 填 `verification_status=verified` + Agent 自编的 page —— 冒签。
- ❌ `publish request` 时 `approved_by` 与 Agent 当生产者的 id 相同 —— publisher 拒绝（白名单 ≠ 生产者）。
- ❌ `inputs/human/**` 下让 Agent 补 CSV —— hook 全局禁写。
- ✅ Agent 产出"候选"文件（放 `projects/*/research/`、`output/`、
  `docs/`），人工再把 **决定性字段**（verified / approved_by / page /
  publisher 等）填进去。
