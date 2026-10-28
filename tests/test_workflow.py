import copy

import pytest

from gxwd.workflow import (
    TRANSITIONS,
    State,
    TransitionError,
    archive_approval,
    transition,
)

NOW = "2026-01-01T00:00:00+00:00"
GOOD_APPROVAL = {
    "approved_by": "主编",
    "approved_at": "2026-01-02T10:00:00+08:00",
    "gates": {"G1": "passed", "G2": "passed", "G3": "passed"},
    "release_version": "v1",
}

# 按 IMPLEMENTATION_PLAN §6 手工硬编码的期望迁移表（不得从被测代码生成）。
# 注意：REVISION_REQUIRED 新增允许回到 TEXT_VERIFIED（A9）。
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
    "REVISION_REQUIRED": {"DRAFT", "RESEARCHED", "TEXT_VERIFIED"},
    "REJECTED": {"DRAFT"},
}
ALL_STATES = sorted(EXPECTED_TABLE)
ALL_PAIRS = [(s, t) for s in ALL_STATES for t in ALL_STATES]


def make(state: State, revision_scope: str | None = None) -> dict:
    base: dict = {"hexagram_id": 37, "state": state.value, "history": []}
    if revision_scope is not None:
        base["revision_scope"] = revision_scope
    return base


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
    # revision_scope rules:
    # - entering REVISION_REQUIRED needs a scope
    # - leaving REVISION_REQUIRED to TEXT_VERIFIED needs scope in {art, layout} on record
    revision_scope_arg = None
    if dst == "REVISION_REQUIRED":
        revision_scope_arg = "text"

    # Build record: if src is REVISION_REQUIRED, give it a scope that allows going to TEXT_VERIFIED
    if src == "REVISION_REQUIRED":
        record = make(State(src), revision_scope="art")
    else:
        record = make(State(src))

    approval = GOOD_APPROVAL if dst == "PUBLISHED" else None

    if dst in EXPECTED_TABLE[src]:
        result = transition(
            record,
            State(dst),
            actor="alice",
            approval=approval,
            now=NOW,
            revision_scope=revision_scope_arg,
        )
        assert result["state"] == dst
    else:
        with pytest.raises(TransitionError):
            transition(
                record,
                State(dst),
                actor="alice",
                approval=GOOD_APPROVAL,
                now=NOW,
                revision_scope=revision_scope_arg,
            )


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


# ── revision_scope 新增测试 ─────────────────────────────────────────────────


def test_entering_revision_required_without_scope_raises():
    """迁入 REVISION_REQUIRED 时不提供 revision_scope 应抛 TransitionError。"""
    with pytest.raises(TransitionError, match="revision_scope"):
        transition(make(State.RESEARCHED), State.REVISION_REQUIRED, actor="a")


@pytest.mark.parametrize("scope", ["text", "art", "layout"])
def test_entering_revision_required_with_valid_scope_succeeds(scope):
    """合法 scope 均可迁入 REVISION_REQUIRED。"""
    result = transition(
        make(State.RESEARCHED), State.REVISION_REQUIRED, actor="a", revision_scope=scope
    )

    assert result["state"] == "REVISION_REQUIRED"
    assert result["history"][-1]["revision_scope"] == scope
    assert result["revision_scope"] == scope


def test_revision_scope_stored_in_history_entry():
    """revision_scope 应写入 history 条目。"""
    result = transition(
        make(State.ART_DRAFT), State.REVISION_REQUIRED, actor="a", revision_scope="art"
    )

    assert result["history"][-1].get("revision_scope") == "art"


def test_invalid_revision_scope_raises():
    """非法 revision_scope 值应抛 TransitionError。"""
    with pytest.raises(TransitionError, match="revision_scope"):
        transition(
            make(State.RESEARCHED), State.REVISION_REQUIRED, actor="a", revision_scope="bogus"
        )


