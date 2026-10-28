# 《观象悟道》落地实施方案 — Round 1（V0.1 + V0.5 骨架）

> 依据：`docs/《观象悟道》易经六十四卦国学与国画大师 Agent Team.docx`（PRD V1.0 · Agent OS V1.0，第 1–43 篇）
> 规划：Opus 5.5 起草 · Opus 5.5 独立正式审定（原定 Fable 5.1，因额度不足由用户确认改用 Opus 审定）· 执行：Sonnet 5.5 并发子 Agent

## 1. 范围判断

PRD 第 43 篇结论：**先建知识底座，再建国画工厂。** 本轮只做可以在代码层面闭环、并且能用测试证明的部分。

| 本轮做 | 本轮不做（原因） |
|---|---|
| V0.1：64 卦主数据、八卦表、二进制验证、SVG 卦符生成器、自动测试 | 图像生成（需选型模型与授权，属 V0.5 试点） |
| 384 爻**结构**（爻位、阴阳、爻名），可确定性推导 | 卦辞与爻辞**原文**：须有底本，不允许凭模型记忆写入 |
| 来源登记册骨架（`sources.json`，底本待人工选定） | 384 条历史故事（PRD 第 26 篇：宁缺毋编） |
| 单卦状态机 + 作品登记册（PUBLISHED 必须有人工批准） | 人工终审、印文、书法定稿 |
| `gxwd` CLI：init / status / hexagram show / validate binary / render svg | 其余 CLI 子命令（留 stub，报 not implemented） |
| CLAUDE.md、AGENTS.md、3 个 Agent、8 个 MVP Skill、国画风格规范、模板 | 13 个 Agent 全员、24 个 Skill 全集（V2.0） |

## 2. 仓库结构（以 PRD 第 38 篇为准）

```
guanxiang-wudao/
├── CLAUDE.md  AGENTS.md  README.md  pyproject.toml
├── data/            trigrams.json hexagrams.json yao-texts.json sources.json asset-catalog.json
├── schemas/         *.schema.json
├── src/gxwd/        domain.py validator.py renderer.py yao.py workflow.py catalog.py cli.py
├── .claude/agents/  classics-researcher.md ink-art-director.md independent-verifier.md
├── .claude/skills/  8 个 MVP Skill（SKILL.md）
├── .claude/rules/   classics.md art-style.md publication.md
├── templates/       research-brief.md art-brief.md business-philosophy.md review-checklist.md
├── docs/            art-style-guide.md IMPLEMENTATION_PLAN.md
├── projects/  assets/hexagram-svg/  output/
└── tests/
```

## 3. 数据契约

### 3.1 编码规则（硬约束）
- 阳 = `1`，阴 = `0`。
- `binary_bottom_to_top` 从初爻读到上爻，**前三位 = 下卦（内卦），后三位 = 上卦（外卦）**。
- `lines_top_to_bottom` 是 `binary_bottom_to_top` 的逆序，元素取 `"yang"` 或 `"yin"`。
- 爻位 `position` 1 = 初爻，6 = 上爻；存储自下而上，展示自上而下。
- 八卦：乾111 坤000 震100 巽011 坎010 离101 艮001 兑110。

### 3.2 `data/trigrams.json`
```json
[{"name":"乾","symbol":"☰","binary":"111","nature":"天","virtue":"健","mnemonic":"乾三连"}, ...8 条]
```

### 3.3 `data/hexagrams.json`（数组，按文王卦序）
```json
{
  "hexagram_id": 37,
  "name": "家人",
  "full_name": "风火家人",
  "slug": "jiaren",
  "symbol": "䷤",
  "lower_trigram": {"name": "离", "binary": "101"},
  "upper_trigram": {"name": "巽", "binary": "011"},
  "binary_bottom_to_top": "101011",
  "lines_top_to_bottom": ["yang","yang","yin","yang","yin","yang"],
  "text_verification": "pending",
  "artwork_status": "not_checked"
}
```
- `symbol` 必须等于 `chr(0x4DC0 + hexagram_id - 1)`（Unicode 的易经卦象区按文王卦序排列）。
- `full_name`：八纯卦写作「X为Y」（乾为天），其余写作「上卦象 + 下卦象 + 卦名」（风火家人）。
- `slug`：无声调拼音，用于 `projects/37-jiaren/`。

### 3.4 `data/yao-texts.json`（由 `gxwd.yao.build_yao_records` 生成，不手写）
```json
{"hexagram_id": 37, "lines": [
  {"position": 1, "line_type": "yang", "line_name": "初九",
   "original_text": null, "source_id": "SOURCE_PENDING", "edition": null, "page": null,
   "variant_readings": [], "interpretation": null, "historical_story_id": null,
   "verification_status": "pending"}
], "extra_lines": []}
```
- 爻名：初/上 + 九/六（初九、上六），二至五爻写作 九/六 + 二三四五（九二、六四）。
- 乾卦 `extra_lines` = `[{"name":"用九", ...}]`，坤卦 = `[{"name":"用六", ...}]`，其余卦为空数组。它们不计入 384。

