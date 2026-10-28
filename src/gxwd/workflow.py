"""单卦状态机：合法迁移表与 transition()（PRD 第 23 篇）。"""

from __future__ import annotations

import copy
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping


class State(StrEnum):
    DRAFT = "DRAFT"
    RESEARCHED = "RESEARCHED"
    TEXT_VERIFIED = "TEXT_VERIFIED"
    ART_DRAFT = "ART_DRAFT"
    ART_APPROVED = "ART_APPROVED"
    LAYOUT_READY = "LAYOUT_READY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    PUBLISHED = "PUBLISHED"
    BLOCKED = "BLOCKED"
    REJECTED = "REJECTED"
    REVISION_REQUIRED = "REVISION_REQUIRED"


class TransitionError(ValueError):
    """非法迁移、缺少操作者或缺少有效批准。"""


_S = State
TRANSITIONS: Mapping[State, frozenset[State]] = MappingProxyType(
    {
        _S.DRAFT: frozenset({_S.RESEARCHED, _S.BLOCKED}),
        _S.RESEARCHED: frozenset({_S.TEXT_VERIFIED, _S.REVISION_REQUIRED, _S.BLOCKED}),
        _S.TEXT_VERIFIED: frozenset({_S.ART_DRAFT, _S.REVISION_REQUIRED, _S.BLOCKED}),
        _S.ART_DRAFT: frozenset({_S.ART_APPROVED, _S.REVISION_REQUIRED, _S.REJECTED}),
        _S.ART_APPROVED: frozenset({_S.LAYOUT_READY, _S.REVISION_REQUIRED}),
        _S.LAYOUT_READY: frozenset({_S.REVIEW_REQUIRED, _S.REVISION_REQUIRED}),
        _S.REVIEW_REQUIRED: frozenset(
            {_S.PUBLISHED, _S.REJECTED, _S.REVISION_REQUIRED}
        ),
        _S.PUBLISHED: frozenset({_S.REVISION_REQUIRED}),
        _S.BLOCKED: frozenset({_S.DRAFT, _S.RESEARCHED}),
        _S.REVISION_REQUIRED: frozenset({_S.DRAFT, _S.RESEARCHED}),
        _S.REJECTED: frozenset({_S.DRAFT}),
    }
)

REQUIRED_GATES = ("G1", "G2", "G3")


def _is_iso8601(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def check_approval(approval: Mapping[str, Any] | None) -> None:
    """校验发布批准；不通过则抛 TransitionError。"""
    if not approval:
        raise TransitionError("迁移到 PUBLISHED 必须提供 approval")
    approver = approval.get("approved_by")
    if not isinstance(approver, str) or not approver.strip():
        raise TransitionError("approval.approved_by 不能为空")
    if not _is_iso8601(approval.get("approved_at")):
        raise TransitionError("approval.approved_at 必须是 ISO8601 时间")
    gates = approval.get("gates")
    if not isinstance(gates, Mapping):
        raise TransitionError("approval.gates 缺失")
    failed = [g for g in REQUIRED_GATES if gates.get(g) != "passed"]
    if failed:
        raise TransitionError(f"门禁未通过: {', '.join(failed)}")


def _current_state(record: Mapping[str, Any]) -> State:
    try:
        return State(record.get("state"))
    except ValueError as exc:
        raise TransitionError(f"记录状态无效: {record.get('state')!r}") from exc


def transition(
    record: dict,
    to: State,
    *,
    actor: str,
    note: str = "",
    approval: dict | None = None,
    now: str | None = None,
) -> dict:
    """返回迁移后的新记录；不修改入参。"""
    if not isinstance(actor, str) or not actor.strip():
        raise TransitionError("actor 不能为空")
    current = _current_state(record)
    target = State(to)
    if target not in TRANSITIONS[current]:
        raise TransitionError(f"非法迁移: {current} -> {target}")
    if target is State.PUBLISHED:
        check_approval(approval)

    result = copy.deepcopy(record)
    at = now if now is not None else datetime.now(UTC).isoformat()
    result.setdefault("history", []).append(
        {"from": current.value, "to": target.value, "actor": actor, "note": note, "at": at}
    )
    result["state"] = target.value
    if target is State.PUBLISHED:
        result["approval"] = copy.deepcopy(approval)
    return result
