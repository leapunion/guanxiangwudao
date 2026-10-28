# Agent Navigation

本文件只做导航：谁负责什么、读写哪里、交给谁。规则正文见 `CLAUDE.md` 与 `.claude/rules/`，技能细节见各 `SKILL.md`。

## 总览

| Agent | 调用的 Skill | 读 | 写 | 产出 | 交给 |
|---|---|---|---|---|---|
| classics-researcher | hexagram-lookup, classical-text-collation, yao-interpretation, business-philosophy-mapping | `data/**` `docs/**` | `projects/*/research/**` | 校勘记录（本轮为 pending）、六爻义理、企业哲学映射 | independent-verifier（G1 + 义理审查） |
| ink-art-director | ink-art-direction, ink-image-production | 通过义理审查的卦义（`research/`）、`docs/art-style-guide.md`、`.claude/rules/art-style.md` | `projects/*/art/**` | 艺术 Brief、无字主图及生成记录、图层说明 | independent-verifier（G2） |
| independent-verifier | hexagram-binary-validation, publication-qa | 所有待审成果与证据 | `projects/*/reviews/**` | pass/fail 与问题清单 | 人工总主编（批准出版） |

independent-verifier 只给 pass/fail 与问题清单，无权批准出版；批准权只属于人工。

## 单卦 DAG（PRD 第 40 篇）

```
Canonical Data
 ├─ 经文校勘 (classical-text-collation) ┐ 可并行
 └─ 卦象编码验证 (hexagram-binary-validation) ┘
        ↓
   G1 经典与数理验收 (independent-verifier)
        → reviews/g1-binary-validation.json
        ↓ 通过后分工
 ┌ 六爻义理 (yao-interpretation)
 ├ 企业哲学 (business-philosophy-mapping)
 └ （义理研究完成后）
        ↓
   义理审查 (independent-verifier)
        → reviews/interpretation-review.json
        ↓ 通过后
   国画构图 (ink-art-direction)  ← 以 interpretation-review.json pass 为前置
        ↓
   国画生成 (ink-image-production) + 矢量卦符 (.venv/bin/gxwd render svg <id>) + 文字排版
        ↓
   G2 艺术与卦象验收 → reviews/g2-<slug>.json
        ↓
   G3 出版与证据验收 (publication-qa) → reviews/g3-<slug>.json
        ↓
   Human Approval → PUBLISHED
```

## 执行顺序
1. 读取经典主数据（`hexagram-lookup`）。
2. 经文校勘与编码验证并行；本轮底本未选定，校勘只能输出 pending。
3. G1 通过后，义理、企业哲学分工进行；义理审查通过后，国画构图方可启动。
4. 生成无字主图，程序绘制卦符，文字与印章独立成层。
5. G2，再 G3。
6. 请求人工批准；批准前状态不得为 PUBLISHED。

## 失败处理
- 缺少前置输入、底本未定、验证不通过 → `BLOCKED` 或 `REVISION_REQUIRED`。
- 永不静默修复权威数据；主数据的差异交人工裁定。

## 状态机
`DRAFT → RESEARCHED → TEXT_VERIFIED → ART_DRAFT → ART_APPROVED → LAYOUT_READY → REVIEW_REQUIRED → PUBLISHED`；详见 `docs/IMPLEMENTATION_PLAN.md` 第 6 节。

## 权限说明
职责隔离由 `.claude/hooks/guard_write.py`（PreToolUse hook）真正执行：
- 全局禁写：`data/**`、`schemas/**`、`src/**`、`pyproject.toml` 等（主会话与 Agent 均受限）。
- Agent 额外禁写：`CLAUDE.md`、`AGENTS.md`、`.claude/agents/**`（CLAUDE_AGENT_ROLE 设置时生效）。
- 角色写入范围：classics-researcher → `projects/*/research/**`；ink-art-director → `projects/*/art/**`；independent-verifier → `projects/*/reviews/**`。
