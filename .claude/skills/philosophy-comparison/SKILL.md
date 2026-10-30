---
name: philosophy-comparison
description: Compare a hexagram's core philosophical theme with parallel concepts in Confucianism, Taoism, Buddhism and major Western schools, producing a structured cross-tradition map for scholarly and business use.
---

# 哲学比较（philosophy-comparison）

## 职责
- 将该卦的核心义理（来自 `interpretation.json`）与儒、道、佛及西方哲学流派的对应概念对照。
- 提炼共性（相通）与差异（独特性），为企业哲学转译和出版批注提供依据。
- 不编造学派立场；差异之处须有典籍或学术来源支撑。

## Input
- `hexagram_id`
- `projects/<id>-<slug>/research/interpretation.json`
- `projects/<id>-<slug>/research/cultural-symbolism.json`

## Rules
- 比较须有文本依据；无据可查的比较标注 `UNVERIFIED`，不得写"某学派认为"而无任何来源。
- 不得混淆"传统义理"与"现代转译"；比较结果作为现代研究层，不进入 L0 经典层。
- 不修改 `data/**`；不引用经文原文（本轮 SOURCE_PENDING）。

## Output
- `projects/<id>-<slug>/research/philosophy-comparison.json`：字段含 hexagram_id、confucian_parallel、taoist_parallel、buddhist_parallel、western_parallels[]（含学派、概念、similarity_note、difference_note）、overall_theme
- Skill Contract V1.0 JSON

## Failure
- `interpretation.json` 缺失或未通过核查 → `BLOCKED`
- 比较项无任何来源标注 → `REVISION_REQUIRED`
- 永不静默修复权威数据

## Implementation
- 纯 Agent：对照已知哲学文献知识；
- 调用 `.venv/bin/gxwd hexagram show <id>` 确认卦名与象义；
- 产出供 `business-philosophy-mapping` 和 `interpret-hexagram` 增补注释。
