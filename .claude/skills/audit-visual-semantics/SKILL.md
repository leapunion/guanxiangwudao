---
name: audit-visual-semantics
description: Run gate G2 visual-semantics audit on a hexagram's art layer — verifying hexagram symbol accuracy, scene-to-meaning fidelity, layer separation, and style compliance — producing a G2 pass/fail report. Cannot approve its own output.
---

# 视觉语义审校（G2）（audit-visual-semantics）

## 职责
- 担任 G2 关卡：对单卦艺术层做独立审校，确认视觉呈现与卦义语义一致。
- 核查：① 卦符 SVG 爻线与主数据一致；② 场景构图不颠倒上下卦关系；③ 三层独立（主图无文字、无卦符线条）；④ 五色体系合规；⑤ 印章文字有人工确认记录。
- 产出 G2 审查报告，不修改被审成果。

## Input
- `hexagram_id`
- `projects/<id>-<slug>/art/`：`hexagram-symbol.svg`、`scene-brief.json`、`art-card-metadata.json`、`calligraphy-seal-metadata.json`
- `projects/<id>-<slug>/art/seals/seal-approval.json`
- `projects/<id>-<slug>/reviews/g1-<slug>.json`（G1 通过为前置条件）
- `docs/art-style-guide.md`

## Rules
- 前置条件：`g1-<slug>.json` 的 `review_status` 为 pass。
- 只给 pass / fail 与问题清单；不修改被审文件。
- 卦符爻线数必须等于 6，且阴阳编码与 `binary_bottom_to_top` 严格一致；任何偏差即 CRITICAL。
- 场景主体方位（上卦象征在上、下卦象征在下）必须正确。
- 画面评分再高，卦象错误也须退回（`REVISION_REQUIRED`）；卦象再准，构图呆板也返工。
- 国学与艺术审查意见分别记录，不混写。
- 永不静默修复被审成果。

## Output
- `projects/<id>-<slug>/reviews/g2-<slug>.json`：字段含 hexagram_id、review_status（pass/fail）、issues[]（每项含 check_item、severity（CRITICAL/HIGH/MEDIUM/LOW）、description）、auditor_note、audited_at
- Skill Contract V1.0 JSON

## Failure
- G1 未通过 → `BLOCKED`
- 卦符爻线编码与主数据不一致 → `BLOCKED`（CRITICAL）
- 印章无 `seal-approval.json` 记录 → `BLOCKED`
- 永不静默修复被审成果

## Implementation
- 半自动：调用 `.venv/bin/gxwd validate binary --id <id>` 核验 SVG 编码；
- Agent 审查场景语义与风格合规；
- G2 通过后，`assemble-art-card` 方可合成，`publication-qa`（G3）方可启动。
