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
}
PATH = ["RESEARCHED", "TEXT_VERIFIED", "ART_DRAFT", "ART_APPROVED",
        "LAYOUT_READY", "REVIEW_REQUIRED", "PUBLISHED"]


def _published_record() -> dict:
    record = build_catalog(HEXAGRAMS)["records"][0]
    for target in PATH:
        approval = APPROVAL if target == "PUBLISHED" else None
        record = transition(record, State(target), actor="tester", approval=approval)
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

    assert errors[0]["rule"] == "history_transition"


def test_validate_catalog_flags_invalid_state_without_raising():
    record = {"hexagram_id": 1, "state": "BOGUS", "history": []}

    errors = validate_catalog({"version": "1", "records": [record]})

    assert errors[0]["rule"] == "state"
