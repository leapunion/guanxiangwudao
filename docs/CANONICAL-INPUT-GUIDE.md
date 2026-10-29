# 经文录入指南（inputs/human）

国学主编按选定底本把 L0 原典录入 CSV，放到 `inputs/human/` 目录。
`.claude/hooks/guard_write.py` 已把 `inputs/human/**` 列为全局禁写：
任何 Agent（含主会话）都不得写入或补全这些 CSV。

## 本轮底本

V0.5 L0 唯一底本：**阮元刻《十三经注疏》本《周易正义》**（王弼、
韩康伯注；孔颖达疏），`source_id = ZYZY-RUAN`，登记在
`data/sources.json`，`status = selected`。

`data/sources.json` 中的 `edition / page_system / publisher / isbn`
在正式录入前由国学主编按手头实物补填（本轮占位为 `TODO`）。

## 文件命名

`<id:02d>-<slug>-canonical.csv`，例如 `37-jiaren-canonical.csv`、
`01-qian-canonical.csv`。卦序与 slug 以 `data/hexagrams.json` 为准
（`gxwd hexagram show <id>` 可查）。

## CSV 列约定

| 列 | 说明 |
|---|---|
| `text_type` | `gua_ci` / `tuan` / `da_xiang` / `yao_ci` / `xiao_xiang` / `yong` |
| `line_position` | `yao_ci` 填 `1..6`；`xiao_xiang` 填空或 `1..6`；`yong` 填 `用九` 或 `用六`；其余留空 |
| `line_name` | `yao_ci` 填初九/六二/九三/六四/九五/上九（阴阳自 `gxwd hexagram show` 查）；其余留空 |
| `original_text` | 底本原文；禁止凭记忆；留空表示 pending |
| `source_id` | 本轮一律写 `ZYZY-RUAN`；pending 条目可写 `SOURCE_PENDING` |
| `edition` | 阮刻影印本版次或印次 |
| `page` | 具体页码（上下栏），如 `19上` |
| `variant_readings_json` | 异文 JSON 数组 `[{"text":"...","source_id":"...","note":"..."}]`，无异文填 `[]` 或留空 |
| `verification_status` | `pending` / `verified` / `rejected`。`original_text` 非空且核对后填 `verified` |

每卦 CSV 应有 13 行（`gua_ci` × 1 + `tuan` × 1 + `da_xiang` × 1 +
`yao_ci` × 6 + `xiao_xiang` × 6）；乾、坤卦另加 `yong` 条（用九、用六）。

录入时 `import_canonical_from_csv` 会校验：

- `source_id` 必须出现在 `data/sources.json` 中、且 `status=selected`。
- 本轮状态为 pending 时，`edition` 与 `page` 允许留空；一旦
  `original_text` 非空，`edition`、`page` 必填且 `verification_status`
  必须为 `verified`（见 `schemas/canonical-texts.schema.json` 的
  if/then 规则）。
- 每卦的 `gua_ci / tuan / da_xiang` 最多各一条；`yao_ci` 位置
  `1..6` 不重复。

模板放在 `templates/canonical-input/`。按卦复制改名到
`inputs/human/`：

```bash
cp templates/canonical-input/37-jiaren-canonical.csv.template \
   inputs/human/37-jiaren-canonical.csv
# 用编辑器填好 original_text、edition、page 后保存
```

## 录入与验证

```bash
# 导入某一卦（校验通过才写入 data/canonical-texts.json；失败不写）
.venv/bin/gxwd texts import inputs/human/37-jiaren-canonical.csv --hexagram-id 37

# 校验 data/canonical-texts.json 整体
.venv/bin/gxwd texts validate
```

`texts import` 成功后，`data/canonical-texts.json` 中该卦的全部
条目被替换；其他卦不受影响。