### 3.5 经文红线（PRD 第 25、27 篇）
`original_text` 一律为 `null`，`source_id` 一律为 `"SOURCE_PENDING"`。**本轮任何文件都不得写入卦辞、爻辞或《彖传》《象传》的正文**，也不得编造书名、版本或页码。底本由人工选定后，另起一轮做校勘录入。

### 3.6 `data/sources.json`
```json
{"sources": [], "status": "awaiting_human_selection",
 "candidate_editions_note": "候选底本（如通行本《周易正义》等）由国学主编确认后登记"}
```

## 4. 主数据正确性：交叉校验方案

单元测试只能证明结构自洽，证明不了"第 N 卦确实是某上某下"。所以采用三道互相独立的校验：

1. **Unicode 锚定**：`symbol == chr(0x4DC0 + id - 1)`，用 `unicodedata.name()` 确认落在 HEXAGRAM 区。
2. **双盲独立表**：WP2 由另一个子 Agent 在**不读取** `data/hexagrams.json` 的前提下，凭自身知识独立写出 `tests/fixtures/kingwen_independent.json`（id → 卦名、上卦、下卦）。测试逐卦 diff，任何不一致都判失败，交人工裁定，**禁止**直接改一边去迁就另一边。
3. **锚点断言**：八纯卦（1、2、29、30、51、52、57、58）、泰(11)=下乾上坤、否(12)=下坤上乾、既济(63)=101010、未济(64)=010101、家人(37)=101011。另外检查一条结构不变量：文王卦序中每一对卦（1–2、3–4……）互为反卦（上下颠倒），或者在倒过来不变时互为错卦（逐爻取反）。

## 5. 模块接口契约（各工作包必须严格遵守）

```python
# gxwd/domain.py  (WP1)
DATA_DIR: Path                       # 默认 <repo>/data，可用环境变量 GXWD_DATA_DIR 覆盖
YANG, YIN = "yang", "yin"
def load_trigrams(data_dir: Path | None = None) -> list[dict]
def load_hexagrams(data_dir: Path | None = None) -> list[dict]
def get_hexagram(hexagram_id: int, data_dir: Path | None = None) -> dict   # 不存在时抛 KeyError
def lines_from_binary(binary_bottom_to_top: str) -> list[str]              # 返回 top_to_bottom

# gxwd/validator.py  (WP1)
class HexagramValidationError(ValueError)
def validate_hexagram(lower: str, upper: str, binary: str) -> dict          # PRD 第 31 篇的函数
def validate_all(hexagrams: list[dict], trigrams: list[dict]) -> dict
#   -> {"valid": bool, "checked": int, "errors": [{"hexagram_id": int|None, "rule": str, "detail": str}]}

# gxwd/renderer.py  (WP3) — 纯函数，只依赖标准库
def render_hexagram_svg(lines_top_to_bottom: list[str], *, size: int = 240,
                        color: str = "#273F52", title: str | None = None) -> str
def render_hexagram_file(hexagram: dict, out_dir: Path) -> Path   # 写出 <id:02d>-<slug>.svg

# gxwd/yao.py  (WP4)
def yao_name(position: int, line_type: str) -> str
def build_yao_records(hexagrams: list[dict]) -> list[dict]          # 结构见 3.4

# gxwd/workflow.py  (WP5)
class State(StrEnum): DRAFT RESEARCHED TEXT_VERIFIED ART_DRAFT ART_APPROVED
                      LAYOUT_READY REVIEW_REQUIRED PUBLISHED BLOCKED REJECTED REVISION_REQUIRED
class TransitionError(ValueError)
def transition(record: dict, to: State, *, actor: str, note: str = "",
               approval: dict | None = None, now: str | None = None) -> dict   # 返回新 dict，不修改入参

# gxwd/catalog.py  (WP5)
def build_catalog(hexagrams: list[dict]) -> dict      # 64 条记录，初始 DRAFT
def summarize(catalog: dict) -> dict[str, int]        # 按状态计数

# gxwd/cli.py  (WP5) — argparse，入口 gxwd.cli:main(argv: list[str] | None = None) -> int
```

**不可变原则**：所有函数返回新对象，不修改入参。

## 6. 状态机（PRD 第 23 篇）

| 当前状态 | 允许迁移到 |
|---|---|
| DRAFT | RESEARCHED, BLOCKED |
| RESEARCHED | TEXT_VERIFIED, REVISION_REQUIRED, BLOCKED |
| TEXT_VERIFIED | ART_DRAFT, REVISION_REQUIRED, BLOCKED |
| ART_DRAFT | ART_APPROVED, REVISION_REQUIRED, REJECTED |
| ART_APPROVED | LAYOUT_READY, REVISION_REQUIRED |
| LAYOUT_READY | REVIEW_REQUIRED, REVISION_REQUIRED |
| REVIEW_REQUIRED | PUBLISHED, REJECTED, REVISION_REQUIRED |
| PUBLISHED | REVISION_REQUIRED（新版本修订） |
| BLOCKED / REVISION_REQUIRED | DRAFT, RESEARCHED |
| REJECTED | DRAFT |

