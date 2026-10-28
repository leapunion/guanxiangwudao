import copy

import pytest

from gxwd.workflow import TRANSITIONS, State, TransitionError, transition

NOW = "2026-01-01T00:00:00+00:00"
GOOD_APPROVAL = {
    "approved_by": "主编",
    "approved_at": "2026-01-02T10:00:00+08:00",
    "gates": {"G1": "passed", "G2": "passed", "G3": "passed"},
}

# 按 IMPLEMENTATION_PLAN §6 手工硬编码的期望迁移表（不得从被测代码生成）。
EXPECTED_TABLE = {
    "DRAFT": {"RESEARCHED", "BLOCKED"},
    "RESEARCHED": {"TEXT_VERIFIED", "REVISION_REQUIRED", "BLOCKED"},
    "TEXT_VERIFIED": {"ART_DRAFT", "REVISION_REQUIRED", "BLOCKED"},
    "ART_DRAFT": {"ART_APPROVED", "REVISION_REQUIRED", "REJECTED"},
    "ART_APPROVED": {"LAYOUT_READY", "REVISION_REQUIRED"},
    "LAYOUT_READY": {"REVIEW_REQUIRED", "REVISION_REQUIRED"},
    "REVIEW_REQUIRED": {"PUBLISHED", "REJECTED", "REVISION_REQUIRED"},
    "PUBLISHED": {"REVISION_REQUIRED"},
    "BLOCKED": {"DRAFT", "RESEARCHED"},
    "REVISION_REQUIRED": {"DRAFT", "RESEARCHED"},
    "REJECTED": {"DRAFT"},
}
ALL_STATES = sorted(EXPECTED_TABLE)
ALL_PAIRS = [(s, t) for s in ALL_STATES for t in ALL_STATES]


def make(state: State) -> dict:
    return {"hexagram_id": 37, "state": state.value, "history": []}


def test_table_covers_all_eleven_states():
    assert set(TRANSITIONS) == set(State)
    assert len(State) == 11


def test_table_is_immutable():
    with pytest.raises(TypeError):
        TRANSITIONS[State.DRAFT] = frozenset()  # type: ignore[index]


def test_table_equals_hardcoded_expected_table():
    actual = {src.value: {dst.value for dst in dsts} for src, dsts in TRANSITIONS.items()}

    assert actual == EXPECTED_TABLE


def test_state_enum_matches_expected_states():
    assert sorted(s.value for s in State) == ALL_STATES
    assert len(ALL_PAIRS) == 121


def test_published_only_predecessor_is_review_required():
    predecessors = {src for src, dsts in EXPECTED_TABLE.items() if "PUBLISHED" in dsts}
    actual = {src.value for src, dsts in TRANSITIONS.items() if State.PUBLISHED in dsts}

    assert predecessors == {"REVIEW_REQUIRED"}
    assert actual == {"REVIEW_REQUIRED"}


@pytest.mark.parametrize(("src", "dst"), ALL_PAIRS)
def test_transition_matches_expected_table(src, dst):
    record = make(State(src))
    approval = GOOD_APPROVAL if dst == "PUBLISHED" else None

    if dst in EXPECTED_TABLE[src]:
        result = transition(record, State(dst), actor="alice", approval=approval, now=NOW)
        assert result["state"] == dst
    else:
        with pytest.raises(TransitionError):
            transition(record, State(dst), actor="alice", approval=GOOD_APPROVAL, now=NOW)


@pytest.mark.parametrize("actor", ["", "   "])
def test_empty_actor_raises(actor):
    with pytest.raises(TransitionError):
        transition(make(State.DRAFT), State.RESEARCHED, actor=actor)


def test_published_without_approval_raises():
    with pytest.raises(TransitionError):
        transition(make(State.REVIEW_REQUIRED), State.PUBLISHED, actor="a")


@pytest.mark.parametrize("gate", ["G1", "G2", "G3"])
@pytest.mark.parametrize("value", ["failed", "pending", None])
def test_published_with_unpassed_gate_raises(gate, value):
    approval = copy.deepcopy(GOOD_APPROVAL)
    approval["gates"][gate] = value

    with pytest.raises(TransitionError):
        transition(make(State.REVIEW_REQUIRED), State.PUBLISHED, actor="a", approval=approval)


def test_published_with_missing_gate_raises():
    approval = copy.deepcopy(GOOD_APPROVAL)
    del approval["gates"]["G3"]

    with pytest.raises(TransitionError):
        transition(make(State.REVIEW_REQUIRED), State.PUBLISHED, actor="a", approval=approval)


@pytest.mark.parametrize("approver", ["", "  ", None])
def test_published_with_empty_approver_raises(approver):
    approval = {**GOOD_APPROVAL, "approved_by": approver}

    with pytest.raises(TransitionError):
        transition(make(State.REVIEW_REQUIRED), State.PUBLISHED, actor="a", approval=approval)


@pytest.mark.parametrize("approved_at", ["yesterday", "", None, 123])
def test_published_with_bad_timestamp_raises(approved_at):
    approval = {**GOOD_APPROVAL, "approved_at": approved_at}

    with pytest.raises(TransitionError):
        transition(make(State.REVIEW_REQUIRED), State.PUBLISHED, actor="a", approval=approval)


def test_published_records_approval():
    result = transition(
        make(State.REVIEW_REQUIRED), State.PUBLISHED, actor="a", approval=GOOD_APPROVAL, now=NOW
    )

    assert result["approval"] == GOOD_APPROVAL
    assert result["approval"] is not GOOD_APPROVAL


def test_inputs_are_not_mutated():
    record = make(State.REVIEW_REQUIRED)
    approval = copy.deepcopy(GOOD_APPROVAL)
    record_before, approval_before = copy.deepcopy(record), copy.deepcopy(approval)

    result = transition(record, State.PUBLISHED, actor="a", approval=approval, now=NOW)

    assert record == record_before
    assert approval == approval_before
    assert result is not record
    result["approval"]["gates"]["G1"] = "x"
    assert approval == approval_before


def test_history_is_appended_in_order():
    first = transition(make(State.DRAFT), State.RESEARCHED, actor="a", note="n1", now=NOW)

    second = transition(first, State.TEXT_VERIFIED, actor="b", note="n2", now=NOW)

    assert second["history"][0] == {
        "from": "DRAFT", "to": "RESEARCHED", "actor": "a", "note": "n1", "at": NOW,
    }
    assert second["history"][1]["to"] == "TEXT_VERIFIED"
    assert len(first["history"]) == 1


def test_default_now_is_utc_iso8601():
    result = transition(make(State.DRAFT), State.BLOCKED, actor="a")

    assert result["history"][0]["at"].endswith("+00:00")


def test_invalid_record_state_raises():
    with pytest.raises(TransitionError):
        transition({"state": "NOPE", "history": []}, State.DRAFT, actor="a")
