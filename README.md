# 观象悟道 · guanxiang-wudao

《周易》六十四卦国学研究、国画创作、企业哲学转译与数字出版的 **Agentic Studio**。
一卦一哲理 · 一卦一国画 · 一爻一故事 · 一卦一企业智慧。

[![CI](https://github.com/leapunion/guanxiangwudao/actions/workflows/ci.yml/badge.svg)](https://github.com/leapunion/guanxiangwudao/actions/workflows/ci.yml)
[![Deploy GH Pages](https://github.com/leapunion/guanxiangwudao/actions/workflows/pages.yml/badge.svg)](https://github.com/leapunion/guanxiangwudao/actions/workflows/pages.yml)
[![Release](https://img.shields.io/github/v/release/leapunion/guanxiangwudao)](https://github.com/leapunion/guanxiangwudao/releases)
[![PyPI](https://img.shields.io/pypi/v/gxwd?label=PyPI&color=547A83)](https://pypi.org/project/gxwd/)
[![License: MIT](https://img.shields.io/badge/License-MIT-A2B4A1.svg)](LICENSE)

**🌏 公开查看器：https://leapunion.github.io/guanxiangwudao/**

---

## 快速入口

### 👀 我是读者，想看

→ **[64 卦查看器](https://leapunion.github.io/guanxiangwudao/)**（公开在线）
- 文王卦序 · 卦符 SVG · 候选经文 · 研究稿 · 国画风格分组
- 每张卦卡两个按钮：📝 **指正此卡** 和 ✨ **建议改进**，一键开 pre-filled Issue
- 发现经文有误？[开 classical-text Issue](https://github.com/leapunion/guanxiangwudao/issues/new?template=classical_text_issue.yml)

### 🛠 我是开发者，想用

**从 PyPI 装**（最简单，等 PYPI_API_TOKEN Secret 配好后自动发布）：

```bash
pip install gxwd
gxwd --help
```

**从源码跑**：

```bash
git clone https://github.com/leapunion/guanxiangwudao.git
cd guanxiangwudao
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -e ".[dev]"

.venv/bin/python -m pytest -q        # 631 passed
.venv/bin/gxwd validate binary --all # 64/64
.venv/bin/gxwd status                # PUBLISHED=64
.venv/bin/gxwd web serve             # 本地查看器
```

或下载 [最新 release](https://github.com/leapunion/guanxiangwudao/releases/latest) 的 wheel 直接 `pip install path/to/gxwd-*.whl`。

### 🧭 我想参与运作 / 修订 / 治理

→ **[OPERATIONS.md](docs/OPERATIONS.md)**：五角色 · 四入口 · 一周周期 · 三条修订路径
→ **[GOVERNANCE.md](docs/GOVERNANCE.md)**：治理 V1→V2 条款、Agent approver 的代价与保留红线
→ **[CLAUDE.md](CLAUDE.md)**：全局原则 · 编码规则 · 红线

---

## 当前状态（截至 2026-10-30）

| 层 | 内容 | 状态 |
|---|---|---|
| **工程** | pytest 631 passed · validate 64/64 · CI 两 job 必须绿 · PR 必走 CODEOWNERS review | ✅ |
| **数据** | 文王卦序 · 卦符 SVG · 候选经文（Ching 通解稿） · 研究稿 · 风格分组 | ✅ |
| **发布** | 64/64 **PUBLISHED**，但 `signed_by_agent=64` / `signed_by_human=0` | ⚠️ 治理 V2 下合规，学术权威性已声明降级 |
| **艺术** | 艺术 brief 齐，master.png 为 1×1 占位（本轮未选定图像模型） | ⏳ |
| **底本** | `canonical-texts.json` 的 provenance 为 "Ching commentary round 67"，无实物页码核对 | ⏳ 等真人选底本 |
| **运作** | GH Pages 自动部署 · 周度健康检查 · Dependabot · Release workflow | ✅ |

**诚实声明**：本仓库在**治理 V2**（2026-10-29 项目所有者授权，见 [GOVERNANCE.md](docs/GOVERNANCE.md)）下合规。任何对外文案都应**避免宣称"学术出版物"**；准确说法是"治理 V2 下 Agentic 发布工厂的实证 + 64 卦数据底座（经文真人核对与真实国画待后续）"。

---

## 编码规则（硬约束）

阳 = `1`，阴 = `0`。`binary_bottom_to_top` 从初爻读到上爻，下卦在前、上卦在后。显示时六爻从上爻排到初爻，顺序与编码相反。

例：第 37 卦《风火家人》= 下离 `101` + 上巽 `011` = `101011`。

卦符 SVG 由 `gxwd.renderer` **程序**生成，**图像模型不得绘制卦符 / 汉字 / 印章**。

---

## 项目结构

```
data/          权威主数据（八卦、64 卦、384 爻、经文、来源、登记册、approvers）
schemas/       JSON Schema（10 份契约）
src/gxwd/      11 个模块：domain · validator · renderer · yao · workflow ·
               catalog · cli · texts · publisher · composer · web
tests/         631 pytest 用例
.claude/       agents（13 个岗位） · skills（24 个） · rules · hooks
assets/        hexagram-svg/（64 个程序生成卦符）
projects/      单卦工作区 × 64：research / art / reviews
output/        三层合成产物归档
docs/          PRD · 实施方案 · 艺术风格 · OPERATIONS · GOVERNANCE · HOW-TO · AUTOPILOT
```

---

## 核心约定

- Skill 优先；Agent 只在需要独立上下文或并行审查时启用
- 仓库是**唯一真相源**（system of record）
- 经典原文 · 义理解释 · 现代应用必须**分层保存**，不得混写
- 卦象数理是**确定性的**，由程序计算，不由模型推理
- 不编造历史证据；宁可标记「尚无合适的可靠案例」
- **未经授权，不得自动出版**

---

## 相关文档

- [OPERATIONS.md](docs/OPERATIONS.md) — 运营手册（本项目**日常怎么运转**）
- [GOVERNANCE.md](docs/GOVERNANCE.md) — 治理版本记录（V1→V2，可追溯回滚）
- [HOW-TO-RUN-AGENTS.md](docs/HOW-TO-RUN-AGENTS.md) — Agent 操作手册
- [AUTOPILOT.md](docs/AUTOPILOT.md) — 治理 V2 下 Agent 独立出版 pipeline
- [FINAL-DELIVERABLES.md](FINAL-DELIVERABLES.md) — 7 层交付清单 + 延展方向
- [CHANGELOG.md](CHANGELOG.md) — 版本演进
- [PUBLISHING.md](PUBLISHING.md) — 出版流程与人工审批门禁

---

## License

[MIT](LICENSE) © 2026 cavin
