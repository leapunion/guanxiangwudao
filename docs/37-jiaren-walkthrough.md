# 第 37 卦家人 · 试点闭环 walkthrough

> 把『观象悟道』从"V0.1 可信底座"推到"至少 1 卦走到 PUBLISHED"的手把手记录。
> 其他 63 卦可以照此复用。真人节点由你完成；Agent 节点由 Claude Code 会话里的 Task tool 跑；程序节点由 CLI 跑。

## 一、起点自检

```bash
.venv/bin/gxwd hexagram show 37
# 应该看到：卦序 37 / 卦名 家人 / 全名 风火家人 / 编码 101011
# 上卦巽(011) 下卦离(101)；显示自上而下 阳阳阴阳阴阳
```

```bash
.venv/bin/gxwd status
# 第 37 卦应该是 DRAFT（和其他 63 卦一样）
```

```bash
ls projects/37-jiaren/
# 应该有：research/、reviews/（含 g1-binary-validation.json）
```

```bash
ls output/canonical-input-prefilled/37-jiaren-canonical.csv
# Agent 为你预填的 CSV，Ching 通解稿经文已填进 original_text 列
```

## 二、第 1 步：底本细节（人工 · 5 分钟）

拿你手头的《周易正义》实物（阮元刻《十三经注疏》本的某个影印版）。
翻版权页，用编辑器改 `data/sources.json`：

```jsonc
{
  "sources": [
    {
      "source_id": "ZYZY-RUAN",
      "title": "周易正义",
      "annotators": ["王弼 注", "韩康伯 注", "孔颖达 疏"],
      "edition": "阮元刻《十三经注疏》本",
      "page_system": "阮刻影印本页码（上下栏分页）",
      "publisher": "中华书局",                 // ← 实物发行社
      "isbn": "978-7-...-...",                 // ← 实物 ISBN
      "notes": "...",
      "status": "selected"
    }
  ],
  ...
}
```

跑一下验证：

```bash
.venv/bin/python -m pytest tests/test_schemas.py tests/test_data_integrity.py -q
# 应该全过
```

## 三、第 2 步：L0 经文签字（人工 · 30–60 分钟）

### 2.1 把预填 CSV 复制到人工专属目录

```bash
mkdir -p inputs/human
cp output/canonical-input-prefilled/37-jiaren-canonical.csv inputs/human/
```

### 2.2 对照实物逐条核对，用编辑器打开

```bash
$EDITOR inputs/human/37-jiaren-canonical.csv
```

每行要做三件事：

1. **核对 `original_text`**：
   - Ching 通解稿是『通行本《周易正义》』的文字，大体可信（见 Ching ACCEPTANCE.md L322、L402 的『与通行本一致』抽核）。
   - **逐字对照你手头实物**。若有偏差，直接改。
   - 禁止：相信 Ching 的文字就等于不核对。

2. **填 `page`**：具体页码，如 `19上`、`19下`。阮刻影印本是上下栏分页，别省栏号。

3. **把 `verification_status` 从 `pending` 改为 `verified`**：这是**你的签字**。意味着你确认该行与实物逐字一致。

CSV 共 15 行：

| text_type | 条数 | 说明 |
|---|---|---|
| gua_ci | 1 | 卦辞「家人：利女贞。」 |
| tuan | 1 | 彖传 |
| da_xiang | 1 | 大象传「风自火出…」 |
| yao_ci | 6 | 初九至上九爻辞 |
| xiao_xiang | 6 | 六条小象 |

**不要**自动化这一步。它是整个项目红线中最硬的一条。

### 2.3 导入 + G1

```bash
./scripts/import-and-gate.sh 37 jiaren
# 流程：
#   gxwd texts import inputs/human/37-jiaren-canonical.csv --hexagram-id 37
#     → data/canonical-texts.json 新增 15 条 verified 条目
#   gxwd texts validate → 对全局跑 schema 校验
#   gxwd validate binary 37 --json --out projects/37-jiaren/reviews/g1-binary-validation.json
```

成功后看一眼：

