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

## 快速开始

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"

.venv/bin/python -m pytest          # 全量测试
.venv/bin/gxwd validate binary --all  # 64 卦编码验证（失败时返回非 0）
.venv/bin/gxwd hexagram show 37       # 查看单卦
.venv/bin/gxwd render svg --all       # 生成卦符 SVG
.venv/bin/gxwd status                 # 64 卦生产状态
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

## 待人工决定

1. 卦辞、爻辞所用底本及版本（国学主编）。
2. 《观象悟道》Rule 01–05 原文（目前只恢复了概括版本）。
3. 图像模型选型与授权，以及印文和书法字体授权。
4. 各卦风格归属（艺术主编）。
