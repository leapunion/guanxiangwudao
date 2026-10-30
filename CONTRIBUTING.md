# 贡献指南

欢迎到观象悟道！在动手之前，先了解几件对本项目**特别**的事。

---

## 一、这个项目和一般开源项目不一样

| 对比项 | 一般项目 | 观象悟道 |
|---|---|---|
| 真相源 | 代码 | 代码 + L0 经文 + 治理条款 |
| 发布门禁 | CI 过就能合 | CI 过 + CODEOWNERS review + publisher 硬检查 + 治理版本约束 |
| 诚实度 | 看情况 | 硬红线（禁编造经文/书名/ISBN/页码） |
| Agent 参与 | 一般不区分 | 身份分离 + `signed_by_agent` provenance 必须真实 |

**在动手前请先读 → [`docs/OPERATIONS.md`](docs/OPERATIONS.md) 和 [`CLAUDE.md`](CLAUDE.md)**。

---

## 二、我想贡献，从哪里开始

### 👀 我只想反馈不想写代码

直接开 Issue（不用 clone）：

- 📝 **经文/底本异议** → [classical-text Issue](https://github.com/leapunion/guanxiangwudao/issues/new?template=classical_text_issue.yml)
- 🐞 **发现 bug** → [bug_report Issue](https://github.com/leapunion/guanxiangwudao/issues/new?template=bug_report.yml)
- ✨ **功能建议 / 延展方向** → [feature_request Issue](https://github.com/leapunion/guanxiangwudao/issues/new?template=feature_request.yml)
- ⚖️ **治理条款变更提案** → [governance_proposal Issue](https://github.com/leapunion/guanxiangwudao/issues/new?template=governance_proposal.yml)

或者直接在 [GH Pages viewer](https://leapunion.github.io/guanxiangwudao/) 打开任一卦，点卡片详情里的「📝 指正此卡」按钮，Issue 会自动预填 `hexagram_id` 和卦名。

### 🛠 我想写代码

```bash
# 1. Fork + clone
gh repo fork leapunion/guanxiangwudao --clone
cd guanxiangwudao

# 2. 装环境（Python 3.12+）
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"

# 3. 跑测试，确认基线绿
.venv/bin/python -m pytest -q        # 应该 631 passed
.venv/bin/gxwd validate binary --all # 应该 64/64

# 4. 开 feature 分支
git checkout -b fix/some-issue

# 5. 改代码，加测试，再跑
.venv/bin/python -m pytest -q
```

---

## 三、贡献类型 × 边界

| 类型 | 允许的改动 | **严禁** 的改动 |
|---|---|---|
| 文档 / README / docs/*.md | 所有 | 治理红线条款（CLAUDE.md、`.claude/rules/*.md`、`docs/GOVERNANCE.md`）—— 必须走 `governance_proposal` Issue |
| 代码（`src/gxwd/`） | 功能/bug fix/新 CLI 子命令 | 绕过 `publisher.request_publication` 的 5 道硬检查 |
| 测试（`tests/`） | 新增用例 | 删除/弱化既有用例 |
| 工作流（`.github/workflows/*`） | 优化 | 用 `--no-verify` / 关 CI gate / 用 PAT 绕过 CODEOWNERS |
| Agent / Skill 骨架 | 新建、补 Input/Output/Failure/Implementation 四节 | 修改既有 Agent 的身份（会破坏 publisher 的 id 分离硬检查） |
| 数据 L0（`data/canonical-texts.json` 的 `original_text` 字段） | 只能通过 `classical_text` Issue 流程修订 | **直接 PR 改 original_text** |
| 数据 L1-L3（`projects/*/research/*.json` 等） | 可以 | 不要动已 PUBLISHED 卦的 `catalog.history` |
| 画作 PNG（`projects/*/art/master.png`） | 替换为真实渲染 | 用图像模型画卦符/汉字/印章（art-style.md 红线） |

---

## 四、Commit / PR 规范

### Commit message

- **语言**：中文（本项目的 commit-zh 规范）
- **格式**：`<type>(<scope>): <description>`
  - type: `feat` / `fix` / `docs` / `chore` / `test` / `refactor` / `release`
  - scope: 一个简短的作用域（如 `publisher` / `web` / `ci` / `H37`）
- **末尾**：如果有 AI 协作，加 `Co-Authored-By:` trailer

示例：
```
feat(web): 加卦卡搜索框

- 顶部增搜索输入，匹配卦名 / 全名 / 别名
- 回车跳到第一个匹配卦的 detail

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
```

### PR 要求

1. **走 PR 模板**：所有必选项打钩或填写
2. **CI 必须绿**：pytest + build wheel + install smoke 两个 job 都是 required status check
3. **CODEOWNERS review**：所有 PR 自动 request `@keevingfu`；外部贡献者无 approve 权限，等 cavin review
4. **一次 PR 只做一件事**：别把文档改 + 代码 fix + schema 变更混在一个 PR
5. **动 L0 数据 / 治理条款 / Agent 身份** → 先开 Issue 讨论，别直接 PR

### 分支命名

- `feat/xxx` 新功能
- `fix/xxx` bug 修复
- `docs/xxx` 文档
- `release/vX.Y.Z` 版本准备
- `auto/xxx` 自动化（如 Dependabot）

---

## 五、测试要求

- **新代码必须带测试**：pytest 的新用例，位置在 `tests/`
- **测试风格**：AAA（Arrange / Act / Assert），用描述性函数名
- **数据相关**：用 `tests/fixtures/` 的独立 fixture，不改真实 `data/*.json`
- **CI 跑的全集必须绿**：PR CI 不绿不能 merge

```bash
.venv/bin/python -m pytest -q                      # 全量
.venv/bin/python -m pytest tests/test_publisher.py # 单个
.venv/bin/python -m pytest -k "publisher"          # 按关键词
```

---

## 六、治理红线（最严格的一级）

**以下操作必须先开 `governance_proposal` Issue 并由 cavin 签字接受代价**：

- 修改 `CLAUDE.md`、`.claude/rules/*.md`、`docs/GOVERNANCE.md` 的任何条款
- 修改 `publisher.request_publication` 的 5 道硬检查逻辑
- 修改 `.claude/hooks/guard_write.py` 的 `GLOBAL_DENY` / `AGENT_DENY_PATTERNS`
- 修改 `data/approvers.json` 的 approver id 构成（新增/删除/改名）
- 修改 `signed_by_agent` 字段的语义或默认值

直接 PR 这些文件不会被接受。

---

## 七、L0 经文的修订（唯一通道）

**不能直接 PR 改 `data/canonical-texts.json` 的 `original_text` 字段**。

正确流程：
1. 开 `classical_text_issue.yml` 模板的 Issue
2. 填必填字段：`hexagram_id`、`text_id`、当前文本、建议文本、异议依据（哪个底本 / 校勘记）
3. 等 cavin 决定走 OPERATIONS.md 的[路径 1/2/3](docs/OPERATIONS.md#五修订如何合入)之一
4. 修订合入后对应卦的 `release_version` 升级

---

## 八、常见问题

### 我是 Agent，不是人，可以贡献吗

可以。治理 V2 下 Agent 身份合法，但：
- 必须用三类分离的身份之一（`agent-researcher` / `agent-verifier` / `autopilot`），不能自造新身份
- 产出必须带 `provenance.signed_by_agent=true`
- 不能批准自己的产出（publisher 硬检查）

见 `docs/HOW-TO-RUN-AGENTS.md` 和 `docs/AUTOPILOT.md`。

### 我 fork 后 CI 跑不起来

两个常见原因：
1. Pages workflow 需要 repo 启用 Pages：Settings → Pages → Source = GitHub Actions（fork 的仓库默认不启用）
2. Release workflow 需要 Secrets：PYPI_API_TOKEN（可选，没加时 PyPI step 自动 skip）

### 为什么 PR 需要那么多检查

本项目的产出是「国学经典的数字出版物」，发布质量门禁不是形式。真要 bypass 请走 governance_proposal 流程，不要用 `--no-verify` 或类似工具绕过。

---

## 九、相关文档

- [OPERATIONS.md](docs/OPERATIONS.md) — 本项目日常怎么运转
- [GOVERNANCE.md](docs/GOVERNANCE.md) — 治理版本与 Agent approver 条款
- [CLAUDE.md](CLAUDE.md) — 全局原则与红线
- [AGENTS.md](AGENTS.md) — 13 个 Agent 岗位
- [HOW-TO-RUN-AGENTS.md](docs/HOW-TO-RUN-AGENTS.md) — Agent 操作手册
- [SECURITY.md](SECURITY.md) — 安全报告流程

---

## License

贡献的所有代码按本项目 [MIT License](LICENSE) 授权。
