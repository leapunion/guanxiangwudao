---
name: hexagram-binary-validation
description: Validate hexagram binary codes, lower/upper trigram consistency and six-line structure with deterministic code. Use at gate G1/G2 or whenever hexagram data or a hexagram symbol changes.
---

# Hexagram Binary Validation

## Input
- hexagram_id（或 `--all`）
- lower_trigram、upper_trigram、binary_code（来自 `data/hexagrams.json`，无需手填）

## Rules
- 阳 = 1，阴 = 0。
- 自下而上读（初爻到上爻）。
- 下卦在前，上卦在后。
- 展示时六爻顺序反转（自上而下）。
- 八卦：乾111 坤000 震100 巽011 坎010 离101 艮001 兑110。
- 结果只表示结构正确，不代表经文、故事或国画已审核。

## Output
- `validation_status`、`expected_binary`、`actual_binary`、`line_structure`、`error_details`。
- 存档：`projects/<id>-<slug>/reviews/binary-validation.json`（全量校验写 `reviews/` 下对应报告）。
- Skill Contract V1.0 JSON，`validation.binary` 为 passed / failed。

## Failure
- 任何不一致 → `REVISION_REQUIRED`（数据层面差异 → `BLOCKED`），拒绝出版。
- 永不静默修复权威数据；差异交人工裁定。

## Implementation
- 命令：`gxwd validate binary --all`（失败时退出码非 0）。
- 或 Python：`gxwd.validator.validate_hexagram(lower, upper, binary)`、`gxwd.validator.validate_all(hexagrams, trigrams)`，数据经 `gxwd.domain` 读取。
- 不使用 LLM 推理卦象。