def test_revision_scope_must_be_none_for_non_revision_required():
    """迁入非 REVISION_REQUIRED 状态时提供 revision_scope 应抛 TransitionError。"""
    with pytest.raises(TransitionError):
        transition(
            make(State.DRAFT), State.RESEARCHED, actor="a", revision_scope="text"
        )


def test_revision_required_to_text_verified_allowed_when_art_scope():
    """REVISION_REQUIRED(art) -> TEXT_VERIFIED 合法。"""
    record = make(State.REVISION_REQUIRED, revision_scope="art")

    result = transition(record, State.TEXT_VERIFIED, actor="a")

    assert result["state"] == "TEXT_VERIFIED"


def test_revision_required_to_text_verified_allowed_when_layout_scope():
    """REVISION_REQUIRED(layout) -> TEXT_VERIFIED 合法。"""
    record = make(State.REVISION_REQUIRED, revision_scope="layout")

    result = transition(record, State.TEXT_VERIFIED, actor="a")

    assert result["state"] == "TEXT_VERIFIED"


def test_revision_required_to_text_verified_blocked_when_text_scope():
    """REVISION_REQUIRED(text) -> TEXT_VERIFIED 非法（文本返工须从 DRAFT/RESEARCHED 重走）。"""
    record = make(State.REVISION_REQUIRED, revision_scope="text")

    with pytest.raises(TransitionError):
        transition(record, State.TEXT_VERIFIED, actor="a")


def test_revision_required_to_text_verified_blocked_when_no_scope_on_record():
    """revision_scope 缺失时也应被拒绝。"""
    record = make(State.REVISION_REQUIRED)  # 没有 revision_scope 顶层字段

    with pytest.raises(TransitionError):
        transition(record, State.TEXT_VERIFIED, actor="a")


# ── archive_approval 测试 ──────────────────────────────────────────────────


def _make_published_record() -> dict:
    """构造一条合法的 PUBLISHED 记录（走完 REVIEW_REQUIRED -> PUBLISHED）。"""
    record = make(State.REVIEW_REQUIRED)
    return transition(record, State.PUBLISHED, actor="approver", approval=GOOD_APPROVAL, now=NOW)


def test_archive_approval_clears_top_level_approval():
    """archive_approval 后顶层 approval 应为 None。"""
    published = _make_published_record()

    archived = archive_approval(published)

    assert archived["approval"] is None


def test_archive_approval_clears_release_version():
    """archive_approval 后顶层 release_version 应为 None。"""
    published = _make_published_record()

    archived = archive_approval(published)

    assert archived.get("release_version") is None


def test_archive_approval_stores_approval_in_history():
    """archive_approval 后 history 最后一条应包含原 approval。"""
    published = _make_published_record()
    original_approval = copy.deepcopy(published.get("approval"))

    archived = archive_approval(published)

    last_history = archived["history"][-1]
    assert last_history["approval"] == original_approval


def test_archive_approval_bumps_patch_version():
    """archive_approval 应递增 patch 版本号。"""
    published = _make_published_record()
    published["version"] = "1.2.3"

    archived = archive_approval(published)

    assert archived["version"] == "1.2.4"


def test_archive_approval_does_not_mutate_input():
    """archive_approval 不修改入参。"""
    published = _make_published_record()
    original = copy.deepcopy(published)

    archive_approval(published)

    assert published == original


def test_archive_approval_returns_new_dict():
    """archive_approval 返回新对象。"""
    published = _make_published_record()

    archived = archive_approval(published)

    assert archived is not published


# ── 非法 to 值应抛 TransitionError（R10）────────────────────────────────────


def test_illegal_to_value_raises_transition_error_not_value_error():
    """非法 to 值应抛 TransitionError，而非 ValueError（R10）。"""
    with pytest.raises(TransitionError):
        transition(make(State.DRAFT), "NONEXISTENT_STATE", actor="a")  # type: ignore[arg-type]
