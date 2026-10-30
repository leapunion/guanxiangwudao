---
name: publish-hexagram-collection
description: Bundle one or more approved hexagram art cards into a distributable collection package (PDF, digital folio or print-ready archive) after all gates pass and human approval is confirmed. Never self-approves.
---

# 六十四卦集结出版（publish-hexagram-collection）

## 职责
- 将已通过 G1+G2+G3 并获人工批准的单卦作品打包成集结出版物（PDF、数字合集或印刷就绪归档）。
- 生成出版元数据清单（版本、卦序、审查哈希）。
- 发布前最终检查：所有入选卦是否均有人工批准记录。

## Input
- 入选 hexagram_id 列表（可为 1–64 的子集）
- 每卦：`projects/<id>-<slug>/art/art-card-composite.*`
- 每卦：`projects/<id>-<slug>/reviews/g1-<slug>.json`、`g2-<slug>.json`、`g3-<slug>.json`
- 每卦：`projects/<id>-<slug>/approval.json`（含 approved_by、approved_at、gates G1/G2/G3）

## Rules
- 只有同时具备 G1+G2+G3 通过记录 **且** `approval.json` 中 approved_by 非空的作品才能入选。
- 经文仍为 SOURCE_PENDING 的作品不得入选。
- 打包操作不修改任何源文件；出版物是只读快照。
- 版本号与审查哈希写入出版清单；经文修订后相关卦标记为需重检，须重走审查流程。
- 任何 AI Agent 无权执行最终发布动作；发布由人工触发，凭密钥授权。

## Output
- `output/collections/<collection-slug>/`：含合成图卡、出版元数据
- `output/collections/<collection-slug>/manifest.json`：字段含 collection_id、created_at、hexagrams[]（每项含 hexagram_id、art_card_path、g1_hash、g2_hash、g3_hash、approved_by、approved_at）
- Skill Contract V1.0 JSON

## Failure
- 任一入选卦缺失批准记录或 G1/G2/G3 任一 fail → `BLOCKED`，整批阻断
- 入选卦中有 SOURCE_PENDING 经文 → `BLOCKED`
- 发布动作无人工授权触发 → `BLOCKED`
- 永不静默修复被审成果

## Implementation
- 半自动：Agent 核查批准记录，CLI 脚本打包；
- 调用 `.venv/bin/gxwd status` 批量检查各卦状态；
- 打包脚本读取 `approval.json` 并写入 manifest；发布密钥由人工提供，不进入日志。