迁移到 PUBLISHED 必须带 `approval={"approved_by": 非空, "approved_at": ISO8601, "gates": {"G1":"passed","G2":"passed","G3":"passed"}}`，否则抛 `TransitionError`。记录中的 `history` 是只追加的列表，每次迁移追加 `{from, to, actor, note, at}`。

## 7. 并行工作包（Sonnet 子 Agent 同时执行）

| WP | 名称 | 独占写入路径 | 验收 |
|---|---|---|---|
| WP1 | 卦象主数据与验证引擎 | `data/trigrams.json` `data/hexagrams.json` `src/gxwd/domain.py` `src/gxwd/validator.py` `tests/test_hexagram_binary.py` `tests/test_validator.py` | `pytest tests/test_hexagram_binary.py tests/test_validator.py` |
| WP2 | 独立文王卦序对照表（双盲） | `tests/fixtures/kingwen_independent.json` `tests/test_kingwen_crosscheck.py` | 集成后运行 `pytest tests/test_kingwen_crosscheck.py` |
| WP3 | SVG 卦符渲染器 | `src/gxwd/renderer.py` `tests/test_renderer.py` | `pytest tests/test_renderer.py` |
| WP4 | 384 爻结构、来源登记与 Schema | `src/gxwd/yao.py` `data/sources.json` `schemas/**` `tests/test_yao.py` `tests/test_schemas.py` | `pytest tests/test_yao.py tests/test_schemas.py` |
| WP5 | 状态机、登记册与 CLI | `src/gxwd/workflow.py` `src/gxwd/catalog.py` `src/gxwd/cli.py` `tests/test_workflow.py` `tests/test_catalog.py` `tests/test_cli.py` | `pytest tests/test_workflow.py tests/test_catalog.py`（CLI 测试在集成后通过） |
| WP6 | Agent / Skill / 规范层 | `CLAUDE.md` `AGENTS.md` `.claude/**` `docs/art-style-guide.md` `templates/**` | 人工审阅 + 集成时检查路径 |

**主会话集成步骤（串行）**：生成 `data/yao-texts.json` 和 `data/asset-catalog.json` → `uv pip install -e .` → 全量 `pytest` → `gxwd validate binary --all` → `gxwd render svg --all` → 修复跨包问题 → 更新 README → 提交。

## 8. 验收清单（对应 PRD 第 42 篇 DoD）

| DoD 条目 | 本轮状态目标 | 检查方式 |
|---|---|---|
| 64 卦主数据 | ✅ | `pytest tests/test_hexagram_binary.py tests/test_kingwen_crosscheck.py` |
| 384 爻结构 | ✅ 结构完整；原文待录 | `pytest tests/test_yao.py`（384 条，无重复） |
| 经文来源 | ⏳ 登记册骨架，底本待人工选定 | `data/sources.json.status == awaiting_human_selection` |
| 卦符生成器 | ✅ | `gxwd render svg --all` 产出 64 个 SVG；测试回读线型 |
| 8 个核心 Skill | ✅ 文档契约 | `.claude/skills/*/SKILL.md` 共 8 个，每个都有 Input/Output/Failure 节 |
| 3 个核心 Agent | ✅ 文档契约 | `.claude/agents/*.md` 共 3 个 |
| 国画风格规范 | ✅ | `docs/art-style-guide.md` |
| 单卦完整闭环 | ❌ 下一轮（V0.5） | — |
| 独立质量审查可阻断 | ✅ 程序层（G2 卦符部分） | `gxwd validate binary --all` 失败时返回非 0 |
| 人工出版审批 | ✅ 程序层 | `pytest tests/test_workflow.py`：无 approval 不能进入 PUBLISHED |

## 9. 风险与待人工确认

1. **Rule 01–05 原文缺失**：只恢复了概括版本（经典有据、卦象有数、故事有义、国画有境、成品有验），上线前必须补齐原文。
2. **底本选择**：卦辞与爻辞用哪一个底本（及版本、页码体系），需要国学主编决定，之后才能开始 L0 录入。
3. **主数据双盲差异**：WP2 与 WP1 如果不一致，只能人工裁定，不能自动修复。
4. **图像模型选型与授权**：V0.5 试点前需要确定。
5. **印文与书法字体授权**：G3 出版前需要确认。
6. **"已生成""已审校""已批准""已出版"严格区分**：状态机已经强制执行，运营上也必须坚持。

## 10. 下一轮（V0.5）

以第 37 卦《风火家人》跑通单卦闭环：选定底本并录入 → G1 → 艺术 Brief → 候选主画 → 三层合成卡片 → G2/G3 → 人工审批。

## 11. 正式审定意见

**审定日期**：2026-10-28 · **审定人**：Opus 5.5（独立审定，未参与本方案的执行）

