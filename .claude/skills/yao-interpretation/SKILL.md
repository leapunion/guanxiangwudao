---
name: yao-interpretation
description: Draft a six-line (yao) interpretation for one hexagram, separating classical meaning, traditional commentary and modern analogy, with evidence-graded historical cases. Use after G1 passes.
---

# Yao Interpretation

## Input
- hexagram_id
- 通过 G1 的结构数据（`data/hexagrams.json`、`data/yao-texts.json`）
- 底本状态（本轮：SOURCE_PENDING）
- `templates/research-brief.md`

## Rules
- 先用 `hexagram-lookup` 取得爻位与阴阳；爻名按初/上 + 九/六、九/六 + 二三四五。
- 本轮无已校勘原文：只能分析爻位结构（位置、阴阳、与相邻爻关系），**不得引用或复述任何经文、传文原文**，示例用"（待底本校勘）"。
- 三层分开：经典原义 / 传统解释 / 现代类比。
- 历史案例标注证据等级：A 可靠史料、B 传统记载、C 文学传说、D 现代类比。按处境四维度匹配：位置、矛盾、行动、结果。
- 无可靠案例就写"尚无合适的可靠历史案例"，宁缺毋编。
- 解读是学术解释，不预测吉凶。

## Output
- `projects/<id>-<slug>/research/interpretation.md`（按 research-brief 模板）。
- `projects/<id>-<slug>/research/yao-cases.json`：每爻的案例候选与证据等级（可为空）。
- Skill Contract V1.0 JSON。

## Failure
- 缺少 G1 通过记录或结构数据 → `BLOCKED`。
- 无法为论断标注证据等级 → `REVISION_REQUIRED`，删去该论断。
- 永不修改 `data/**`。

## Implementation
- 以 `gxwd hexagram show <id>` 获取结构；写作遵循 `.claude/rules/classics.md`。
- 交给 independent-verifier 做 G1 复核。
