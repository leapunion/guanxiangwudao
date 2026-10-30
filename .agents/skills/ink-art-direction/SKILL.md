---
name: ink-art-direction
description: Produce an ink-painting art brief for one hexagram - image extraction, concept, composition, brush-and-color plan - from approved hexagram meaning and the project art style guide. Use before any artwork is generated.
---

# Ink Art Direction

## Input
- hexagram_id
- 通过义理审查的卦义摘要（`projects/<id>-<slug>/research/` 中通过义理审查的内容，见 `reviews/interpretation-review.json`）
- `docs/art-style-guide.md`、`.Codex/rules/art-style.md`
- `templates/art-brief.md`

## Rules
- 先立意，后造境：取象 → 立意 → 经营位置 → 笔墨设色，一卦一象，一象一境，一境一理，一理一用。
- 选定四种风格类型之一，并说明理由。
- 采用统一视觉参数与五色体系；留白约 35%–45%，按叙事灵活调整。
- 艺术含蓄，卦符精确：不要求机械画出"上面一团风、下面一团火"。
- 画面中不含文字、卦符、印章（均为独立图层）。
- 明确"应避免的错误表达"。
- 未经义理审查（`reviews/interpretation-review.json` 为 pass）的卦义不得形成正式创作稿。

## Output
- `projects/<id>-<slug>/art/art-brief.md`（按模板填写）。
- Skill Contract V1.0 JSON。

## Failure
- 卦义未通过义理审查 → `BLOCKED`。
- Brief 与卦象冲突或违反艺术底线 → `REVISION_REQUIRED`。
- 永不修改经文、卦序、编码。

## Implementation
- 用 `.venv/bin/gxwd hexagram show <id>` 取上下卦和编码填入 Brief，不用 LLM 推导。
- 完成后交 independent-verifier 审查。