```bash
.venv/bin/python -c "
import json
entries = json.load(open('data/canonical-texts.json'))['entries']
h37 = [e for e in entries if e['hexagram_id'] == 37]
print(f'第 37 卦条数: {len(h37)}')
print(f'全部 verified: {all(e[\"verification_status\"] == \"verified\" for e in h37)}')
"
```

## 四、第 3 步：义理研究稿（Agent · 5–10 分钟）

**本步在 Claude Code 会话里跑**，不是 CLI。

Agent 版的研究稿第 37 卦**第四轮已经做过一版**，在
`projects/37-jiaren/research/{interpretation.md, yao-cases.json,
business-philosophy.md, skill-result.json}`。查看一下，看是否满意：

```bash
cat projects/37-jiaren/research/interpretation.md | head -30
cat projects/37-jiaren/research/yao-cases.json | head -40
```

如果要重新跑或修订，在 Claude Code 会话里：

```python
Task(
    subagent_type="classics-researcher",
    description="第 37 卦家人研究稿 (v2)",
    prompt=(
        "重新产出 projects/37-jiaren/research/interpretation.md、"
        "yao-cases.json、business-philosophy.md。"
        "本轮 data/canonical-texts.json 已有第 37 卦 verified 经文，"
        "可用 text_id ([[H37-gua_ci]] 等) 交叉引用。"
        "历史故事按 .claude/rules/classics.md 的 A/B/C/D 等级标注，"
        "没有可靠案例就写『尚无合适的可靠历史案例』。"
    ),
)
```

## 五、第 4 步：义理审查（Agent · 独立实例 · 2–5 分钟）

在 Claude Code 会话里起**另一个** independent-verifier Agent
（和第 3 步的 classics-researcher 不是同一个 session）：

```python
Task(
    subagent_type="independent-verifier",
    description="第 37 卦义理审查",
    prompt=(
        "对 projects/37-jiaren/research/interpretation.md 独立审查，"
        "产出 projects/37-jiaren/reviews/interpretation-review.json。"
        "字段按 schemas/review-report.schema.json：gate=interpretation、"
        "result=pass 或 fail、findings 列表、verifier={id,name,role}、"
        "producer_ids=['classics-researcher'] 或空。禁止通过只是因为自己产出。"
    ),
)
```

跑完后：

```bash
cat projects/37-jiaren/reviews/interpretation-review.json
# result 必须是 "pass"，否则下一步阻塞
```

## 六、第 5 步：WP9 艺术 Brief 和主图（阻塞）

**这里停住**。WP9 冻结需要三项人工决定：

1. **图像模型选型 + 商用授权**：选 DALL-E 3 / Imagen / 即梦 / Midjourney 之一，确认商用条款。写到 `docs/image-model-decision.md`。
2. **书法字体 + 印章授权**：篆刻家或字体商用授权。
3. **艺术主编确认第 37 卦归属**：家人卦候选是 `P 人物故事 · 国学叙事`（`docs/art-style-assignment-candidate.md`）。签字确认。

完成后：

```python
Task(
    subagent_type="ink-art-director",
    description="第 37 卦家人艺术 Brief",
    prompt=(
        "按 .claude/skills/ink-art-direction/SKILL.md 和 "
        "docs/art-style-guide.md 产出 projects/37-jiaren/art/art-brief.md。"
        "输入：projects/37-jiaren/research/interpretation.md（通过义理审查）、"
        "data/canonical-texts.json 中第 37 卦经文。"
        "风格类型：P 人物故事（已由艺术主编确认）。"
        "主画应避开现代物品；人物应是中国古代文人、家人、庭院。"
    ),
)
```

然后用你选定的图像模型（这步不是 Claude Code 的事）生成一张无字主图，
保存到 `projects/37-jiaren/art/master.png`。记得保留 prompt、参数、模型版本到
`projects/37-jiaren/art/provenance/v1.json`。

## 七、第 6 步：三层合成（CLI · 10 秒）

