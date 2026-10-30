# guanxiang-wudao（观象悟道）

《周易》六十四卦国学研究、国画创作、企业哲学转译与数字出版的 Agentic Studio。

定位：一卦一哲理 · 一卦一国画 · 一爻一故事 · 一卦一企业智慧。原则：Skill-first、经典为本、国画为魂、验证先行。

- 需求文档：`docs/《观象悟道》易经六十四卦国学与国画大师 Agent Team.docx`
- 实施方案：`docs/IMPLEMENTATION_PLAN.md`
- 全局规则：`CLAUDE.md`　Agent 导航：`AGENTS.md`

## 当前版本：V0.1（可信底座）

| 能力 | 状态 |
|---|---|
| 64 卦主数据（文王卦序、上下卦、六位编码、卦符） | ✅ 通过双盲交叉校验 |
| 384 爻结构（爻位、阴阳、爻名，另含用九、用六） | ✅ 结构完整 |
| 卦辞、爻辞原文 | ⏳ `SOURCE_PENDING`，等待人工选定底本 |
| SVG 卦符生成器 | ✅ 64 个，见 `assets/hexagram-svg/` |
| 单卦状态机 + 作品登记册 | ✅ 未经人工批准，不能进入 PUBLISHED |
| 3 个 Agent、8 个 MVP Skill、国画风格规范 | ✅ 文档契约 |
| 国画生成、单卦完整闭环 | ❌ 下一轮（V0.5） |

## V0.5 批次 A 完成 + 批次 B 预备（2026-10-29）

| 能力 | 状态 |
|---|---|
| publisher 门禁重算（approved_by 白名单 + ≠ 生产者） | ✅ `src/gxwd/publisher.py`；经文 verified + 审查哈希 + 白名单任一失败抛 PublicationError |
| 经文契约 canonical-texts + schema | ✅ `schemas/canonical-texts.schema.json`；L0 原文仍 SOURCE_PENDING，入库通道 `inputs/human/` 全局禁写 |
| 三层合成器 composer | ✅ `src/gxwd/composer.py`；Layer 1 主图 / Layer 2 SVG 卦符 / Layer 3 文字印章 |
| 权限 hook（inputs/human 全局禁写） | ✅ `.claude/hooks/guard_write.py`；带 CLAUDE_AGENT_ROLE 的子 Agent 只写 `projects/*/{research,art,reviews}/**` |
| 只读 64 卦查看器（`web/index.html`，self-contained） | ✅ ~300 KB 单文件，内嵌主数据 + SVG + G1 + 研究初稿 + 风格规范 |
| 预建 CLI：texts import/validate、publish request、compose、web build/serve | ✅ 11 个子命令；`gxwd web build/serve` 已可跑 |
| 批量脚本：import-and-gate.sh、import-and-gate-all.sh、pipeline.sh | ✅ `scripts/`；单卦和全量两个入口 |
| 候选资产：64 份 Ching 候选经文、64 份 CSV 预填稿、风格候选表 | ✅ `projects/<id>/research/candidate-text-from-ching.json` × 64；`output/canonical-input-prefilled/` × 64；`docs/art-style-assignment-candidate.md` |
| Release 包：pyproject metadata + LICENSE + CHANGELOG + PUBLISHING.md | ✅ `dist/gxwd-0.1.0.tar.gz` sdist 可装可跑；wheel 等 WP1 完成后可用 |
| 13 个 Agent 岗位骨架（3 个落地 + 10 个 specialist） | ✅ `.claude/agents/specialists/` × 10（由 R7 WP5 建） |
| 24 个 Skill（8 个 MVP + 16 个骨架） | ✅ `.claude/skills/` × 16 骨架（由 R7 WP4 建） |

## 快速开始

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"

.venv/bin/python -m pytest            # 全量测试
.venv/bin/gxwd validate binary --all  # 64 卦编码验证（失败时返回非 0）
.venv/bin/gxwd hexagram show 37       # 查看单卦
.venv/bin/gxwd render svg --all       # 生成卦符 SVG
.venv/bin/gxwd status                 # 64 卦生产状态

.venv/bin/gxwd texts validate         # 校验 canonical-texts
.venv/bin/gxwd compose 37 --master <png>  # 三层合成（需主图 PNG）
.venv/bin/gxwd web build && .venv/bin/gxwd web serve  # 只读查看器
./scripts/pipeline.sh 37 jiaren       # 单卦完整流水线
```

`gxwd init` 会根据主数据生成 `data/yao-texts.json` 和 `data/asset-catalog.json`（加 `--force` 覆盖已有文件）。

## 编码规则

阳 = 1，阴 = 0。`binary_bottom_to_top` 从初爻读到上爻，下卦在前、上卦在后。显示时六爻从上爻排到初爻，顺序与编码相反。例如第 37 卦《风火家人》：下离 101 + 上巽 011 = `101011`。

## 项目结构

```
data/          权威主数据（八卦、64 卦、384 爻、来源登记、作品登记册）
schemas/       JSON Schema
src/gxwd/      domain · validator · renderer · yao · workflow · catalog · cli
tests/         自动测试（含 tests/fixtures/ 独立文王卦序对照表）
.claude/       agents · skills · rules
templates/     研究、艺术 Brief、企业哲学、审校清单模板
assets/        hexagram-svg/（程序生成的卦符）
docs/          PRD、实施方案、国画风格规范
```

## 下一步要人工

1. 补 `data/sources.json` 的 publisher/isbn/page_system（对实物 ZYZY-RUAN 查看）。
2. 把 `output/canonical-input-prefilled/` 的 64 份 CSV 对实物核对后，抄到 `inputs/human/`（填实物页码、`verification_status=verified`）。
3. 图像模型选型 + 书法 / 印章授权（真实合约，Agent 不能代做）。
4. 艺术主编签字风格归属（`docs/art-style-assignment-candidate.md` 已列候选，等签字）。
5. 《观象悟道》Rule 01–05 原文（目前只恢复了概括版本）。

## 相关文档

- `docs/HOW-TO-RUN-AGENTS.md` — 逐步运行 Agent 的操作手册
- `docs/37-jiaren-walkthrough.md` — 第 37 卦家人试点闭环 walkthrough
- `docs/DEVLOG.md` — 开发日志（按时间倒序）
- `PUBLISHING.md` — 出版流程与人工审批门禁说明
- `CHANGELOG.md` — 版本变更记录
