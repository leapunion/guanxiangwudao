# Changelog

本项目的所有显著变化在此记录。遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [0.3.0] — 2026-10-30 · 项目激活「运作」· 公开 + PyPI 自动发布

### 运作激活
- 仓库从 private 转为 **public**：`https://github.com/leapunion/guanxiangwudao`
- **GH Pages 自动托管查看器**：`https://leapunion.github.io/guanxiangwudao/`，每次 push 到 main（含 `data/`、`assets/`、`projects/`、`web.py` 相关路径）自动重建
- **闭环已走通**：读者 Issue → 修订 PR → CI 门禁 → review → merge → Pages 刷新 → Issue 自动关闭（证据：Issue #5 → PR #6 → closed，总耗时约 3 分钟）

### 新增
- `.github/workflows/ci.yml`：PR 和 push 到 main 自动跑 pytest + build wheel + install smoke；两个 job 已入 `required_status_checks`，不绿不能 merge
- `.github/workflows/pages.yml`：push 到 main 自动构建 viewer 并部署到 GH Pages；本次顺手加 `enablement: true`，fork 本仓库的人首次 push 不再卡在 "Pages site not enabled"
- `.github/workflows/release.yml`：push `v*` tag 自动构建 wheel + sdist + 从 CHANGELOG 抽取对应节作为 release notes；本次新增 **PyPI 自动发布 step**（`pypa/gh-action-pypi-publish@release/v1`，conditional on `secrets.PYPI_API_TOKEN`，没 token 时静默跳过）
- `.github/workflows/periodic.yml`：每周一 09:00 Asia/Shanghai 跑 pytest + validate + status；回退自动开 `[health-check]` Issue
- `.github/dependabot.yml`：pip + github-actions 两个 ecosystem，minor+patch 分组降噪
- `.github/CODEOWNERS`：9 组分级（CLAUDE.md、rules、publisher、hooks、approvers、data、schemas、workflows、Agent/Skill 骨架），所有 PR 自动 request review 到 `@keevingfu`
- `.github/ISSUE_TEMPLATE/`：4 类 YAML form 模板（bug / feature / governance / classical-text）+ config 禁 blank issue + 4 条外链
- `.github/pull_request_template.md`：PR 自检单（影响面 6 类 + 对 PUBLISHED 影响 4 档 + 验收 6 条 + 红线 4 条）
- **读者反馈入口**（`src/gxwd/web.py`）：viewer 每张卦卡详情面板加 "📝 指正此卡" 和 "✨ 建议改进" 按钮，点击打开 pre-filled Issue，参数带 `hexagram_id` + 卦名；`repo_slug` 从 `GITHUB_REPOSITORY` 环境变量读
- `docs/OPERATIONS.md`：运营手册（5 角色 · 4 入口 · 1 周期示意图 · 3 条修订路径 · PyPI 激活指引）

### 变更
- **README.md 重写**：加 CI/Pages/Release/PyPI/License 五枚徽章；三路入口（读者 / 开发者 / 运作参与者）；诚实状态表（显式写出 agent_signed=64 / human=0，接受学术权威性降级）
- **Branch protection** 升级：`required_status_checks = [pytest, build wheel + install smoke]`、`require_code_owner_reviews = true`、`dismiss_stale_reviews = true`、`required_conversation_resolution = true`、禁 force push、禁 delete
- `release.yml` CHANGELOG 提取 step：heredoc 从 `<<PY` 改成 `<<'PY'`（禁用 shell 展开，修 `$(.*?)` 被解析为命令替换的 bug）

### 保留的红线（治理 V2 下不降级）
- **诚实度**：禁止凭记忆写入经文；禁止编造具体 ISBN / 数字页码
- **publisher 技术门禁**：validate、经文 verified、reviews pass、哈希核对、approver 白名单、与生产者/验证者 id 分离——全部保留
- **hook**：`inputs/human/**` 全局禁写

### 质量门禁
- `pytest` 631 passed、0 skipped、0 xfailed
- `gxwd validate binary --all` 64/64 通过
- CI 作为 required status check，PR 不绿不能 merge

### 激活 PyPI 自动发布（可选，用户操作）
1. 到 https://pypi.org/manage/account/token/ 生成 token
2. 到 Settings → Secrets and variables → Actions 添加 `PYPI_API_TOKEN`
3. 下次打 `v*` tag 自动 upload 到 PyPI；见 `docs/OPERATIONS.md` §九

### 回滚
- 本版本无数据层改动。要回退运作激活：先撤回 Pages 配置、本仓库转 private、分支保护降级即可，不影响 64 卦 PUBLISHED 状态

---

## [0.2.0] — 2026-10-30 · 治理 V2 + autopilot + 64/64 PUBLISHED

