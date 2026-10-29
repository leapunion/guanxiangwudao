# output/canonical-input-prefilled/

Agent 用 `projects/<id>/research/candidate-text-from-ching.json` 的通行本经文**预填**好 `original_text` 和 `edition`。

剩下两列由主编人工填：

- `page`：对手头实物填具体页码（如 `19上`、`25下`）。
- `verification_status`：主编逐条核对无误后从 `pending` 改为 `verified`。

## 用法

```bash
# 1. 挑一卦，复制到 inputs/human/（人工专属目录）
cp output/canonical-input-prefilled/37-jiaren-canonical.csv inputs/human/

# 2. 编辑器打开，填 page + 改 verification_status
$EDITOR inputs/human/37-jiaren-canonical.csv

# 3. 单卦录入 + G1
./scripts/import-and-gate.sh 37 jiaren

# 多卦录入
./scripts/import-and-gate-all.sh
```

## 为什么是预填稿，不是正式 CSV

- `verification_status=pending` 不等于主编签字，`gxwd texts validate` 在 original_text 非 null + verification_status=pending 时会报 schema 不符 — 这是设计所要的，确保 Agent 预填的文字不能冒充 L0。
- Agent 不写 `inputs/human/`（hook 全局禁写）；主编手动 cp 过去。
- 把 60 份 CSV 从 15 行抄 Ching 文字 + 填 page/verified 降为只填 page/verified —— Agent 可做部分做满。
