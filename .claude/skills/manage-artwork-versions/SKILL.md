---
name: manage-artwork-versions
description: Track, bump and reconcile version records for all hexagram artwork layers and composite cards, ensuring review records stay consistent after any layer update. Never auto-promotes version status.
---

# 作品版本管理（manage-artwork-versions）

## 职责
- 维护每卦各图层（Layer 1 / 2 / 3）及合成图卡的版本号记录。
- 当任一图层更新时，标记下游合成版本为 stale，并触发重检提示。
- 提供版本一致性检查：验证 `art-card-metadata.json` 中的三层版本号与各图层文件的实际版本一致。

## Input
- `hexagram_id`（可批量处理 1–64）
- `projects/<id>-<slug>/art/art-card-metadata.json`
- `projects/<id>-<slug>/art/hexagram-symbol-metadata.json`（Layer 2 版本）
- `projects/<id>-<slug>/art/calligraphy-seal-metadata.json`（Layer 3 版本）
- `projects/<id>-<slug>/reviews/`（g1/g2/g3 报告）

## Rules
- 版本号格式：`v<major>.<minor>`（主版本：内容重大变更；次版本：微调）。
- 任何图层更新必须同步更新版本号；不得保持旧版本号以规避重检。
- 经文修订（从 SOURCE_PENDING 升级为实际经文）视为主版本变更，相关作品强制标记 `review_required: true`。
- 版本降级（回退到旧版本）必须有人工授权；Agent 不得自行回退。
- 不修改源图层文件内容；只更新版本元数据。

## Output
- `projects/<id>-<slug>/art/artwork-versions.json`：字段含 hexagram_id、layer1_version、layer2_version、layer3_version、composite_version、last_updated、review_required
- Skill Contract V1.0 JSON，含 `stale_items[]`（需重检的条目）

## Failure
- 版本号互相矛盾或格式不合规 → `REVISION_REQUIRED`
- 图层文件缺失但版本号存在 → `BLOCKED`，交人工确认
- 永不自动清除 `review_required` 标记（须由人工或审查通过后清除）

## Implementation
- 半自动：CLI 脚本扫描 `art/` 目录文件修改时间，与版本记录比对；
- Agent 处理版本语义判断（主/次版本分类）；
- 调用 `.venv/bin/gxwd status <id>` 辅助确认各图层状态。
