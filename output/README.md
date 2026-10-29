# output/

Agent 产出的临时文件；不是权威主数据。

## 37-jiaren-from-ching.csv —— 已废弃

该文件由早先一次尝试生成，其 edition 和 page 字段带有未经核对
的推断值（例如 page=『卷四 · 家人』）。该推断违反
`.claude/rules/classics.md` 的红线『不编造书名、版本、页码』，
已不作为参考。

家人卦的候选经文现放在：
`projects/37-jiaren/research/candidate-text-from-ching.json`

该 JSON 带诚实的 provenance，不走 canonical-texts.schema，不进
data/canonical-texts.json，只供国学主编对照手头底本后决定是否
录入 `inputs/human/37-jiaren-canonical.csv`。
