import json

from gxwd.catalog import build_catalog, load_catalog, save_catalog, summarize, validate_catalog
from gxwd.workflow import State, transition

HEXAGRAMS = [
    {"hexagram_id": 3, "name": "屯", "slug": "tun"},
    {"hexagram_id": 1, "name": "乾", "slug": "qian"},
    {"hexagram_id": 2, "name": "坤", "slug": "kun"},
]


def test_build_catalog_sorts_and_initializes_records():
    catalog = build_catalog(HEXAGRAMS)

    assert catalog["version"] == "1"
    assert [r["hexagram_id"] for r in catalog["records"]] == [1, 2, 3]
    assert catalog["records"][0] == {
        "hexagram_id": 1, "name": "乾", "slug": "qian",
        "state": "DRAFT", "version": "0.1.0", "history": [],
    }


def test_build_catalog_does_not_mutate_input():
    snapshot = json.dumps(HEXAGRAMS)

    build_catalog(HEXAGRAMS)

    assert json.dumps(HEXAGRAMS) == snapshot


def test_summarize_lists_all_states_with_zero():
    catalog = build_catalog(HEXAGRAMS)

    counts = summarize(catalog)

    assert set(counts) == {s.value for s in State}
    assert counts["DRAFT"] == 3
    assert sum(counts.values()) == 3
    assert counts["PUBLISHED"] == 0


def test_summarize_counts_mixed_states():
    catalog = build_catalog(HEXAGRAMS)
    records = [dict(r) for r in catalog["records"]]
    records[0]["state"] = "PUBLISHED"
    records[1]["state"] = "BLOCKED"

    counts = summarize({"version": "1", "records": records})

    assert (counts["PUBLISHED"], counts["BLOCKED"], counts["DRAFT"]) == (1, 1, 1)


def test_summarize_skips_invalid_state_records():
    """非法状态的记录不计入任何计数（R1 要求）。"""
    catalog = build_catalog(HEXAGRAMS)
    records = [dict(r) for r in catalog["records"]]
    records[0]["state"] = "BOGUS_STATE"

    counts = summarize({"version": "1", "records": records})

    # 2 valid DRAFT records + 1 bogus (skipped)
    assert counts["DRAFT"] == 2
    assert sum(counts.values()) == 2


def test_save_and_load_roundtrip_format(tmp_path):
    catalog = build_catalog(HEXAGRAMS)
    path = tmp_path / "sub" / "asset-catalog.json"

    save_catalog(catalog, path)

    text = path.read_text(encoding="utf-8")
    assert "乾" in text and "\\u" not in text
    assert text.endswith("}\n")
    assert text.startswith('{\n  "version"')
    assert load_catalog(path) == catalog


APPROVAL = {
    "approved_by": "reviewer",
    "approved_at": "2026-01-01T00:00:00+00:00",
    "gates": {"G1": "passed", "G2": "passed", "G3": "passed"},
    "release_version": "v1",
}
PATH = ["RESEARCHED", "TEXT_VERIFIED", "ART_DRAFT", "ART_APPROVED",
        "LAYOUT_READY", "REVIEW_REQUIRED", "PUBLISHED"]


def _published_record() -> dict:
    record = build_catalog(HEXAGRAMS)["records"][0]
    for target in PATH:
        approval = APPROVAL if target == "PUBLISHED" else None
        revision_scope = None
        record = transition(
            record,
            State(target),
            actor="tester",
            approval=approval,
            revision_scope=revision_scope,
        )
    return record


def test_validate_catalog_accepts_legit_publish_path():
    catalog = {"version": "1", "records": [_published_record()]}

    assert validate_catalog(catalog) == []


def test_validate_catalog_flags_published_without_approval():
    record = {**_published_record()}
    del record["approval"]

    errors = validate_catalog({"version": "1", "records": [record]})

    assert [e["rule"] for e in errors] == ["published_approval"]


def test_validate_catalog_flags_published_with_empty_history():
    record = {**_published_record(), "history": []}

    errors = validate_catalog({"version": "1", "records": [record]})

    assert "published_history" in [e["rule"] for e in errors]


def test_validate_catalog_flags_illegal_history_jump():
    record = _published_record()
    record["history"] = [{**record["history"][0], "to": "PUBLISHED"}, *record["history"][1:]]

    errors = validate_catalog({"version": "1", "records": [record]})

    assert errors[0]["rule"] in ("history_transition", "history_replay")


