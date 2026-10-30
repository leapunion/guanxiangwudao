---
name: publication-qa
description: Run gate G3 publication and provenance QA on a hexagram deliverable - text-image match, layout, calligraphy, seals, versions, licensing, completeness. Use before requesting human approval; it can never approve publication.
---

# Publication QA（G3）

## Input
- hexagram_id
- 全套成果：`research/`、`art/`、卦符 SVG、版式文件
- G1、G2 审查报告（`projects/<id>-<slug>/reviews/`）：`g1-<slug>.json`、`g2-<slug>.json`
- `templates/review-checklist.md`

## Rules
- 前置条件：`reviews/g1-<slug>.json` 和 `reviews/g2-<slug>.json` 均为 pass。
- 检查图文匹配、文字排版、书法、印章、版本引用、授权、交付完整性，并核对三层是否独立。
- 自动检查通过后仍需人工审稿与艺术审定；国学与艺术意见分别记录。
- 只给 pass/fail 与问题清单。**人工批准前不得进入 PUBLISHED**；本 Skill 无权批准。
- 经文仍为 SOURCE_PENDING 的作品不得通过 G3。

## Output
- `projects/<id>-<slug>/reviews/g3-<slug>.json`
- `projects/<id>-<slug>/reviews/g3-<slug>.md`（问题清单）
- Skill Contract V1.0 JSON，`review_status` 为 pass / fail。

## Failure
- 任一关键检查失败 → `REVISION_REQUIRED`，进入返工队列，不得进入发布目录。
- 前置材料缺失 → `BLOCKED`。
- 永不静默修复被审成果。

## Implementation
- 先运行 `.venv/bin/gxwd validate binary --all` 与 `.venv/bin/gxwd status` 确认结构与状态。
- 通过后交人工总主编；批准信息（approved_by、approved_at、gates G1/G2/G3）由状态机记录，见 `gxwd.workflow.transition`。