**总体结论**：**有条件批准**本方案为 Round 1 正式规划。范围取舍符合 PRD 第 37、43 篇（P0 / V0.1 先建可信底座），经文红线执行到位（全仓检索未发现卦辞、爻辞、彖传、象传正文），`pytest` 269 项全部通过，`gxwd validate binary --all` 输出 64/64。批准附带两个条件：一是下表标为"本轮修"的 R1–R6 须在提交前完成；二是在 R1 修复前，§8 中"人工出版审批 ✅"降为"⚠️ 仅函数层"。

审定时实际复现了两个问题（在 scratchpad 的数据副本上操作，未改动仓库）：
- 把 `asset-catalog.json` 中第 37 卦手工改为 `PUBLISHED`、不附 approval，Schema 校验通过，`gxwd status` 输出"已发布 1/64"，退出码 0。
- 对上述副本执行 `gxwd init --force`，登记册被整体重建，状态与 history 全部清空，没有任何提示。

### 11.1 方案与 PRD 的一致性

| # | 审定项 | 结论 | 依据 | 处置建议 |
|---|---|---|---|---|
| A1 | 范围取舍：V0.1 + V0.5 骨架，不写原文、不生成图像、不编故事 | 同意 | PRD 第 26、37、43 篇；第 42 篇 DoD | — |
| A2 | `hexagrams.json` 采用第 31 篇的形态，而不是第 25 篇示例（后者 `lines_top_down` 用 1/0，与第 31 篇的 yang/yin 冲突） | 同意 | PRD 第 25 篇 vs 第 31 篇 | 下一轮：在 §3 注明取舍理由 |
| A3 | §3.4 `yao-texts.json` 示例与实现不一致：实现带顶层 `{"version","hexagrams":[...]}` 包装 | 需修改 | `src/gxwd/cli.py:56-58`；`schemas/yao-texts.schema.json` | 本轮修（方案文字，以实现和 Schema 为准） |
| A4 | 数据模型没有卦辞、《彖传》、《大象》《小象》的存储位置；`yao-texts.json` 只有爻辞和用九/用六 | 遗漏 | PRD 第 25 篇 L0 层定义；第 25 篇（续）证据字段 `text_type` | 下一轮：新增 `data/canonical-texts.json`，`text_type` ∈ {gua_ci, yao_ci, yong, tuan, da_xiang, xiao_xiang}（见 §12 V5-WP1） |
| A5 | `slug` 不唯一：qian(乾/谦)、kun(坤/困)、bi(比/贲)、lv(履/旅)、yi(颐/益)、jian(蹇/渐)，64 卦只有 58 个不同 slug；另外项目目录写作 `37-jiaren`、SVG 写作 `<id:02d>-<slug>`，两种写法不统一 | 需修改 | `data/hexagrams.json`；§3.3；`src/gxwd/renderer.py:94` | 本轮修（方案）：唯一键改为 `<id:02d>-<slug>`，`projects/` 同样采用补零写法（第 37 卦不受影响）；下一轮补唯一性测试 |
| A6 | §4 第 1 道"Unicode 锚定"表述过强：`symbol == chr(0x4DC0+id-1)` 只锚定 id 与卦符，不约束卦名和二进制 | 需修改 | `src/gxwd/validator.py:106-107` | 下一轮（文档）：改称"卦符码位一致性"。真正起作用的独立校验是双盲表加锚点断言 |
| A7 | 双盲表由同一模型族写出，两边的错误可能相关 | 遗漏（风险） | §4 第 2 道；`tests/fixtures/kingwen_independent.json` | 下一轮：国学主编对 `gxwd hexagram show 1..64` 的输出做一次人工签核，存档到 `reviews/` |
| A8 | 状态机主干与第 23 篇一致；BLOCKED / REJECTED / REVISION_REQUIRED 的回退边是合理补充 | 同意 | PRD 第 23 篇；`src/gxwd/workflow.py:31-47` | — |
| A9 | `REVISION_REQUIRED` 只能回到 DRAFT 或 RESEARCHED，所以纯艺术返工也要重走经文核验；没有记录返工范围 | 需修改 | `src/gxwd/workflow.py:44` | 下一轮：增加 `revision_scope`（text/art/layout），art 和 layout 范围允许回到 TEXT_VERIFIED |
| A10 | PUBLISHED 门禁只检查调用方自报的 `gates` 字符串，不重算硬性检查，不核对审查报告文件，也不限制 `approved_by` 的身份（Agent 可以自己填）；出版时也不检查经文是否仍为 SOURCE_PENDING | 需修改 | PRD 第 23 篇"通过全部硬性检查"；第 28 篇"任何 AI Agent 不应拥有自动出版权限"；`src/gxwd/workflow.py:62-75`；`.claude/rules/publication.md`"经文仍为 SOURCE_PENDING 的作品不得出版" | 下一轮：新增 `publisher.py`，重算 `validate_all`、检查该卦经文全部已核验、要求 `reviews/g1..g3` 报告存在且为 pass（记录文件哈希）、`approved_by` 必须在人工审批人名单中且不同于任何生产者 |
| A11 | 离开 PUBLISHED 后，`approval` 仍留在记录上；`version` 没有递增，也没有保存已出版快照 | 需修改 | `src/gxwd/workflow.py:109-111`；PRD 第 36 篇作品证书 | 下一轮 |
| A12 | 权限要求"由文件系统或工具权限真正执行"：仓库没有 `.claude/settings.json` 或 hook，3 个 Agent 都有 Write 和不受限的 Bash | 遗漏 | PRD 第 24 篇"不能仅依赖提示词"；第 27 篇；`AGENTS.md`"权限说明" | 下一轮（V0.5 开工前完成，见 V5-WP4） |
| A13 | 缺少 `publisher.py`、作品证书（文件哈希、release_version、canonical_text_version）、版本锁定（经文修订后相关作品标记为需重检） | 遗漏 | PRD 第 24、36、38 篇 | 下一轮（V5-WP2、V5-WP5） |
| A14 | Skill Contract 与 ExecutionPlan 只写在 Agent 文档里，没有 Schema 做机器校验 | 遗漏 | PRD 第 24 篇（含"二"） | 下一轮（V5-WP3） |
| A15 | DoD 映射总体正确；"人工出版审批 ✅ 程序层"过于乐观（见 R1） | 需修改 | PRD 第 42 篇；§8 | 本轮修（R1 修好后才能保留 ✅） |

