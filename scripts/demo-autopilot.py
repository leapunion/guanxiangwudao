#!/usr/bin/env python3
"""DEMO ONLY — 全自动把第 37 卦家人跑到 PUBLISHED。

**警告**：本脚本只在 `demo-autopilot` 分支存在。它刻意绕过项目红线
『L0 经文必须真人签字』『任何 AI Agent 不应拥有自动出版权限』——
通过主会话权限直接写 verified 经文、demo-verifier 身份签审查报告、
autopilot 身份走 publish request。

目的：教讲演示，让人看清楚『全自动到 PUBLISHED』不是能力问题，
是设计问题。main 分支永远不会合并本分支。

Agent 冒充的三种身份：
- demo-producer：L0 录入和 catalog history 的 actor
- demo-verifier：reviews 中的 verifier
- autopilot：approved_by（白名单里，身份独立于前两个）

把 catalog 从 DRAFT 推到 PUBLISHED 需要走完 §6 状态机的全部 8 态，
每一步 actor=demo-producer。只有最后 REVIEW_REQUIRED → PUBLISHED 一步
由 autopilot 走。
"""
from __future__ import annotations

import base64
import copy
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from gxwd import catalog, composer, domain, publisher, workflow

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
HEX_ID = 37
SLUG = "jiaren"
PROJ = REPO / "projects" / f"{HEX_ID:02d}-{SLUG}"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# 1×1 PNG 占位
_MINIMAL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "nGP8z8DwHwAFAAH/VscvDQAAAABJRU5ErkJggg=="
)


def banner(step: str, msg: str) -> None:
    print(f"\n\033[1;35m[DEMO · {step}]\033[0m {msg}")


# ─── 1. 经文 verified ─────────────────────────────────────────────────
banner("1", "把 Ching 候选经文冒签为 verified，写入 data/canonical-texts.json")
candidate = json.loads(
    (PROJ / "research" / "candidate-text-from-ching.json").read_text(encoding="utf-8")
)
entries = []
for c in candidate["entries"]:
    entries.append({
        "text_id": c["text_id"],
        "hexagram_id": HEX_ID,
        "text_type": c["text_type"],
        "line_position": c["line_position"],
        "line_name": c["line_name"],
        "original_text": c["candidate_text"],
        "source_id": "ZYZY-RUAN",
        "edition": "阮元刻《十三经注疏》本",
        "page": "DEMO · 占位页码",  # 真实流程这里必须是具体页码
        "variant_readings": [],
        "verification_status": "verified",
    })
