---
name: classical-text-collation
description: Collate hexagram and line texts against a registered base edition, recording variants and sources. Use for L0 canonical text entry; while no base edition is selected it may only output pending status.
---

# Classical Text Collation

## Input
- hexagram_id
- source_id（取自 `data/sources.json`）
- `data/yao-texts.json` 中该卦的爻记录
- 底本版本与页码体系（由国学主编选定后才有）

## Rules
- 底本未选定（`data/sources.json` 的 status 为 `awaiting_human_selection`）时，**只能输出 pending**：`original_text = null`、`source_id = "SOURCE_PENDING"`。**禁止凭记忆补原文。**
- 本轮 L0 一律 SOURCE_PENDING。
- 有底本后：逐条对应，异文独立记录（`variant_readings`），不静默覆盖；乾用九、坤用六另行记录，不计入 384。
- 不编造书名、版本、页码。
- 经文、传统解释、现代应用分层保存。

## Output
- `projects/<id>-<slug>/research/collation.json`：每爻一条，含 position、source_id、edition、page、variant_readings、verification_status（本轮均为 pending）。
- 同目录 `collation-notes.md`：待决事项与阻断原因。
- Skill Contract V1.0 JSON，`status` 为 `blocked`（底本未选）或 `completed`。

## Failure
- 底本未选定 → 输出 pending 并以 `BLOCKED` 结束，说明等待人工选定底本。
- 底本与现有数据冲突 → `REVISION_REQUIRED`，列出差异，交人工裁定。
- 永不静默修复 `data/**`。

## Implementation
- 读取 `data/sources.json` 判断底本状态；读取 `data/yao-texts.json` 获取爻结构。
- 只写 `projects/<id>-<slug>/research/`。主数据的写入由人工另起一轮完成。
