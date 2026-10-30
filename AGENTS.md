# Agent Navigation

本文件只做导航：谁负责什么、读写哪里、交给谁。规则正文见 `CLAUDE.md` 与 `.claude/rules/`，技能细节见各 `SKILL.md`。

## 3 个已落地 Agent

| Agent | 调用的 Skill | 读 | 写 | 产出 | 交给 |
|---|---|---|---|---|---|
| classics-researcher | hexagram-lookup, classical-text-collation, yao-interpretation, business-philosophy-mapping | `data/**` `docs/**` | `projects/*/research/**` | 校勘记录（本轮为 pending）、六爻义理、企业哲学映射 | independent-verifier（G1 + 义理审查） |
| ink-art-director | ink-art-direction, ink-image-production | 通过义理审查的卦义（`research/`）、`docs/art-style-guide.md`、`.claude/rules/art-style.md` | `projects/*/art/**` | 艺术 Brief、无字主图及生成记录、图层说明 | independent-verifier（G2） |
| independent-verifier | hexagram-binary-validation, publication-qa | 所有待审成果与证据 | `projects/*/reviews/**` | pass/fail 与问题清单 | 人工总主编（批准出版） |

independent-verifier 只给 pass/fail 与问题清单，无权批准出版；批准权只属于人工。

## 10 个 Specialist Agent 骨架（由 R7 WP5 建）

骨架位于 `.claude/agents/specialists/`，待后续轮次按需激活。

| Agent | 职责概述 |
|---|---|
| trigram-analyst | 八卦卦象结构与象意分析 |
| yao-position-analyst | 爻位与承乘比应关系分析 |
| historical-case-researcher | A/B/C/D 证据等级历史案例挖掘 |
| business-translator | 企业哲学现代应用转译 |
| art-style-classifier | 国画风格归属判断（G/M/S/P） |
| composition-planner | 国画构图立意与场景设计 |
| svg-reviewer | 卦符 SVG 几何精度审查 |
| text-layer-designer | 第三层文字排版与印章设计 |
| publication-packager | 出版包组装与元数据核查 |
| review-auditor | 审查报告交叉核验（防自我批准） |

## 单卦执行 DAG（9 步，PRD §40）

步骤中"主会话"指不带 CLAUDE_AGENT_ROLE 的集成层；"subagent"指带角色标识的派发 Agent。

```
步骤 1  读取主数据（主会话）
        hexagram-lookup 拉取 data/hexagrams.json + data/trigrams.json
        ↓
步骤 2  并行（subagent）
        ├─ 经文校勘 (classical-text-collation)  →  本轮输出 SOURCE_PENDING
        └─ 编码验证 (hexagram-binary-validation) →  reviews/g1-<slug>.json
        ↓
步骤 3  G1 经典与数理验收（independent-verifier subagent）
        → reviews/g1-<slug>.json  result: pass | fail
        ↓ G1 pass 后分工
步骤 4  并行（subagent）
        ├─ 六爻义理 (yao-interpretation)
        └─ 企业哲学 (business-philosophy-mapping)
        ↓
步骤 5  义理审查（independent-verifier subagent）
        → reviews/interpretation-review.json
        ↓ 义理 pass 后
步骤 6  国画构图 (ink-art-direction, ink-art-director subagent)
        前置：interpretation-review.json result=pass
        ↓
步骤 7  国画生成 + 卦符 + 文字层（并行或串行，ink-art-director subagent）
        gxwd render svg <id>    →  assets/hexagram-svg/<id>-*.svg
        ink-image-production    →  projects/*/art/main-image.*
        text-layer-designer     →  projects/*/art/text-layer.svg（骨架）
        ↓
步骤 8  G2 艺术与卦象验收（independent-verifier subagent）
        → reviews/g2-<slug>.json
        ↓
步骤 9  G3 出版与证据验收（independent-verifier subagent）
        → reviews/g3-<slug>.json
        ↓
        Human Approval（主编）→ PUBLISHED
```

## reviews/ 文件名约定

| 报告 | 文件名 |
|---|---|
| G1 编码验证 | `reviews/g1-<slug>.json` |
| 义理审查 | `reviews/interpretation-review.json` |
| G2 艺术验收 | `reviews/g2-<slug>.json` |
| G3 出版验收 | `reviews/g3-<slug>.json` |

approval.gates 的证据字段必须引用 reviews/ 中对应报告文件的哈希。

## 24 个 Skill 地图

### 8 个 MVP Skill（已落地）

| Skill | 调用者 |
|---|---|
| hexagram-lookup | classics-researcher |
| classical-text-collation | classics-researcher |
| yao-interpretation | classics-researcher |
| business-philosophy-mapping | classics-researcher |
| hexagram-binary-validation | independent-verifier |
| publication-qa | independent-verifier |
| ink-art-direction | ink-art-director |
| ink-image-production | ink-art-director |

### 16 个骨架 Skill（由 R7 WP4 建，位于 `.claude/skills/`）

| Skill | 预定用途 |
|---|---|
| research-historical-allusions | 历史案例证据等级标注 |
| historical-evidence-check | A 级可靠史料核查 |
| philosophy-comparison | 跨卦义理对比 |
| cultural-symbolism | 卦象文化象征解读 |
| extract-visual-symbols | 卦义到画面符号提取 |
| compose-hexagram-scene | 国画场景立意合成 |
| svg-geometry-check | SVG 卦符几何回读验证 |
| text-layer-compose | 文字印章层排版 |
| art-style-classify | 国画风格分类（G/M/S/P） |
| composition-critique | 构图评分与改进建议 |
| publication-package | 出版包组装校验 |
| approval-gate-check | 审批人白名单 + 门禁重算 |
| canonical-text-import | 经文 CSV 导入校验辅助 |
| source-evidence-trace | 底本来源链溯源 |
| hexagram-cross-reference | 卦际互参与错综分析 |
| devlog-summarize | DEVLOG 状态摘要生成 |

## 执行与失败处理

- 缺少前置输入、底本未定、验证不通过 → `BLOCKED` 或 `REVISION_REQUIRED`。
- 永不静默修复权威数据；主数据差异交人工裁定。

## 状态机

`DRAFT → RESEARCHED → TEXT_VERIFIED → ART_DRAFT → ART_APPROVED → LAYOUT_READY → REVIEW_REQUIRED → PUBLISHED`；详见 `docs/IMPLEMENTATION_PLAN.md` 第 6 节。

## 权限说明

职责隔离由 `.claude/hooks/guard_write.py`（PreToolUse hook）真正执行：
- 全局禁写：`data/**`、`schemas/**`、`src/**`、`inputs/human/**`、`pyproject.toml` 等。
- Agent 额外禁写：`CLAUDE.md`、`AGENTS.md`、`.claude/agents/**`（CLAUDE_AGENT_ROLE 设置时生效）。
- 角色写入范围：classics-researcher → `projects/*/research/**`；ink-art-director → `projects/*/art/**`；independent-verifier → `projects/*/reviews/**`。
