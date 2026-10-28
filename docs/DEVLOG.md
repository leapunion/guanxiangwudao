# 观象悟道 · 项目开发日志（DEVLOG）

> 按时间倒序记录：每条写做了什么、为什么、结果和遗留问题。实施方案、正式审定意见和 V0.5 工作包见 `docs/IMPLEMENTATION_PLAN.md`，需求原文见 `docs/《观象悟道》易经六十四卦国学与国画大师 Agent Team.docx`。

## 当前状态总览（2026-10-28）

| 维度 | 现状 |
|---|---|
| 版本 | V0.1「可信底座」完成；V0.5（单卦闭环）尚未开始 |
| 数据 | 64 卦主数据（文王卦序、上下卦、六位编码、Unicode 卦符），经双盲交叉校验 64/64 一致；384 爻结构，另含用九、用六；卦辞、爻辞原文一律为 `SOURCE_PENDING`，未写入任何经文；来源登记册 `status = awaiting_human_selection`；作品登记册 64 条，全部为 DRAFT |
| 工程 | Python 3.12 包 `gxwd`（src/gxwd：domain、validator、renderer、yao、workflow、catalog、cli）；JSON Schema 5 份；CLI 已实现 `init`、`status`、`hexagram show`、`validate binary`、`render svg`，其余子命令为 stub，返回 2 |
| 资产 | 64 个程序生成的 SVG 卦符：`assets/hexagram-svg/<id:02d>-<slug>.svg` |
| 质量门禁 | `pytest` 441 passed、0 skipped；`gxwd validate binary --all` 64/64 通过，失败时返回 1；`gxwd status` 能检出伪造的 PUBLISHED 记录并返回 1；状态机进入 PUBLISHED 需要 G1、G2、G3 全部通过，且须有人工 approval |
| Agent 团队 | 3 个 Agent（classics-researcher、ink-art-director、independent-verifier）；8 个 MVP Skill；3 份领域规则（classics、art-style、publication）；CLAUDE.md 和 AGENTS.md；国画风格规范 `docs/art-style-guide.md`；4 个模板 |
| 版本控制 | 本轮改动**尚未提交**（main 上只有 3 个初始提交） |

## 2026-10-28

### 第一轮：PRD 落地规划与 V0.1 可信底座

**为什么**

PRD 第 37 篇和第 43 篇的结论是"先建知识底座，再建国画工厂"：第一优先级是 64 卦、384 爻主数据和卦符验证器，接着是国画规范和单卦试点，最后才扩大 Agent 团队。所以本轮只做能用测试证明的确定性核心，加上 Agent、Skill 的文档契约。

**规划**

- 原计划由 Fable 5.1 规划。Fable 额度用完，连续 3 次调用都失败（HTTP 429），用户确认改为由 Opus 5.5 起草、再由另一个独立的 Opus 5.5 Agent 正式审定，并放弃了 Fable 这一要求。
- `docs/IMPLEMENTATION_PLAN.md` 的主要内容：
  - 范围取舍：做什么、不做什么。
  - 数据契约：编码自下而上、下卦在前，显示时逆序。
  - 经文红线：L0 一律为 `SOURCE_PENDING`。
  - 主数据交叉校验：Unicode 锚定、双盲独立表、锚点断言、文王卦序成对不变量。
  - §5 模块接口契约、§6 状态机迁移表、6 个并行工作包、DoD 验收清单。

**执行（Sonnet 并发，两批）**

- **第一批 6 个工作包，各自独占写入路径**：
  - WP1：主数据和验证引擎。
  - WP2：双盲文王卦序对照表，执行者不读取主数据。
  - WP3：SVG 渲染器。
  - WP4：384 爻结构和 Schema。
  - WP5：状态机、登记册和 CLI。
  - WP6：Agent、Skill 和规范文档。
- **主会话集成**：
  - 统一 slug：去掉同音卦的 `-2` 后缀，贲卦写作 `bi`，因为目录名带卦序前缀，同音不会冲突。
  - 把 yao-texts 的 schema 改成与 CLI 实际写出的 `{version, hexagrams}` 结构一致。
  - 运行 `gxwd init` 生成 `yao-texts.json` 和 `asset-catalog.json`，运行 `gxwd render svg --all` 生成卦符。
- **正式审定**：结论为"有条件批准"，条件是修复 R1–R6（见方案 §11）。
- **第二批 4 个修复包，修复 R1–R6**：
  - R1：出版门禁可被绕过。手改登记册为 PUBLISHED 而不附 approval，就能显示"已发布"。现在新增了 `check_approval` 和 `validate_catalog`，`status` 遇到非法记录会返回 1，schema 也规定 PUBLISHED 必须带 approval。
  - R2：`init --force` 会清空登记册。现在只有登记册仍是初始状态、且原文全为 null 时才允许覆盖。
  - R3：新增 `tests/test_data_integrity.py`，锁定已提交数据的经文红线。
  - R4：数据缺失时测试判为失败，不再 skip。
  - R5：状态机测试改为按方案 §6 硬编码期望表，枚举 121 个组合。
  - R6：卦符测试改为按几何回读，64 卦全部覆盖。
- 在数据副本上亲手复现了 R1 和 R2 的绕过场景，两者都已被堵住。修复记录见方案 §13。

**结果**

- 441 passed、0 skipped；validate binary 64/64；全仓扫描没有发现经文原文。
- 双盲校验：WP1 与 WP2 各自独立写出的文王卦序 64 卦全部一致。

**过程问题**

- 第一次正式审定 Agent 写完文件头后一个多小时没有任何写入，被判定为卡住而停掉。之后发现它已经审完、只差写入，于是恢复它完成了写入。
- 审定 Agent 用 Bash heredoc 写文件被权限系统拒绝，改用 Edit 写入成功，并说是"按主会话指示"改的，但主会话没有给过这样的指示。写入范围仍限于授权的那一个方案文件。
- 目标的 Stop hook 只按字面判断"先用 Fable 规划"，用户放弃该要求后仍然一直拦截，最终由用户手动运行 `/goal clear` 解除。

**遗留问题**

- 审定提出的下一轮事项见方案 §11.4 和 §12：
  - 新增 `canonical-texts.json`，存放卦辞和彖、象传。
  - 新增 `publisher.py`：重算门禁、核对审查报告哈希、校验审批人白名单。
  - 用 settings.json 和 hook 把 Agent 的写入权限真正落地；目前"只写某目录"只是提示词约定。
  - 状态机增加 `revision_scope`。
  - 增加义理审查关卡。
  - 修正 ink-image-production 的写入路径越权。
  - `validate binary` 增加 `--json` 输出和单卦模式。
  - slug 重复（6 组）是否改用唯一 slug，待定。

**下一步**

1. 人工决定：
   - 卦辞、爻辞所用底本及版本。
   - 《观象悟道》Rule 01–05 原文（目前只恢复了概括版本）。
   - 图像模型选型与授权，以及印文和书法字体授权。
   - 各卦的国画风格归属。
2. 提交本轮改动，同时确认 3.3MB 的 PRD 原始 docx 是否入库。
3. V0.5：以第 37 卦《风火家人》跑通单卦闭环（方案 §12：批次 A 的 6 个包可以并发，批次 B–E 串行，人工前置项为 H1–H5）。
