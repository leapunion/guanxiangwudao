# Changelog

本项目的所有显著变化在此记录。遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

## [0.1.0] — 2026-10-29

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