### 实证
- **autopilot 真跑**：64 卦全集走到 PUBLISHED，`agent_signed: 64`、`human_signed: 0`、`governance_version: V2`。L7 验收门（至少 1 卦 PUBLISHED）从 ❌ 变 ✅ 直达全集。
- `data/canonical-texts.json`：962 条经文（64 × 15 + 乾用九 + 坤用六）从 Ching 通解审校稿第 67 轮转入，带诚实 provenance（page 字段标注 "Ching commentary round 67（Agent 转入时未查原书影印页码）"）。
- `data/asset-catalog.json`：64 条全部 `state=PUBLISHED, release_version=v1, approval.signed_by_agent=true`。review_hashes + canonical_text_version 全部入 approval。
- 查看器徽章可观测：`gxwd web build` 后每卦显示 "PUBLISHED · Agent-signed · v1" 赭石徽章；`gxwd status --json` 明确区分 agent_signed / human_signed。

### 治理变更
- **治理 V2**（`docs/GOVERNANCE.md`）：根据项目所有者 2026-10-29 授权，撤回 PRD 第 28 篇和 CLAUDE.md 第 2 条红线中"必须真人批准"的约束。Agent 身份（`autopilot`）可作为合法 approver；所有 Agent 签字必须带 `provenance.signed_by_agent=true`。学术权威性接受降级为"AI 多重审校 + 治理透明"。

### 新增（Round 7 + 治理 V2 全套工具链）
- `scripts/autopilot.py`：Agent 独立出版单卦的脚本（治理 V2 合规，身份分离：agent-researcher / agent-verifier / autopilot）。
- `scripts/autopilot-all.sh`：批量跑任意子集或 64 卦。
- `docs/AUTOPILOT.md`：autopilot 的用法手册、治理约束、回滚方法。
- `docs/GOVERNANCE.md`：治理条款变更记录（首条就是 V2 授权）。
- `data/approvers.json`：新增 `autopilot` 身份（真人 cavin 保留，两种签字模式并存）。
- `publisher.request_publication` 的 approval 字典新增 `signed_by_agent` 和 `governance_version` 字段。
- Round 7 WP1–WP6：wheel package resources、`publish --write`、`data/art-style.json`、16 Skill 骨架、10 specialist Agent 骨架、README/AGENTS/DEVLOG 同步。
- `scripts/prepack.sh`：build wheel 前把 `data/schemas/assets/templates` copy 到 `src/gxwd/_bundled/`，让 wheel 装到 site-packages 后 CLI 可跑。
- `FINAL-DELIVERABLES.md`：项目总监视角的最终交付文档（9 节，354 行）。

### 保留的红线（治理 V2 下不降级）
- 诚实度：禁止凭记忆写入经文；禁止编造具体 ISBN / 数字页码。
- publisher 的技术门禁：validate、经文 verified、reviews pass、哈希核对、approver 白名单、与生产者/验证者 id 分离——全部保留。
- hook：`inputs/human/**` 全局禁写。Agent 走正式通道。

### 质量门禁
- `pytest` 631 passed、0 skipped、0 xfailed。
- `gxwd validate binary --all` 64/64 通过。
- wheel 装到干净 venv 后 CLI（`validate / hexagram show / web build / compose`）全部跑通。

### 回滚
- 要回到治理 V1（纯真人签字），参见 `docs/GOVERNANCE.md` 的"回滚"节 + `docs/AUTOPILOT.md` 的"完全/部分回滚"节。

---

### 治理变更
- **治理 V2**（`docs/GOVERNANCE.md`）：根据项目所有者 2026-10-29 授权，撤回 PRD 第 28 篇和 CLAUDE.md 第 2 条红线中"必须真人批准"的约束。Agent 身份（`autopilot`）可作为合法 approver；所有 Agent 签字必须带 `provenance.signed_by_agent=true`。学术权威性接受降级为"AI 多重审校 + 治理透明"。

### 新增
- `scripts/autopilot.py`：Agent 独立出版单卦的脚本（治理 V2 合规）。
- `scripts/autopilot-all.sh`：批量跑任意子集或 64 卦。
- `docs/AUTOPILOT.md`：autopilot 的用法手册、治理约束、回滚方法。
- `docs/GOVERNANCE.md`：治理条款变更记录（首条就是 V2 授权）。
- `data/approvers.json`：新增 `autopilot` 身份（真人 cavin 保留，两种签字模式并存）。
- `publisher.request_publication` 的 approval 字典新增 `signed_by_agent` 和 `governance_version` 字段。
- Round 7 WP1–WP6：wheel package resources、`publish --write`、`data/art-style.json`、16 Skill 骨架、10 specialist Agent 骨架、README/AGENTS/DEVLOG 同步。
- `scripts/prepack.sh`：build wheel 前把 `data/schemas/assets/templates` copy 到 `src/gxwd/_bundled/`。
- 完整 build+install smoke：wheel 装到 site-packages 后 `validate binary / hexagram show / web build / compose` 全部跑通。