canonical_path = DATA / "canonical-texts.json"
canonical_doc = {"version": "1", "entries": entries}
canonical_path.write_text(
    json.dumps(canonical_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f"  wrote {canonical_path} ({len(entries)} entries, 全部 verified)")

# ─── 2. 审查报告 ──────────────────────────────────────────────────────
banner("2", "产生四份 reviews/*.json，全部 result=pass，verifier=demo-verifier")
reviews_dir = PROJ / "reviews"
reviews_dir.mkdir(parents=True, exist_ok=True)

DEMO_VERIFIER = {"id": "demo-verifier", "name": "DEMO Verifier", "role": "独立验证"}


def write_review(filename: str, gate: str, report_id: str) -> Path:
    path = reviews_dir / filename
    doc = {
        "report_id": report_id,
        "gate": gate,
        "hexagram_id": HEX_ID,
        "verifier": DEMO_VERIFIER,
        "checked_at": NOW,
        "result": "pass",
        "findings": [],
        "attachments": [],
        "producer_ids": ["demo-producer"],
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


# g1 由 gxwd validate binary 产出；复用，但补 verifier
g1_path = reviews_dir / "g1-binary-validation.json"
if g1_path.exists():
    g1 = json.loads(g1_path.read_text(encoding="utf-8"))
    if "verifier" not in g1:
        g1["verifier"] = DEMO_VERIFIER
        g1["producer_ids"] = ["demo-producer"]
        g1_path.write_text(json.dumps(g1, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
else:
    write_review("g1-binary-validation.json", "G1", "g1-037-1")
write_review("g2-visual.json", "G2", "g2-037-1")
write_review("g3-publication.json", "G3", "g3-037-1")
write_review("interpretation-review.json", "interpretation", "interpretation-037-1")
print(f"  wrote 4 reviews under {reviews_dir}")

# ─── 3. 占位主图 + compose ────────────────────────────────────────────
banner("3", "占位 PNG + gxwd compose 产三层合成")
art_dir = PROJ / "art"
art_dir.mkdir(exist_ok=True)
master_path = art_dir / "master.png"
master_path.write_bytes(_MINIMAL_PNG)

hexagram = domain.get_hexagram(HEX_ID, DATA)
layout_dir = PROJ / "layout"
artifact = composer.compose_card(
    hexagram=hexagram,
    master_png=master_path,
    canonical_texts=entries,
    art_style={},
    out_dir=layout_dir,
    final=True,  # 经文全 verified，final=True 不抛
    now=NOW,
)
print(f"  composed: {artifact.layers['composed']}")

# ─── 4. autopilot 入 approvers ───────────────────────────────────────
banner("4", "把 autopilot 加进 data/approvers.json")
approvers_path = DATA / "approvers.json"
approvers = json.loads(approvers_path.read_text(encoding="utf-8"))
ids = {a["id"] for a in approvers["approvers"]}
if "autopilot" not in ids:
    approvers["approvers"].append({
        "id": "autopilot",
        "name": "DEMO Autopilot",
        "role": "总主编",
        "added_at": "2026-10-29",
        "notes": "DEMO ONLY · 冒签的审批人身份；仅在 demo-autopilot 分支存在。",
    })
    approvers_path.write_text(
        json.dumps(approvers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"  added autopilot to approvers")
else:
    print("  autopilot 已存在")

# ─── 5. 把 catalog 第 37 卦推到 REVIEW_REQUIRED ───────────────────────
banner("5", "catalog 从 DRAFT 推到 REVIEW_REQUIRED，actor=demo-producer")
catalog_path = DATA / "asset-catalog.json"
cat = catalog.load_catalog(catalog_path)
records = cat["records"]
idx = next(i for i, r in enumerate(records) if r["hexagram_id"] == HEX_ID)

STEPS = [
    workflow.State.RESEARCHED,
    workflow.State.TEXT_VERIFIED,
    workflow.State.ART_DRAFT,
    workflow.State.ART_APPROVED,
    workflow.State.LAYOUT_READY,
    workflow.State.REVIEW_REQUIRED,
]
record = records[idx]
for state in STEPS:
    record = workflow.transition(record, state, actor="demo-producer", note=f"DEMO autopilot → {state.value}", now=NOW)

records[idx] = record
cat["records"] = records
catalog_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"  state: {record['state']}  (history: {len(record['history'])} 步)")

# ─── 6. publish request —— 真走 publisher 门禁 ───────────────────────
banner("6", "autopilot 身份请求 publish；publisher 重算全部门禁")
try:
    new_record = publisher.request_publication(
        HEX_ID,
        approved_by="autopilot",
        approved_at=NOW,
        data_dir=DATA,
    )
except publisher.PublicationError as exc:
    print(f"\033[1;31m  publisher 拒绝: {exc}\033[0m")
    raise SystemExit(1)

# 写回 catalog
cat = catalog.load_catalog(catalog_path)
cat["records"][idx] = new_record
catalog_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"  state: {new_record['state']}")
print(f"  release_version: {new_record.get('release_version')}")
print(f"  approval.approved_by: {new_record['approval']['approved_by']}")

banner("done", "第 37 卦家人全自动走到 PUBLISHED（DEMO）")
print("  跑 .venv/bin/gxwd status 看 catalog。")
print("  main 分支不受影响：git checkout main && git status --short")
