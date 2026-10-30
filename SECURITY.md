# 安全策略

## 支持的版本

本项目目前以**最新的 minor 版本**为支持对象。

| 版本 | 支持状态 |
|---|---|
| 0.3.x | ✅ 支持 |
| 0.2.x | ❌ 建议升级到 0.3.x |
| 0.1.x | ❌ 不再支持 |

升级很简单——没有 breaking change；`data/` 和 `schemas/` 向后兼容。

---

## 如何报告安全问题

### ✅ 这些**是**安全问题，请私下报告

- `publisher.request_publication` 的 5 道硬检查有办法 bypass（白名单 / 哈希校对 / id 分离 / 经文 verified / state 合法性）
- `.claude/hooks/guard_write.py` 的 `inputs/human/**` 禁写有办法绕过
- `catalog.history` 可以被篡改且不留追溯链
- `provenance.signed_by_agent` 字段可以被伪造（真人产出被误标为 agent，或反之）
- CI / release workflow 可以上传任意内容到 PyPI / GitHub Release
- Agent 身份 `agent-researcher` / `agent-verifier` / `autopilot` 的 id 分离硬检查失效
- 任何让 L0 经文（`data/canonical-texts.json` 的 `original_text`）被 Agent 直接写入而没有真人路径的通道

**报告方式**（任选其一，推荐 GitHub Security Advisory）：

1. **GitHub Security Advisory**（推荐）：
   https://github.com/leapunion/guanxiangwudao/security/advisories/new
   仅 maintainer 可见，直到你和 maintainer 同意公开。

2. **私下邮件**：vovolhuang@gmail.com
   标题带 `[security]` 前缀。
   不要在公开 Issue、PR、discussion 里讨论未修复的安全问题。

### ❌ 这些**不是**安全问题，请走正常 Issue

- "L0 经文有误 / 底本标注不准" → [`classical_text_issue.yml`](https://github.com/leapunion/guanxiangwudao/issues/new?template=classical_text_issue.yml)
- "画作太丑 / 艺术风格不对" → [`feature_request.yml`](https://github.com/leapunion/guanxiangwudao/issues/new?template=feature_request.yml)
- "我不同意治理 V2 让 Agent 批准" → [`governance_proposal.yml`](https://github.com/leapunion/guanxiangwudao/issues/new?template=governance_proposal.yml)
- "CLI 报错" → [`bug_report.yml`](https://github.com/leapunion/guanxiangwudao/issues/new?template=bug_report.yml)
- 查看器不好用 → feature_request

**学术性异议、艺术性批评、治理哲学分歧不是安全问题**，不需要走私下通道，应该公开讨论。

---

## 响应时间

本项目是单人 maintainer（@keevingfu）。承诺：

- **24 小时内**：确认收到报告
- **7 天内**：评估严重程度、给出初步计划
- **30 天内**：发布修复或说明不修复的理由

严重问题（可以让任意 Agent 冒充真人签字、或让 L0 经文被伪造）会插队。

---

## 披露政策

- 修复发布后，可能在 GitHub Security Advisory 和 CHANGELOG 中公开（标注 `[security]`）
- 报告者可以匿名或署名；默认匿名
- 没有 bug bounty（本项目无营收）
- 对帮助项目的研究者，maintainer 会在 CHANGELOG 的 "Credits" 节公开感谢（经你同意）

---

## 已知的「不是漏洞是红线」

这些是**显式允许**的，不要作为漏洞报告：

- `enforce_admins=false`：admin（@keevingfu）可以 bypass branch protection 直接 push / override merge。这是单人项目的工作模式。要改请开 governance_proposal
- `signed_by_agent=true` 的作品被认为合规：治理 V2 下这是预期行为，接受学术权威性降级，见 `docs/GOVERNANCE.md`
- `canonical-texts.json` 的 provenance.page 全是 "Ching commentary round 67"：Agent 诚实承认未查原书影印页码，不是伪造；要换真实页码走真人路径（见 `docs/OPERATIONS.md` §五）

---

## 密钥 / Secrets 泄露

如果你发现：

- `PYPI_API_TOKEN` 等 Secret 出现在日志 / commit / Issue 评论中
- 任何 Agent 的 token / API key 被 commit

**立即走私下通道**（见上），不要在公开地方讨论。maintainer 会：
1. 立即 rotate 相关 Secret
2. 清理 git 历史（可能需要 force push，这是允许本项目破例的场景）
3. 追查谁有权限访问

---

## License

本安全策略按 [MIT License](LICENSE) 授权。