### 11.2 实现与方案的一致性（本轮须修复：R1–R6）

| # | 审定项 | 结论 | 依据（file:line） | 处置建议 |
|---|---|---|---|---|
| R1 | **PUBLISHED 门禁可以通过登记册绕过**：手改 JSON 为 PUBLISHED 且不附 approval，Schema、`summarize`、`gxwd status` 全部接受，并计入"已发布"（已复现） | 需修改 | `schemas/asset-catalog.schema.json`（state 只有 enum，没有条件约束）；`src/gxwd/catalog.py:27-35`；`src/gxwd/cli.py:63-74` | **本轮修**：① `workflow.py` 把 `_check_approval` 公开为 `check_approval`；② `catalog.py` 新增 `validate_catalog(catalog) -> list[str]`，对每条 PUBLISHED 记录检查 `check_approval(record["approval"])` 是否通过，以及 `history[-1]` 是否为 `{from: REVIEW_REQUIRED, to: PUBLISHED}`，并按迁移表重放整条 history；③ `_cmd_status` 先调用它，有问题时输出到 stderr 并返回 1，`summarize` 不计入非法记录；④ Schema 增加 `if state==PUBLISHED then required approval`；⑤ 在 `tests/test_catalog.py` 和 `tests/test_cli.py` 中加入伪造 PUBLISHED 的用例 |
| R2 | **`gxwd init --force` 会无条件重建登记册和爻数据**，清空状态、history、approval；V0.5 开始录入经文后，还会清空已录入的经文（已复现） | 需修改 | `src/gxwd/cli.py:49-58` | **本轮修**：`--force` 只在两种情况下允许覆盖：登记册全部为 DRAFT 且 history 为空；`yao-texts.json` 中所有 `original_text` 为 null 且 `source_id` 为 SOURCE_PENDING。否则拒绝并返回 1。补一个对应测试 |
| R3 | 经文红线没有对**已提交**数据做机器断言：`test_yao.py` 只测生成函数，Schema 允许 `original_text` 为字符串 | 需修改 | `tests/test_yao.py`；`schemas/yao-texts.schema.json` | **本轮修**：新增测试，断言 `data/yao-texts.json == {"version":"1","hexagrams": build_yao_records(load_hexagrams())}`，同时防止数据漂移和红线被突破。V0.5 引入 `canonical-texts.json` 后，再把这条测试改为"有原文就必须有已登记的 source_id、edition、page" |
| R4 | 主数据缺失时测试会 **skip 而不是 fail**；数据被误删时，CI 仍然显示通过 | 需修改 | `tests/test_kingwen_crosscheck.py:33-34`；`tests/test_schemas.py:107-108`；`tests/test_cli.py:35-39` | **本轮修**：数据已经入库，把三处 `pytest.skip` 改为直接断言文件存在 |
| R5 | 状态机测试有同义反复：`LEGAL` 由被测对象 `TRANSITIONS` 自己生成，表里多一条或少一条边都检测不出来（`ILLEGAL` 只列了 7 条） | 需修改 | `tests/test_workflow.py:14` | **本轮修**：在测试中按 §6 逐行硬编码期望迁移表，断言 `TRANSITIONS == EXPECTED`；另外断言 PUBLISHED 唯一的前驱是 REVIEW_REQUIRED |
| R6 | 渲染测试只读回 `data-position` 和 `data-line-type`，这是渲染器自己写上的元数据，没有检验几何位置；即使 y 坐标上下颠倒，测试仍会通过 | 需修改 | `tests/test_renderer.py:23-31`；`src/gxwd/renderer.py:50-52` | **本轮修**：按 rect 的 `y` 升序分组，断言每行的 rect 数量（阳 1、阴 2）依次等于 `lines_top_to_bottom`，并断言 y 最小的一行 `data-position == 6` |
| R7 | `render svg` 直接使用 `lines_top_to_bottom`，没有先校验 | 需修改 | `src/gxwd/renderer.py:91`；`src/gxwd/cli.py:114-133` | 下一轮：改为 `lines_from_binary(binary_bottom_to_top)`，或者先跑 `validate_all`，失败就拒绝渲染 |
| R8 | `validate_all` 没有把八卦表钉死在规范值上；`gxwd validate binary` 这道门禁依赖 `trigrams.json` 本身正确（目前只有 pytest 检查八卦表） | 需修改 | `src/gxwd/validator.py:24-25,132-133`；`tests/test_hexagram_binary.py:27-31` | 下一轮：在 validator 中内置第 31 篇的 `TRIGRAMS` 常量并加一条规则 `trigram_table` |
| R9 | `validate_hexagram` 隐式读取默认 DATA_DIR；`cli._data_dir` 重复了 domain 中的环境变量逻辑 | 需修改（低） | `src/gxwd/validator.py:29`；`src/gxwd/cli.py:26-28` vs `src/gxwd/domain.py:15-22` | 下一轮 |
| R10 | 传入非法的 `to` 时抛出 `ValueError`，而不是 `TransitionError` | 需修改（低） | `src/gxwd/workflow.py:98` | 下一轮 |
| R11 | 不可变要求：domain、validator、yao、renderer、workflow、catalog 都返回新对象，并有测试 | 同意 | `tests/test_workflow.py:109-120`；`tests/test_hexagram_binary.py:101-105`；`tests/test_validator.py:109-113`；`tests/test_yao.py` | — |
| R12 | §5 接口签名与实现一致（`transition` 只接受关键字参数；`validate_all` 返回结构正确；CLI 入口为 `gxwd.cli:main`） | 同意 | `src/gxwd/*.py`；`pyproject.toml` | — |
| R13 | 主数据正确性：锚点（八纯卦、泰、否、既济、未济、家人）、反卦/错卦配对不变量、双盲逐卦比对都通过；`full_name` 规则对 64 卦逐一核验无误 | 同意 | `tests/test_hexagram_binary.py:40-75`；`tests/test_kingwen_crosscheck.py` | — |

