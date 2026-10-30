---
name: interpret-hexagram
description: Produce a layered scholarly interpretation of one hexagram — classical meaning, traditional commentary, and modern analogy — based on validated structural data. Use after hexagram-lookup and classical-text-collation pass.
---

# Interpret Hexagram（interpret-hexagram）

## 职责
- 综合卦名、卦象、上下卦象义，生成三层解释：经典原义 / 传统解释 / 现代类比。
- 为每层标注依据来源（text_id 或证据等级）。
- 不做吉凶预测；只做学术义理分析。

## Input
- `hexagram_id`（1–64）
- `data/hexagrams.json`、`data/trigrams.json` 中已通过 hexagram-binary-validation 的记录
- `data/yao-texts.json` 中对应条目（本轮 `original_text` 均为 null，`source_id = "SOURCE_PENDING"`）
- `data/sources.json`（底本状态清单）
- `projects/<id>-<slug>/research/lookup.json`（hexagram-lookup 产出）

## Rules
- 必须先调用 `hexagram-lookup` 取得完整结构数据，不得凭记忆推断卦位。
- 本轮经文全为 SOURCE_PENDING：只分析卦象结构与传统象义，**不引用任何卦辞、爻辞、彖传、象传原文**；引用占位写 `[[H<id>-guaci]]`、`[[H<id>-Y<n>]]`。
- 三层严格分开，不得混写；现代类比不得冒充古典原义。
- 解释须逻辑自洽，有可追溯的象义推导链。
- 不修改任何 `data/**` 文件。

## Output
- `projects/<id>-<slug>/research/interpretation.json`：含 hexagram_id、三层解释（classical / traditional / modern）、text_ids（占位）、source_status
- `projects/<id>-<slug>/research/interpretation.md`：人可读的义理摘要
- Skill Contract V1.0 JSON

## Failure
- 结构数据缺失或 hexagram-binary-validation 未通过 → `BLOCKED`
- 引用文本的 source_id 非 `"SOURCE_PENDING"` 且未在 `data/sources.json` 中登记 → `BLOCKED`
- 三层无法区分 → `REVISION_REQUIRED`
- 永不静默修复权威数据

## Implementation
- 调用 `.venv/bin/gxwd hexagram show <id>` 获取结构；
- 读取 `data/trigrams.json` 获取上下卦象义（山、水、雷、风等）；
- 半自动：Agent 写义理，hexagram-lookup 提供确定性结构数据；
- 产出写入 `projects/<id>-<slug>/research/` 后交 `audit-classical-evidence` 做 G1 复核。