def test_validate_catalog_flags_invalid_state_without_raising():
    record = {"hexagram_id": 1, "state": "BOGUS", "history": []}

    errors = validate_catalog({"version": "1", "records": [record]})

    assert errors[0]["rule"] == "state"


# ── history_replay 新增测试 ──────────────────────────────────────────────────


def test_validate_catalog_history_replay_detects_forged_step():
    """篡改 history（跳过中间状态）应被 history_replay 检出。"""
    # 构造一条 RESEARCHED -> PUBLISHED 的非法 history（跳过多个状态）
    record = build_catalog(HEXAGRAMS)["records"][0]
    record = {
        **record,
        "state": "PUBLISHED",
        "approval": APPROVAL,
        "history": [
            {
                "from": "DRAFT",
                "to": "RESEARCHED",
                "actor": "tester",
                "note": "",
                "at": "2026-01-01T00:00:00+00:00",
            },
            {
                "from": "RESEARCHED",
                "to": "PUBLISHED",  # 非法：跳过 TEXT_VERIFIED 等中间状态
                "actor": "tester",
                "note": "",
                "at": "2026-01-01T01:00:00+00:00",
                "approval": APPROVAL,
            },
        ],
    }

    errors = validate_catalog({"version": "1", "records": [record]})

    rules = [e["rule"] for e in errors]
    assert "history_replay" in rules or "history_transition" in rules


def test_validate_catalog_history_replay_accepts_valid_path():
    """合法路径的 history 不应产生 history_replay 错误。"""
    record = _published_record()
    catalog = {"version": "1", "records": [record]}

    errors = [e for e in validate_catalog(catalog) if e["rule"] == "history_replay"]

    assert errors == []


def test_validate_catalog_history_replay_detects_revision_scope_path():
    """包含 REVISION_REQUIRED 的合法路径（含 revision_scope）应通过重放。"""
    record = build_catalog(HEXAGRAMS)["records"][0]
    record = transition(record, State.RESEARCHED, actor="a")
    record = transition(record, State.TEXT_VERIFIED, actor="a")
    # 进入 REVISION_REQUIRED 需要 revision_scope
    record = transition(record, State.REVISION_REQUIRED, actor="a", revision_scope="art")
    # art scope 允许回到 TEXT_VERIFIED
    record = transition(record, State.TEXT_VERIFIED, actor="a")

    catalog = {"version": "1", "records": [record]}
    errors = [e for e in validate_catalog(catalog) if e["rule"] == "history_replay"]

    assert errors == []


# ── revision_scope_required 新增测试 ────────────────────────────────────────


def test_validate_catalog_revision_scope_required_flags_missing_scope():
    """history 中迁入 REVISION_REQUIRED 但缺少 revision_scope 应被检出。"""
    record = build_catalog(HEXAGRAMS)["records"][0]
    # 手工构造一条缺少 revision_scope 的 REVISION_REQUIRED 迁入步骤
    record = {
        **record,
        "state": "REVISION_REQUIRED",
        "history": [
            {
                "from": "DRAFT",
                "to": "RESEARCHED",
                "actor": "a",
                "note": "",
                "at": "2026-01-01T00:00:00+00:00",
            },
            {
                "from": "RESEARCHED",
                "to": "REVISION_REQUIRED",
                "actor": "a",
                "note": "",
                "at": "2026-01-01T01:00:00+00:00",
                # revision_scope 故意缺失
            },
        ],
    }

    errors = validate_catalog({"version": "1", "records": [record]})

    rules = [e["rule"] for e in errors]
    assert "revision_scope_required" in rules or "history_replay" in rules


def test_validate_catalog_revision_scope_required_passes_when_present():
    """history 中迁入 REVISION_REQUIRED 且有 revision_scope 时不报错。"""
    record = build_catalog(HEXAGRAMS)["records"][0]
    record = transition(record, State.RESEARCHED, actor="a")
    record = transition(record, State.REVISION_REQUIRED, actor="a", revision_scope="text")

    errors = [
        e for e in validate_catalog({"version": "1", "records": [record]})
        if e["rule"] == "revision_scope_required"
    ]

    assert errors == []
