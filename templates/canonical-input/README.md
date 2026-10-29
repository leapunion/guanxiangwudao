# 经文录入 CSV 模板

每卦一份 `<id:02d>-<slug>-canonical.csv.template`。按卦复制到
`inputs/human/` 后由国学主编填 `original_text`、`edition`、`page` 列。

录入流程、字段含义、`gxwd` 命令详见 `docs/CANONICAL-INPUT-GUIDE.md`。

本轮本目录只提供第 37 卦的模板。其他卦的模板按同样格式生成，
`line_name` 列的阴阳取自 `data/hexagrams.json` 的 `lines_top_to_bottom`
（自上而下），逆序读到初爻；由 `gxwd hexagram show <id>` 可查。
