# templates/card/

图卡合成模板目录。

## text-layer.tmpl.svg

文字层 SVG 模板，由 `gxwd.composer.compose_card` 读取并渲染。

### 占位符清单

| 占位符 | 含义 | 来源 |
|---|---|---|
| `{{hexagram_name}}` | 卦名（如"家人"） | `hexagram["name"]` |
| `{{full_name}}` | 全名（如"风火家人"） | `hexagram["full_name"]` |
| `{{gua_ci}}` | 卦辞 | `canonical_texts` 中 `text_type == "gua_ci"` |
| `{{tuan}}` | 彖传 | `canonical_texts` 中 `text_type == "tuan"` |
| `{{da_xiang}}` | 大象 | `canonical_texts` 中 `text_type == "da_xiang"` |
| `{{yao_ci_1}}` … `{{yao_ci_6}}` | 六爻爻辞（初爻至上爻） | `canonical_texts` 中 `text_type == "yao_ci"` 且 `position == 1..6` |
| `{{xiao_xiang_1}}` … `{{xiao_xiang_6}}` | 六爻小象（初爻至上爻） | `canonical_texts` 中 `text_type == "xiao_xiang"` 且 `position == 1..6` |

### 未核验字段

任何经文若 `verification_status != "verified"` 或 `original_text is None`，
`compose_card` 将该位置替换为 `（待底本校勘）`，并在 `CardArtifact.text_source_versions` 中记为 `SOURCE_PENDING`。

### 如何扩展

1. 在模板中新增 `{{new_field}}` 占位符。
2. 在 `composer.py` 的 `_build_text_vars` 函数中添加对应逻辑。
3. 在 `tests/test_composer.py` 中补充测试覆盖新字段。

### 颜色规范（来自 docs/art-style-guide.md §3）

| 名称 | 色值 | 用途 |
|---|---|---|
| 青黛 | #273F52 | 主墨色、卦符默认色 |
| 石青 | #547A83 | 辅助文字、副标题 |
| 石绿 | #A2B4A1 | 小象标签 |
| 赭石 | #B58C69 | 爻位标签 |
| 朱砂 | #A74439 | 印章占位框 |
