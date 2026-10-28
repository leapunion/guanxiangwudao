"""作品登记册：构建、汇总、读写 asset-catalog.json。"""

from __future__ import annotations

import json
from pathlib import Path

from gxwd.workflow import TRANSITIONS, State, TransitionError, check_approval, transition


def build_catalog(hexagrams: list[dict]) -> dict:
    """为每个卦生成初始 DRAFT 记录，按 hexagram_id 排序。"""
    records = [
        {
            "hexagram_id": h["hexagram_id"],
            "name": h["name"],
            "slug": h["slug"],
            "state": State.DRAFT.value,
            "version": "0.1.0",
            "history": [],
        }
        for h in sorted(hexagrams, key=lambda h: h["hexagram_id"])
    ]
    return {"version": "1", "records": records}


def summarize(catalog: dict) -> dict[str, int]:
    """按状态计数；11 个状态全部列出。非法状态的记录不计入任何计数。"""
    counts = {state.value: 0 for state in State}
    for record in catalog["records"]:
        state = record["state"]
        if state in counts:
            counts[state] += 1
        # 非法状态静默跳过（不计入，不抛出）
    return counts


def load_catalog(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_catalog(catalog: dict, path: Path) -> None:
    text = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def _err(hexagram_id: object, rule: str, detail: str) -> dict:
    return {"hexagram_id": hexagram_id, "rule": rule, "detail": detail}


def _parse_state(value: object) -> State | None:
    try:
        return State(value)
    except ValueError:
        return None


def _check_history(hid: object, history: list) -> list[dict]:
    errors: list[dict] = []
    for i, step in enumerate(history):
        src = _parse_state(step.get("from")) if isinstance(step, dict) else None
        dst = _parse_state(step.get("to")) if isinstance(step, dict) else None
        if src is None or dst is None or dst not in TRANSITIONS[src]:
            errors.append(_err(hid, "history_transition", f"第 {i + 1} 步迁移非法: {step!r}"))
    return errors


def _check_published(hid: object, record: dict) -> list[dict]:
    errors: list[dict] = []
    try:
        check_approval(record.get("approval"))
    except TransitionError as exc:
        errors.append(_err(hid, "published_approval", str(exc)))
    history = record.get("history")
    last = history[-1] if isinstance(history, list) and history else None
    if not isinstance(last, dict) or (last.get("from"), last.get("to")) != (
        State.REVIEW_REQUIRED.value,
        State.PUBLISHED.value,
    ):
        errors.append(
            _err(hid, "published_history", "PUBLISHED 记录的最后一步必须是 REVIEW_REQUIRED -> PUBLISHED")
        )
    return errors


def _check_revision_scope_required(hid: object, history: list) -> list[dict]:
    """history 中迁入 REVISION_REQUIRED 的每一步必须附 revision_scope。"""
    errors: list[dict] = []
    for i, step in enumerate(history):
        if not isinstance(step, dict):
            continue
        if step.get("to") == State.REVISION_REQUIRED.value:
            if not step.get("revision_scope"):
                errors.append(
                    _err(
                        hid,
                        "revision_scope_required",
                        f"第 {i + 1} 步迁入 REVISION_REQUIRED 但缺少 revision_scope: {step!r}",
                    )
                )
    return errors


def _check_history_replay(hid: object, history: list) -> list[dict]:
    """从 DRAFT 起逐步重放 history，任何一步失败记录错误。"""
    errors: list[dict] = []
    # 构造一个最小 record 从 DRAFT 开始
    current_record: dict = {
        "hexagram_id": hid,
        "state": State.DRAFT.value,
        "history": [],
    }
    for i, step in enumerate(history):
        if not isinstance(step, dict):
            errors.append(_err(hid, "history_replay", f"step {i + 1}: 步骤不是 dict"))
            break
        to_val = step.get("to")
        actor = step.get("actor") or "replay"
        note = step.get("note", "")
        approval = step.get("approval")
        revision_scope = step.get("revision_scope")
        now = step.get("at")
        try:
            current_record = transition(
                current_record,
                to_val,  # type: ignore[arg-type]
                actor=actor,
                note=note or "",
                approval=approval,
                now=now,
                revision_scope=revision_scope,
            )
        except (TransitionError, ValueError) as exc:
            errors.append(_err(hid, "history_replay", f"step {i + 1}: {exc}"))
            break
    return errors


def validate_catalog(catalog: dict) -> list[dict]:
    """校验登记册一致性，返回错误列表（不抛异常，不修改入参）。"""
    errors: list[dict] = []
    for record in catalog.get("records", []):
        hid = record.get("hexagram_id")
        state = _parse_state(record.get("state"))
        if state is None:
            errors.append(_err(hid, "state", f"状态无效: {record.get('state')!r}"))
            continue
        history = record.get("history")
        if not isinstance(history, list):
            errors.append(_err(hid, "history", "history 必须是列表"))
            continue
        errors.extend(_check_history(hid, history))
        errors.extend(_check_revision_scope_required(hid, history))
        errors.extend(_check_history_replay(hid, history))
        if state is State.PUBLISHED:
            errors.extend(_check_published(hid, record))
    return errors
