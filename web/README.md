# web/

只读 64 卦查看器。单文件、无后端。

## 构建与查看

```bash
.venv/bin/python scripts/build-web.py
open web/index.html
```

`web/index.html` 是**派生产物**，不入库（见 `.gitignore`）。真相源是
`scripts/build-web.py` 加 `data/`、`assets/hexagram-svg/`、
`projects/**/reviews/g1-binary-validation.json`、
`projects/**/research/candidate-text-from-ching.json`。

## 页面能看什么

- 64 卦网格；点任一卦看详情。
- 国画风格过滤（G 工写青绿 / M 文人水墨 / S 苍润山水 / P 人物故事）。
- 单卦详情：卦符 SVG、上下卦、编码、显示爻线、风格徽章、G1 验证徽章、
  从 Ching 抽的候选经文（卦辞/彖/大象/六爻/六小象，乾坤加用爻）。

## 页面不能做什么

- 不改任何数据（纯静态只读）。
- 不显示 `data/canonical-texts.json`：本轮此文件仍空；只显示 Ching 候选。
- 不涉及出版、G2/G3、合成器预览。

## 要改什么

- 配色：`scripts/build-web.py` 的 `PALETTE` 字典。
- 风格归属：`scripts/build-web.py` 的 `STYLE` 字典（与
  `docs/art-style-assignment-candidate.md` 一致，待艺术主编签字后
  建议迁移到 `data/art-style.json`）。
- 卡片内容：HTML_TEMPLATE 里的 `renderDetail` 函数。
