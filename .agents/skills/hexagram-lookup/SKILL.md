---
name: hexagram-lookup
description: Look up canonical hexagram master data (name, symbol, trigrams, binary code, line structure) by id, name or slug. Use whenever any task needs hexagram facts; never derive hexagram structure by LLM reasoning.
---

# Hexagram Lookup

## Input
- hexagram_id（1–64），或卦名 / slug
- task_id

## Rules
- 只读 `data/hexagrams.json`、`data/trigrams.json`；不修改。
- 阳 = 1，阴 = 0；`binary_bottom_to_top` 自初爻起，前三位为下卦，后三位为上卦；展示自上而下。
- 不得凭模型记忆补充或"纠正"卦序、上下卦、编码。
- 本轮不返回任何卦辞、爻辞原文（`text_verification` 为 pending）。

## Output
- 返回结构化记录（内存返回即可）：hexagram_id、name、full_name、slug、symbol、lower/upper trigram、binary_bottom_to_top、lines_top_to_bottom、text_verification。
- 如需留痕，写入 `projects/<id>-<slug>/research/lookup.json`。
- 按 Skill Contract V1.0 返回 JSON。

## Failure
- id 不存在、数据缺失、字段互相矛盾 → `BLOCKED`，并报告差异，交人工裁定。
- 永不静默修复权威数据。

## Implementation
- 调用 `.venv/bin/gxwd hexagram show <id>`；
- 或在 Python 中使用 `gxwd.domain.get_hexagram(id)`、`gxwd.domain.lines_from_binary(...)`。
- 不使用 LLM 推理卦象。
