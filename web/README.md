# web/

只读 64 卦查看器。单文件、无后端。

## 构建与查看

```bash
# 推荐入口
.venv/bin/gxwd web build        # 重建 web/index.html
.venv/bin/gxwd web serve        # 启本地服务 http://127.0.0.1:8000（默认 build 后启动）

# 历史兼容入口（薄壳 shim）
.venv/bin/python scripts/build-web.py
```

常用参数：

```bash
gxwd web build --out /tmp/x.html --repo-root /path/to/repo
gxwd web serve --port 8080 --host 0.0.0.0 --no-build
```

`web/index.html` 是**派生产物**，不入库（见 `.gitignore`）。真相源是
`src/gxwd/web.py` 加 `data/`、`assets/hexagram-svg/`、
`projects/**/reviews/g1-binary-validation.json`、
`projects/**/research/candidate-text-from-ching.json`、
`projects/**/research/{interpretation.md, yao-cases.json,
business-philosophy.md}`、`docs/art-style-guide.md`。

## 页面能看什么

- **8×8 卦符网格**：每格 SVG + 卦序 + 卦名 + 风格色点。
- **国画风格过滤**：全部 / G 工写青绿 / M 文人水墨 / S 苍润山水 / P 人物故事。
- **单卦详情（右侧抽屉）**：
  - 大版 SVG 卦符、上下卦、二进制编码、显示爻线
  - 风格徽章 + G1 验证徽章
  - 候选经文（从 Ching 抽的通行本，卦辞/彖/大象/六爻/六小象，乾坤加用爻）
  - **研究初稿（WP6）**：目前仅第 37 卦有，含
    - interpretation.md 的义理解读（内联 markdown 渲染）
    - 六爻历史故事候选（带 A/B/C/D 等级徽章；无案例时标注"尚无可靠案例"）
    - business-philosophy.md 的三层转译（经典原义 / 现代类比 / 经营建议）
- **底部 About 区**（可折叠）：`docs/art-style-guide.md` 全文。

## 页面不能做什么

- 不改任何数据（纯静态只读）。
- 不显示 `data/canonical-texts.json`：本轮此文件仍空；只显示 Ching 候选。
- 不涉及出版、G2/G3、合成器预览。

## 要改什么

- **配色**：`src/gxwd/web.py` 的 `PALETTE` 字典。
- **风格归属**：`src/gxwd/web.py` 的 `STYLE` 字典（与
  `docs/art-style-assignment-candidate.md` 一致，待艺术主编签字后
  建议迁移到 `data/art-style.json`）。
- **卡片内容**：`HTML_TEMPLATE` 里的 `renderDetail` / `renderResearch` 函数。
- **markdown 渲染**：极简实现 `mdToHtml`，支持标题/列表/粗体/行内 code/
  `[[text-id]]` 高亮；完整 CommonMark 请改用外部库。