```bash
.venv/bin/gxwd compose 37 \
  --master projects/37-jiaren/art/master.png \
  --out projects/37-jiaren/layout \
  --final \
  --now "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

输出的 JSON 里 `pending_slots: []` 表示所有经文都 verified
（第 2 步做到位了就是这样）。

## 八、第 7 步：G2 + G3（Agent · 独立实例）

还是在 Claude Code 会话里跑两次 Task：

```python
# G2 卦符与画面
Task(
    subagent_type="independent-verifier",
    description="第 37 卦 G2 卦符与画面",
    prompt=(
        "对 projects/37-jiaren/layout/card.svg 和 master.png 做 G2 审查。"
        "重点：hexagram.svg 几何回读等于 lines_from_binary('101011')；"
        "画面意象与下离上巽（家人卦）一致；"
        "不出现现代物品、错误服饰、颠倒上下卦等。"
        "产出 projects/37-jiaren/reviews/g2-visual.json。"
    ),
)

# G3 出版与溯源
Task(
    subagent_type="independent-verifier",
    description="第 37 卦 G3 出版与溯源",
    prompt=(
        "对 projects/37-jiaren/layout/ 做 G3 审查。"
        "重点：图卡文字与 data/canonical-texts.json 中第 37 卦 verified 文本"
        "逐字一致；各层 sha256 哈希稳定；art/provenance/*.json 完整；"
        "字体、模型、印章授权齐全（docs/image-model-decision.md）。"
        "产出 projects/37-jiaren/reviews/g3-publication.json。"
    ),
)
```

两份报告 `result` 都必须是 `pass`。

## 九、第 8 步：人工总主编终审 + publish request（人工 + CLI）

**你本人**阅读以下材料：

```bash
cat projects/37-jiaren/research/interpretation.md
cat projects/37-jiaren/research/business-philosophy.md
cat projects/37-jiaren/research/yao-cases.json
cat projects/37-jiaren/reviews/interpretation-review.json
cat projects/37-jiaren/reviews/g1-binary-validation.json
cat projects/37-jiaren/reviews/g2-visual.json
cat projects/37-jiaren/reviews/g3-publication.json
# 查看合成的卡片：
open projects/37-jiaren/layout/card.svg
```

满意后在 CLI 终审：

```bash
.venv/bin/gxwd publish request 37 \
  --approved-by cavin \
  --approved-at "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

publisher 会**重算全部门禁**：

- 调 validate_all 对主数据
- 第 37 卦 canonical-texts 全部 verified
- 4 份 reviews 存在、result=pass、record 文件哈希
- `approved_by=cavin` 在 `data/approvers.json` 中且 ≠ 任何 verifier/生产者 id

任一失败 publisher 返回非 0 并给出理由。全部通过后，**它返回新的 record**
（state=PUBLISHED），但**不写回 catalog**——这一步你手动确认后再写。

如果你同意写回：

```bash
# publisher 已返回 new_record；写回 asset-catalog.json 由集成层做。
# 本轮 CLI 没把这一步放到 publish request 里，是故意的——给你最后
# 一次机会检查 approval 内容。
# 如需自动写回，追加一行 CLI 或自己：
.venv/bin/python -c "
import json
from pathlib import Path
cat = json.loads(Path('data/asset-catalog.json').read_text(encoding='utf-8'))
# 从 publish request 的 stdout JSON 拿 record 回填...
# 实际做法：下一轮把 publish request 加 --write 选项
"
```

**0.2.0 TODO**：给 `gxwd publish request` 加 `--write` 参数一键回填 catalog。
当前要么手动，要么跑 `demo-autopilot` 分支看自动化版本（教讲性，不合入 main）。

## 十、完成后

```bash
.venv/bin/gxwd status
# 第 37 卦变 PUBLISHED
# 其他 63 卦 DRAFT
```

```bash
.venv/bin/gxwd web build && open web/index.html
# 查看器显示 G1/G2/G3 全 pass，verified 经文、研究稿、画面都在
```

恭喜，这就是第一个真正走到 PUBLISHED 的"观象悟道"作品。

## 十一、下一卦怎么办

从第 1 步重复（底本细节已填就不用再改）。
8 卦试点（乾、坤、屯、蒙、泰、否、家人、革）跑完后再决定是否批量 64。