### 11.3 文档层一致性

| # | 审定项 | 结论 | 依据 | 处置建议 |
|---|---|---|---|---|
| D1 | CLAUDE.md、AGENTS.md 与第 39 篇的结构一致；3 个 Agent、8 个 Skill 齐全，每个 Skill 都有 Input、Rules、Output、Failure、Implementation 节 | 同意 | `.claude/agents/*.md`；`.claude/skills/*/SKILL.md` | — |
| D2 | `ink-image-production` 要求执行 `gxwd render svg --all`，会写到 `assets/hexagram-svg/`，超出 ink-art-director 只能写 `projects/*/art/**` 的权限 | 需修改 | `.claude/skills/ink-image-production/SKILL.md:34`；`.claude/agents/ink-art-director.md`"可写" | 下一轮：改为只读 `assets/hexagram-svg/<id:02d>-<slug>.svg`，或执行 `gxwd render svg <id> --out projects/<id:02d>-<slug>/art/layers/` |
| D3 | `hexagram-binary-validation` 要求产出 `reviews/binary-validation.json`，但 CLI 只输出到 stdout，没有 JSON 输出，也没有单卦模式（`--all` 是必填参数） | 需修改 | `.claude/skills/hexagram-binary-validation/SKILL.md:22,30`；`src/gxwd/cli.py:176` | 下一轮：增加 `--json` 和 `<id>` 参数 |
| D4 | 顺序矛盾：`ink-art-direction` 和 `business-philosophy-mapping` 的输入写的是"通过 G1 的 interpretation.md"，但按 DAG，义理研究是在 G1 之后才做的，G1 无法覆盖它 | 需修改 | `AGENTS.md` DAG；`.claude/skills/ink-art-direction/SKILL.md:10`；`.claude/skills/business-philosophy-mapping/SKILL.md:10` | 下一轮：增设"义理审查"报告 `reviews/interpretation-review.json`（属于第 28 篇第二层），艺术 Brief 以它为前置条件 |
| D5 | Agent 文档要求返回 Skill Contract JSON，但 G1、G2、G3 报告的文件名没有统一（`binary-validation.json`、`g3-publication-qa.json`），approval 中的 gates 也无法引用对应文件 | 需修改 | `.claude/skills/publication-qa/SKILL.md:22`；§6 | 下一轮：统一为 `reviews/g1-*.json`、`g2-*.json`、`g3-*.json`，并由 `review-report.schema.json` 约束 |
| D6 | CLAUDE.md 的常用命令写的是裸 `gxwd`，需要先激活 venv；§2 列出了 `projects/` 和 `output/`，但这两个目录还没有创建 | 需修改（低） | `CLAUDE.md`"常用命令"；§2 | 下一轮 |
| D7 | `docs/` 中的 PRD docx 含有示范性经文；它不是底本，Agent 可能把它当作来源引用 | 遗漏（风险） | PRD 第 32 篇；`.claude/rules/classics.md` | 下一轮：在 classics.md 中写明"PRD 文本不得作为 source_id 或经文来源" |
| D8 | 由 classics-researcher 兼管 business-philosophy-mapping（第 39 篇没有分配企业哲学 Agent） | 同意 | PRD 第 27、39 篇 | 第 27 篇对企业哲学 Agent 的禁止项已由 `rules/classics.md` 覆盖 |

