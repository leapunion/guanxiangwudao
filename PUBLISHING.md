# 如何发布 gxwd 到 PyPI

本文说明把 `gxwd` 作为"六十四卦数据底座"打成 wheel 并上传 PyPI 的
流程。本项目的权威内容资产（64 卦 JSON、SVG、Schema、模板）会
作为 package data 一起打包。

## 一、本地构建 wheel

```bash
# 1. 清理旧产物
rm -rf dist/ build/ src/*.egg-info

# 2. 装构建工具
.venv/bin/python -m pip install --upgrade pip build

# 3. 构建 sdist + wheel
.venv/bin/python -m build

# 4. 看产物
ls -lh dist/
# gxwd-0.1.0-py3-none-any.whl
# gxwd-0.1.0.tar.gz
```

## 二、本地安装验证

```bash
# 在一个干净的虚拟环境里装
python3.12 -m venv /tmp/test-gxwd
/tmp/test-gxwd/bin/pip install dist/gxwd-0.1.0-py3-none-any.whl
/tmp/test-gxwd/bin/gxwd validate binary --all   # 应该 64/64 通过
/tmp/test-gxwd/bin/gxwd hexagram show 37
```

## 三、发布到 TestPyPI（强烈推荐先发测试站）

```bash
.venv/bin/python -m pip install --upgrade twine

# 需要 TestPyPI 账号和 token（https://test.pypi.org/manage/account/token/）
.venv/bin/python -m twine upload --repository testpypi dist/*
```

从 TestPyPI 装回来验证：

```bash
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            gxwd
```

## 四、发布到正式 PyPI

```bash
# 需要 PyPI 账号和 API token（https://pypi.org/manage/account/token/）
.venv/bin/python -m twine upload dist/*
```

## 五、版本号规范

遵循 [SemVer](https://semver.org/lang/zh-CN/)：

- `0.1.0`：V0.1 可信底座（当前）
- `0.2.0`：V0.5 批次 B，首卦试点闭环完成
- `0.5.0`：64 卦试点全部完成，开始规模化
- `1.0.0`：64 卦全部出版、Rule 01-05 原文核对完毕

发布前更新：

1. `pyproject.toml` 的 `version`
2. `CHANGELOG.md` 新加一节
3. `git tag v0.1.0 && git push --tags`

## 六、0.1.0 的已知限制：wheel 不含数据

当前构建产生两件东西：

| 产物 | 大小 | 内容 | 装完可用否 |
|---|---|---|---|
| `gxwd-0.1.0.tar.gz` (sdist) | ~80 KB | 代码 + 全部 data/assets/schemas/templates | ✅ 装了直接能用 |
| `gxwd-0.1.0-py3-none-any.whl` | ~59 KB | 只含代码，data 以 `*.data/share/gxwd/` 格式随 wheel 走，位置依赖 install prefix | ⚠️ 装到 site-packages 时 CLI 找不到 data |

**0.1.0 的实际发布建议**：只发 **sdist**（`twine upload dist/*.tar.gz`），
用户 `pip install gxwd-0.1.0.tar.gz` 就能跑 `gxwd validate binary --all`。

**0.2.0 要做的事**：把 `data/`、`assets/hexagram-svg/`、`schemas/`、
`templates/card/` 挪到 `src/gxwd/_bundled/` 作为真正的 package data，
用 `importlib.resources` 读。本重构不影响 API，但要动 `domain.get_data_dir`、
`web.collect_bundle`、`composer._TEMPLATE_PATH`、`texts.load_canonical_texts`
的路径逻辑。预计 1 小时。做完后 wheel 就能装了。

## 七、本项目是否真的要发布？

**0.1.0 可发**：仅含数据底座 + 工具层（无 L0 原文 / 无国画 / 无
人工终审产物），授权 MIT。读者/下游用于编辑器插件、学习工具、
研究引用都 OK。

**0.2.0+ 慎重**：涉及真实 L0 原文（阮刻《十三经注疏》本影印页码
引用）、国画作品、企业哲学卡片的分发时，需要主编一一确认版权和
授权条款（见 `docs/image-and-licensing-decisions.md`）。

## 七、不打包的内容

本项目这些目录**不**进 wheel（看 `MANIFEST.in` 或 setuptools 默认
排除规则）：

- `projects/` — 单卦工作区（研究稿、候选经文、审查报告），都是
  内部产物。
- `inputs/human/` — 人工录入目录，不应打包分发。
- `output/` — 临时产物（预填 CSV、Ching 候选稿），每次重建。
- `docs/*.docx` — 原始 PRD。
- `web/*.html` — 查看器派生产物。

要分发查看器，用户装完包后跑 `gxwd web build` 和 `gxwd web serve`
自己生成。
