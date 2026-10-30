---
name: cultural-symbolism
description: Extract and catalogue the natural symbols, cultural imagery and cosmological motifs encoded in a hexagram's trigrams and line structure, for use by art and philosophy pipelines.
---

# 文化象征提取（cultural-symbolism）

## 职责
- 从卦象（上下卦、六爻阴阳）中系统提取自然象征（天、地、山、水、雷、风、火、泽）及其文化含义。
- 列举与该卦相关的传统意象（方位、季节、人伦关系、器物）。
- 输出标准化象征词条，供艺术脚本与企业哲学两条线复用。

## Input
- `hexagram_id`
- `data/hexagrams.json`、`data/trigrams.json`
- `projects/<id>-<slug>/research/interpretation.json`（义理层）

## Rules
- 象征提取以卦象结构为依据，不凭模型记忆填充与卦无关的意象。
- 区分"卦象直接象征"与"传统引申象征"，两类分开记录。
- 不引用任何卦辞、爻辞原文（本轮 SOURCE_PENDING）；占位用 `[[H<id>-guaci]]`。
- 不修改 `data/**`。

## Output
- `projects/<id>-<slug>/research/cultural-symbolism.json`：字段含 hexagram_id、primary_symbols[]（卦象直接象征）、extended_symbols[]（传统引申）、season、direction、element、human_relations[]
- Skill Contract V1.0 JSON

## Failure
- 缺少 `data/trigrams.json` 或 hexagram 结构验证未通过 → `BLOCKED`
- 引申象征无法追溯到卦象结构 → `REVISION_REQUIRED`
- 永不静默修复权威数据

## Implementation
- 调用 `.venv/bin/gxwd hexagram show <id>` 取得上下卦名称；
- 读取 `data/trigrams.json` 中每个经卦的 `symbol`、`element`、`direction` 字段；
- 半自动：确定性结构数据来自 CLI，传统引申由 Agent 撰写；
- 产出供 `extract-visual-symbols` 与 `business-philosophy-mapping` 消费。
