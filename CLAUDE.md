# 观象悟道 — Global Control Map

## Mission
建立一套有经典依据、艺术风格统一的《周易》六十四卦研究与出版系统：国学研究、国画创作、企业哲学转译、数字出版。

## Principles
- Skill 优先；只有需要独立上下文、专业判断或并行审查时才启用 Agent。
- 仓库是唯一真相源（system of record）。
- 经典原文、义理解释、现代经营应用必须分层保存，不得混写。
- 卦象数理是确定性的，由程序计算，不由模型推理。
- 不编造历史证据；宁可标记"尚无合适的可靠案例"。
- 未经人工批准，不得自动出版。

## Critical Rules（编码规则）
- 阳 = `1`，阴 = `0`。
- `binary_bottom_to_top` 自初爻读到上爻；前三位 = 下卦（内卦），后三位 = 上卦（外卦）。
- 展示时六爻自上而下（`lines_top_to_bottom` 为其逆序）。
- 卦符一律由 `gxwd.renderer` 程序生成 SVG，不由图像模型绘制；文字与印章是独立图层。
- 画作永不修改经典主数据；验证失败即阻断出版。
- **红线（本轮）：L0 经文一律为 `SOURCE_PENDING`，禁止凭模型记忆写入卦辞、爻辞、《彖传》《象传》原文。** 底本由人工选定后另起一轮校勘。
- 不编造书名、版本、页码；Rule 01–05 仅恢复了概括版本，原文待补，不得冒充原文。

## Source of Truth
- `data/trigrams.json`
- `data/hexagrams.json`
- `data/yao-texts.json`
- `data/sources.json`

## Navigation
- Agent 职责与单卦执行顺序：`AGENTS.md`
- Skills：`.claude/skills/`　Agents：`.claude/agents/`
- 领域红线：`.claude/rules/`（classics / art-style / publication）
- 艺术规范：`docs/art-style-guide.md`　模板：`templates/`
- 单卦工作区：`projects/<id>-<slug>/`（research / art / reviews）
- 验证：`tests/`　实施方案：`docs/IMPLEMENTATION_PLAN.md`　开发日志：`docs/DEVLOG.md`

## Publication
必须通过 G1、G2、G3 **并且**人工批准，才能进入 PUBLISHED。任何 Agent 都无权批准出版。

## 常用命令
```
.venv/bin/python -m pytest
gxwd validate binary --all
gxwd render svg --all
gxwd status
gxwd hexagram show <id>
```