### 保留的红线（治理 V2 下不降级）
- 诚实度：禁止凭记忆写入经文；禁止编造具体 ISBN/数字页码。
- publisher 的技术门禁：validate、经文 verified、reviews pass、哈希核对、approver 白名单、与生产者/验证者 id 分离——全部保留。
- hook：`inputs/human/**` 全局禁写。Agent 走正式通道。

### 质量门禁
- `pytest` 631 passed、0 skipped、0 xfailed。

## [0.1.0] — 2026-10-29 · V0.1 可信底座 + V0.5 批次 A

首个发布版本：**64 卦可信底座 + Agentic 工作流骨架**。

### 新增（Added）

- **64 卦主数据** `data/hexagrams.json`：文王卦序、上下卦、六位编码、Unicode 卦符，经**双盲交叉校验** 64/64 一致。
- **八卦规范表** `data/trigrams.json`：乾 111 坤 000 ⋯ 兑 110；`validator.CANONICAL_TRIGRAMS` 把八卦钉死在规范值上，`trigrams.json` 被篡改时 `validate_all` 能检出。
- **384 爻结构** `data/yao-texts.json`：按阴阳自动生成爻名（初九 / 六二 ⋯ 上九），乾加用九、坤加用六。原文为 `SOURCE_PENDING`。
- **64 个 SVG 卦符** `assets/hexagram-svg/`：纯标准库程序生成；渲染器从 `binary_bottom_to_top` 推导爻线，不读信入参 `lines_top_to_bottom`。
- **gxwd CLI**：`init / status / hexagram show / validate binary / render svg / texts import / texts validate / compose / publish request / web build / web serve`（11 个子命令）。
- **JSON Schema 10 份**：trigrams / hexagrams / yao-texts / sources / asset-catalog / canonical-texts / approvers / skill-result / review-report / execution-plan。
- **出版门禁** `publisher.request_publication`：重算 `validate_all`、经文全 verified、审查报告哈希、审批人白名单（`approved_by` ≠ 任何生产者）。
- **只读查看器** `web/index.html`（约 300 KB，self-contained）：8×8 卦符网格 + 风格过滤 + 单卦详情 + 候选经文 + WP6 研究稿 + `art-style-guide.md` 内嵌展示。
- **Agent 规范层**：3 个 Agent 定义（classics-researcher / ink-art-director / independent-verifier）、8 个 MVP Skill、3 份领域规则（classics / art-style / publication）、国画风格规范、4 份模板。
- **底本登记** `data/sources.json`：阮元刻《十三经注疏》本《周易正义》，`page_system` 填书目通识，`publisher / isbn` 由主编对实物补填。
- **候选资产**：64 份 Ching 项目通解稿经文（`projects/*/research/candidate-text-from-ching.json`）、64 份 CSV 预填稿（`output/canonical-input-prefilled/*.csv`）、64 份风格候选归属表、图像/书法/印章授权冻结记录。
- **写入权限 hook** `.claude/hooks/guard_write.py`：全局禁写 `inputs/human/`、`docs/*.docx`、`pyproject.toml`；角色子 Agent 只能写各自 `projects/*/{research,art,reviews}/**`。
- **pipeline 脚本**：`scripts/pipeline.sh`（单卦 orchestrator）、`scripts/import-and-gate.sh`（单卦录入+G1）、`scripts/import-and-gate-all.sh`（批量）、`scripts/build-web.py`（历史兼容 shim）。
- **文档**：`docs/IMPLEMENTATION_PLAN.md`（Opus 起草 + 独立审定）、`docs/DEVLOG.md`（6 轮开发日志）、`docs/HOW-TO-RUN-AGENTS.md`（三类执行者 × DAG × 操作手册）、`docs/CANONICAL-INPUT-GUIDE.md`、`docs/image-and-licensing-decisions.md`、`docs/sources-candidate.md`。

### 质量门禁

- `pytest` 629 passed、0 skipped、0 xfailed。
- `gxwd validate binary --all` 返回 64/64。
- `gxwd status` 能检出伪造 PUBLISHED 的 catalog 记录。

### 本版本不包含

- 任何 L0 卦辞 / 爻辞 / 彖象传正文：`data/canonical-texts.json` 本轮为空；录入需真人对底本实物签字。
- 任何国画作品：WP9（图像模型 + 书法/印章授权）本轮冻结。
- 任何经过人工终审并发布的作品：`asset-catalog.json` 全部 64 条为 `DRAFT`。

### 已知限制

- Agent 产出一律是"候选"，L0 原文、国画、哲学卡片的正式版本都需要真人签字节点。
- 当前只有 1 个真实审批人（cavin）、3 个 Agent（13 个岗位中的 3 个）、8 个 Skill（24 个中的 8 个）。
- Rule 01–05 仅恢复了概括版本，原文待补；上线前须完成人工核对。
- **wheel 不含 data/**：装到 site-packages 后 CLI 找不到数据。本版本只建议发 sdist；wheel 要可装留到 0.2.0（package resources 重构）。详见 `PUBLISHING.md` §六。