### 11.4 遗漏与风险汇总
1. **原文入库路径未设计**（A4）：V0.5 的第一步就会卡在这里。经文只能由人工依据底本录入，Agent 只负责结构、校验和比对工具。
2. **门禁可信度**（R1、A10、A12）：目前门禁只在函数调用这一条路径上成立。只有把登记册校验、出版重算和工具权限这三项都补齐，才满足第 28 篇"任何 Agent 不能绕过"的要求。
3. **数据被误覆盖**（R2）：在录入经文之前必须修好。
4. **测试检出力**（R4–R6）：部分测试在关键回归上会给出"假绿"结果。

## 12. V0.5 并行工作包（以第 37 卦家人为例）

**目标**（PRD 第 43 篇 V0.5）：第 37 卦跑通全流程，从研究、G1、义理审查、艺术 Brief、主图、三层合成，到 G2、G3、人工批准。正式生产前须先查询作品登记册（PRD 第 31 篇）。

**前置条件（主会话串行，或由人工完成）**
- P0：§11 中 R1–R6 已合入，并且全量 `pytest` 通过。
- H1（人工）：国学主编选定底本，在 `data/sources.json` 登记 source_id、书名、版本、页码体系，并把 status 改为 `selected`。
- H2（人工）：按底本录入第 37 卦的卦辞、六爻、《彖传》《象传》，写入人工专用目录 `inputs/human/37-jiaren-canonical.csv`。**Agent 不得写入或补全这个文件。**
- H3（人工）：确定图像模型与授权；确定书法字体与印文授权。
- H4（人工）：建立审批人名单 `data/approvers.json`，只能列真人。

**共同约束**：每个包只写自己独占的路径。`src/gxwd/cli.py` 不分配给任何包，各包只暴露函数和测试，由主会话在集成时接入 CLI。测试中的经文一律使用合成占位串（例如 `〔测试文本甲〕`），**不得出现任何真实的卦辞或爻辞**。

