"""单卦状态机：合法迁移表与 transition()（PRD 第 23 篇）。"""

from __future__ import annotations

import copy
import re
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

_SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")

VALID_REVISION_SCOPES: frozenset[str] = frozenset({"text", "art", "layout"})


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
        _S.REVISION_REQUIRED: frozenset({_S.DRAFT, _S.RESEARCHED, _S.TEXT_VERIFIED}),
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


def _bump_patch(version: str) -> str:
    """将语义版本 patch 位加 1；无法解析时追加 '.1'。"""
    m = _SEMVER_RE.match(version or "")
    if not m:
        return (version or "0.1.0") + ".1"
    major, minor, patch = m.group(1), m.group(2), m.group(3)
    return f"{major}.{minor}.{int(patch) + 1}"


def transition(
    record: dict,
    to: State,
    *,
    actor: str,
    note: str = "",
    approval: dict | None = None,
    now: str | None = None,
    revision_scope: str | None = None,
) -> dict:
    """返回迁移后的新记录；不修改入参。

    revision_scope:
        必须为 None | "text" | "art" | "layout"。
        迁入 REVISION_REQUIRED 时必须提供；其他迁移时必须为 None。
        从 REVISION_REQUIRED 回到 TEXT_VERIFIED 仅当 revision_scope ∈ {"art", "layout"} 时合法。
    """
    if not isinstance(actor, str) or not actor.strip():
        raise TransitionError("actor 不能为空")

    # 校验 revision_scope 取值
    if revision_scope is not None and revision_scope not in VALID_REVISION_SCOPES:
        raise TransitionError(
            f"revision_scope 只能为 None、'text'、'art'、'layout'，得到: {revision_scope!r}"
        )

    current = _current_state(record)

    # 解析目标状态（非法枚举值抛 TransitionError）
    try:
        target = State(to)
    except ValueError as exc:
        raise TransitionError(f"非法目标状态: {to!r}") from exc

    # 检查迁移表合法性
    if target not in TRANSITIONS[current]:
        raise TransitionError(f"非法迁移: {current} -> {target}")

    # revision_scope 规则
    if target is State.REVISION_REQUIRED:
        if revision_scope is None:
            raise TransitionError("迁入 REVISION_REQUIRED 时必须提供 revision_scope")
    else:
        if revision_scope is not None:
            raise TransitionError(f"迁入 {target} 时 revision_scope 必须为 None")

    # REVISION_REQUIRED -> TEXT_VERIFIED 仅当 scope 为 art 或 layout
    if current is State.REVISION_REQUIRED and target is State.TEXT_VERIFIED:
        scope = record.get("revision_scope")
        if scope not in ("art", "layout"):
            raise TransitionError(
                "从 REVISION_REQUIRED 回到 TEXT_VERIFIED 仅当 revision_scope ∈ {art, layout}"
            )

    # PUBLISHED 门禁
    if target is State.PUBLISHED:
        check_approval(approval)

    result = copy.deepcopy(record)
    at = now if now is not None else datetime.now(UTC).isoformat()
    entry: dict[str, Any] = {
        "from": current.value,
        "to": target.value,
        "actor": actor,
        "note": note,
        "at": at,
    }
    if revision_scope is not None:
        entry["revision_scope"] = revision_scope
    # 迁入 PUBLISHED 时把 approval 也写入 history 条目，便于历史重放
    if target is State.PUBLISHED and approval is not None:
        entry["approval"] = copy.deepcopy(approval)
    result.setdefault("history", []).append(entry)
    result["state"] = target.value

    # 迁入 REVISION_REQUIRED 时把 scope 存入顶层，便于后续回退判断
    if target is State.REVISION_REQUIRED:
        result["revision_scope"] = revision_scope
    elif "revision_scope" in result and target not in (
        State.REVISION_REQUIRED,
    ):
        # 离开 REVISION_REQUIRED 时清除顶层 scope
        del result["revision_scope"]

    if target is State.PUBLISHED:
        result["approval"] = copy.deepcopy(approval)
        # release_version 由 publisher 传入 approval 并在此提升到顶层
        if approval and approval.get("release_version"):
            result["release_version"] = approval["release_version"]

    return result


def archive_approval(record: dict) -> dict:
    """当记录从 PUBLISHED 迁出（进入 REVISION_REQUIRED）时调用。

    将当前 approval 和 release_version 归档到 history 最后一条，
    然后清空顶层 approval 和 release_version，并递增 patch 版本号。
    返回新 dict，不修改入参。
    """
    result = copy.deepcopy(record)
    history = result.get("history", [])
    if history:
        last = history[-1]
        last["approval"] = copy.deepcopy(result.get("approval"))
        last["release_version"] = result.get("release_version")
    result["approval"] = None
    result["release_version"] = None
    result["version"] = _bump_patch(result.get("version", "0.1.0"))
    return result