| 批次 | WP | 名称 | 执行者 | 独占写入路径 | 输入 | 验收方式 |
|---|---|---|---|---|---|---|
| A（P0 后立即并行） | V5-WP1 | 经文数据契约与录入校验 | Sonnet 子 Agent（代码） | `schemas/canonical-texts.schema.json` `src/gxwd/texts.py` `tests/test_texts.py` `tests/fixtures/texts/**` | §3、A4；PRD 第 25 篇证据字段；`data/sources.json` | `pytest tests/test_texts.py`：没有已登记 source_id、edition、page 的原文会被拒绝；异文写入 `variant_readings`，不覆盖原文；导入函数返回新对象，不修改原数据；全仓 grep 不到真实经文 |
| A | V5-WP2 | 出版门禁与 publisher | Sonnet 子 Agent（代码） | `src/gxwd/workflow.py` `src/gxwd/catalog.py` `src/gxwd/publisher.py` `schemas/asset-catalog.schema.json` `tests/test_workflow.py` `tests/test_catalog.py` `tests/test_publisher.py` | §6、A9–A11、A13；PRD 第 23、28、36 篇 | `pytest` 中的反例全部被拒：伪造 PUBLISHED、approved_by 不在名单内、approved_by 与生产者相同、经文仍为 SOURCE_PENDING、审查报告缺失或哈希不符；`revision_scope` 回退正确；离开 PUBLISHED 时归档 approval 并递增 version |
| A | V5-WP3 | Skill Contract 与审查报告 Schema | Sonnet 子 Agent（代码） | `schemas/skill-result.schema.json` `schemas/review-report.schema.json` `schemas/execution-plan.schema.json` `tests/test_contract_schemas.py` | PRD 第 24 篇；`.claude/agents/*.md` 中的输出契约；D5 | `pytest tests/test_contract_schemas.py`：3 个 Agent 文档里的示例 JSON 能通过校验；`review_status` 只接受 pass 或 fail；缺少 provenance 时报错 |
| A | V5-WP4 | 权限落地与文档对齐 | Sonnet 子 Agent（配置与文档） | `.claude/settings.json` `.claude/hooks/**` `.claude/skills/**` `.claude/rules/**` `CLAUDE.md` `AGENTS.md` `tests/test_guard_hook.py` | A12、D2–D7 | `pytest tests/test_guard_hook.py`：用模拟的 hook 输入验证写 `data/**`、`schemas/**`、`src/**`、`inputs/human/**` 会被拒绝，写 `projects/37-jiaren/...` 时按角色放行；D2–D7 逐条在文档中关闭；`CLAUDE.md` 与 `AGENTS.md` 中的命令和路径都能在仓库里找到 |
| A | V5-WP5 | 三层合成器（图卡） | Sonnet 子 Agent（代码） | `src/gxwd/composer.py` `templates/card/**` `tests/test_composer.py` | PRD 第 26、27 篇三层模型；`renderer.py`；`docs/art-style-guide.md` 色板 | `pytest tests/test_composer.py`：卦符层由 `binary_bottom_to_top` 生成并能回读；文字层只取已核验字段，pending 字段显示"（待底本校勘）"；经文未核验时 `final=True` 必须抛错；主图用占位 PNG |
| A | V5-WP6 | 第 37 卦研究初稿（不含原文） | classics-researcher（Sonnet） | `projects/37-jiaren/research/**` | `gxwd hexagram show 37`；`templates/research-brief.md`；`templates/business-philosophy.md`；`.claude/rules/classics.md` | 产出 `lookup.json`、`collation.json`（H2 完成前全部为 pending）、`interpretation.md`、`yao-cases.json`、`business-philosophy.md`；每份都附 Skill Contract JSON 并通过 V5-WP3 的 Schema；引用经文只能用 text_id 引用，不得抄写正文；历史故事标注 A/B/C/D 等级，没有可靠案例时明确写出 |
| B（H1、H2 完成且 WP1 合入后） | V5-WP7 | 第 37 卦经文导入与 G1 | 主会话执行导入；independent-verifier 执行 G1 | `data/canonical-texts.json`（只能由导入函数写入）；`projects/37-jiaren/reviews/g1-*.json` | `inputs/human/37-jiaren-canonical.csv`；`data/sources.json` | 导入函数对 H2 文件做格式与来源校验；国学主编人工抽查并签字；G1 报告为 pass，或者状态转为 BLOCKED |
| B | V5-WP8 | 义理审查 | independent-verifier（独立实例，未参与 WP6） | `projects/37-jiaren/reviews/interpretation-review.json` | WP6 产出；G1 报告 | 报告通过 `review-report.schema.json`；原典、注释、现代应用分层清楚，现代解释没有冒充原文；结果为 pass 或 fail，并附问题清单 |
| C（WP8 为 pass 后） | V5-WP9 | 艺术 Brief 与主图 | ink-art-director（Sonnet） | `projects/37-jiaren/art/**` | 已通过审查的 `interpretation.md`；`templates/art-brief.md`；`docs/art-style-guide.md`；`assets/hexagram-svg/37-jiaren.svg`（只读）；H3 | `art-brief.md` 各栏填写完整，上下卦和编码取自 CLI；主图不含文字和卦符；`provenance/v<N>.json` 记录模型、prompt、参数、seed |
| D | V5-WP10 | 合成、G2、G3 | 主会话调用 composer；independent-verifier 执行 G2、G3 | `projects/37-jiaren/layout/**`（主会话）；`projects/37-jiaren/reviews/g2-*.json` `g3-*.json`（验证者） | WP5、WP9 产出 | G2 中卦符回读等于 `101011`，画面与卦义一致；G3 中图文与已核验文本逐字一致，各版本哈希相符；国学与艺术意见分别记录 |
| E | H5 | 人工终审 | 人工总主编 | `projects/37-jiaren/reviews/approval.json`（人工提交） | G1、G2、G3 报告 | 由 `publisher` 重算全部门禁后迁移到 PUBLISHED；`gxwd status` 显示"已发布 1/64"，并能校验通过 |

**并发度**：批次 A 的 6 个包没有共享写入路径，可以同时派发。批次 B 到 E 受 G1、义理审查和 G2 门禁约束，必须串行推进。V0.5 的发布条件是 H5 完成。

## 13. 审定条件闭环：R1–R6 修复记录

R1–R6 已由 4 个 Sonnet 子 Agent 并发修复，主会话完成验证。审定"有条件批准"的条件已满足，本方案即为本轮正式规划。

| 编号 | 修复 | 验证 |
|---|---|---|
| R1 | 新增 `workflow.check_approval`、`catalog.validate_catalog`；`gxwd status` 遇到非法记录时返回 1；schema 规定 state 为 PUBLISHED 时必须有 approval | 手改一条记录为 PUBLISHED 且不附 approval：status 报出 2 条错误，退出码 1 |
| R2 | `init --force` 只在登记册全部为初始状态、且原文全为 null 时才允许覆盖 | 对已篡改的登记册执行 `--force`：被拒绝，退出码 1，文件不变 |
| R3 | 新增 `tests/test_data_integrity.py`：已提交的 yao-texts 必须等于程序推导结果，386 条均为 `SOURCE_PENDING` | 通过 |
| R4 | 数据缺失时测试判定失败，不再 skip | 全量测试 0 skip |
| R5 | 期望迁移表按 §6 硬编码，枚举全部 121 个组合，并断言 PUBLISHED 的唯一前驱是 REVIEW_REQUIRED | 实现与 §6 一致 |
| R6 | 新增几何回读：按 y 坐标分组，64 卦全部回读校验 | 渲染器几何无误 |

全量测试 441 passed，0 skipped；`gxwd validate binary --all` 64/64 通过。
