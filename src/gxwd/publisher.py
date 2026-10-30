"""出版门禁：request_publication 重算全部硬性检查后迁移到 PUBLISHED。

职责：
  1. 载入 hexagrams/trigrams，运行 validate_all。
  2. 载入 canonical-texts，检查指定卦的经文全部已核验。
  3. 检查 reviews/ 中 g1/g2/g3/interpretation-review.json 存在且 result=="pass"。
  4. 核对 approved_by 在 approvers.json 名单中，且不与生产者重复。
  5. 组装 approval dict，调用 workflow.transition 返回新 record。
不写回文件——写回由主会话或 CLI 层负责。
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from gxwd.catalog import load_catalog
from gxwd.domain import load_hexagrams, load_trigrams
from gxwd.validator import validate_all
from gxwd.workflow import State, TransitionError, transition

# 必须核验的 text_type（乾、坤额外要求 yong）
_REQUIRED_TYPES_COMMON: frozenset[str] = frozenset({"gua_ci", "tuan", "da_xiang"})
_REQUIRED_YAO_COUNT = 6  # 普通卦 6 条 yao_ci
_QIAN_KUN_IDS = frozenset({1, 2})  # 乾坤额外需要 yong

_CATALOG_FILENAME = "asset-catalog.json"
_RELEASE_VERSION_RE = re.compile(r"^v(\d+)$")


class PublicationError(ValueError):
    """出版门禁检查失败。"""


def hash_file(path: Path) -> str:
    """返回文件内容的 sha256 十六进制摘要。"""
    digest = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return digest


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _default_data_dir() -> Path:
    import os

    override = os.environ.get("GXWD_DATA_DIR")
    return Path(override) if override else _repo_root() / "data"


def _next_release_version(record: dict) -> str:
    """从 history 中推算下一个 release_version（v1, v2, …）。"""
    count = sum(
        1
        for step in record.get("history", [])
        if step.get("to") == State.PUBLISHED.value
    )
    return f"v{count + 1}"


def _check_canonical_texts(
    texts_data: dict,
    hexagram_id: int,
) -> None:
    """校验指定卦的经文全部已核验且覆盖必要类型。

    抛 PublicationError 说明失败原因。
    """
    entries = [
        e for e in texts_data.get("entries", []) if e.get("hexagram_id") == hexagram_id
    ]

    # 检查有无 pending
    pending = [e for e in entries if e.get("verification_status") != "verified"]
    if pending:
        raise PublicationError(
            f"第 {hexagram_id} 卦有 {len(pending)} 条经文未核验（verification_status != 'verified'）"
        )

    # 检查必要类型覆盖
    types_present: set[str] = {e["text_type"] for e in entries}
    missing_common = _REQUIRED_TYPES_COMMON - types_present
    if missing_common:
        raise PublicationError(
            f"第 {hexagram_id} 卦缺少经文类型: {', '.join(sorted(missing_common))}"
        )

    # 检查 yao_ci 数量
    yao_entries = [e for e in entries if e.get("text_type") == "yao_ci"]
    if len(yao_entries) < _REQUIRED_YAO_COUNT:
        raise PublicationError(
            f"第 {hexagram_id} 卦 yao_ci 不足 {_REQUIRED_YAO_COUNT} 条，只有 {len(yao_entries)} 条"
        )

    # 乾坤额外 yong
    if hexagram_id in _QIAN_KUN_IDS:
        yong_entries = [e for e in entries if e.get("text_type") == "yong"]
        if not yong_entries:
            raise PublicationError(f"第 {hexagram_id} 卦（乾/坤）缺少 yong 条目")


def _load_review_file(path: Path, hexagram_id: int, label: str) -> dict:
    """载入并基本校验审查报告文件。"""
    if not path.exists():
        raise PublicationError(f"审查报告 {label} 缺失: {path}")
    try:
        data = _load_json(path)
    except (json.JSONDecodeError, OSError) as exc:
        raise PublicationError(f"审查报告 {label} 无法解析: {exc}") from exc
    if not isinstance(data, dict):
        raise PublicationError(f"审查报告 {label} 格式错误：顶层不是对象")
    if data.get("result") != "pass":
        raise PublicationError(
            f"审查报告 {label} result={data.get('result')!r}，必须为 'pass'"
        )
    if data.get("hexagram_id") != hexagram_id:
        raise PublicationError(
            f"审查报告 {label} hexagram_id={data.get('hexagram_id')!r}，"
            f"与参数 {hexagram_id} 不符"
        )
    return data


def _find_review(reviews_dir: Path, prefix: str, hexagram_id: int, label: str) -> Path:
    """在 reviews_dir 中找到以 prefix 开头的文件（取第一个匹配）。"""
    matches = sorted(reviews_dir.glob(f"{prefix}*.json"))
    if not matches:
        raise PublicationError(
            f"reviews/ 目录中缺少 {label} 报告（前缀 '{prefix}'）: {reviews_dir}"
        )
    return matches[0]


def request_publication(
    hexagram_id: int,
    *,
    approved_by: str,
    approved_at: str,
    data_dir: Path | None = None,
    reviews_dir: Path | None = None,
    approvers_path: Path | None = None,
) -> dict:
    """重算全部门禁后迁移到 PUBLISHED，返回新 record（不写文件）。

    Args:
        hexagram_id: 卦序号（1–64）。
        approved_by: 批准人 ID，必须在 approvers.json 中。
        approved_at: ISO8601 时间字符串。
        data_dir: 数据目录，默认 <repo>/data。
        reviews_dir: 审查报告目录，默认 <repo>/projects/<id:02d>-<slug>/reviews。
        approvers_path: 审批人名单路径，默认 <repo>/data/approvers.json。

    Raises:
        PublicationError: 任何一项检查失败。
        TransitionError: workflow.transition 拒绝（状态前置条件不满足）。
    """
    effective_data_dir = data_dir if data_dir is not None else _default_data_dir()

    # ── 步骤 1：卦象主数据校验 ────────────────────────────────────────────
    hexagrams = load_hexagrams(effective_data_dir)
    trigrams = load_trigrams(effective_data_dir)
    result = validate_all(hexagrams, trigrams)
    if not result["valid"]:
        raise PublicationError(
            f"validate_all 失败，{len(result['errors'])} 个错误: "
            + "; ".join(e.get("detail", "") for e in result["errors"][:3])
        )

    # 找到目标卦信息（用于后续默认路径）
    target_hexagram = next(
        (h for h in hexagrams if h["hexagram_id"] == hexagram_id), None
    )
    if target_hexagram is None:
        raise PublicationError(f"hexagram_id={hexagram_id} 不存在于 hexagrams.json")

    # ── 步骤 2：经文完整性校验 ───────────────────────────────────────────
    try:
        import gxwd.texts as _texts_mod  # noqa: F401
        texts_path = effective_data_dir / "canonical-texts.json"
        if not texts_path.exists():
            raise PublicationError("canonical-texts.json 缺失")
        texts_data = _load_json(texts_path)
    except ImportError:
        # texts 模块不存在时仍要求文件在场
        texts_path = effective_data_dir / "canonical-texts.json"
        if not texts_path.exists():
            raise PublicationError("canonical-texts.json 缺失")
        texts_data = _load_json(texts_path)

    canonical_text_hash = hash_file(texts_path)
    _check_canonical_texts(texts_data, hexagram_id)

    # ── 步骤 3：审查报告校验 ─────────────────────────────────────────────
    slug = target_hexagram.get("slug", f"{hexagram_id:02d}")
    if reviews_dir is None:
        reviews_dir = _repo_root() / "projects" / f"{hexagram_id:02d}-{slug}" / "reviews"

    g1_path = _find_review(reviews_dir, "g1-", hexagram_id, "G1")
    g2_path = _find_review(reviews_dir, "g2-", hexagram_id, "G2")
    g3_path = _find_review(reviews_dir, "g3-", hexagram_id, "G3")
    interp_path = reviews_dir / "interpretation-review.json"

    _load_review_file(g1_path, hexagram_id, "g1")
    _load_review_file(g2_path, hexagram_id, "g2")
    _load_review_file(g3_path, hexagram_id, "g3")
    _load_review_file(interp_path, hexagram_id, "interpretation-review")

    review_hashes = {
        "g1": hash_file(g1_path),
        "g2": hash_file(g2_path),
        "g3": hash_file(g3_path),
        "interpretation": hash_file(interp_path),
    }

    # ── 步骤 4：审批人身份核验 ──────────────────────────────────────────
    if approvers_path is None:
        approvers_path = effective_data_dir / "approvers.json"
    if not approvers_path.exists():
        raise PublicationError(f"approvers.json 缺失: {approvers_path}")
    approvers_data = _load_json(approvers_path)
    approver_ids: set[str] = {
        a["id"] for a in approvers_data.get("approvers", []) if isinstance(a, dict)
    }
    if approved_by not in approver_ids:
        raise PublicationError(
            f"approved_by={approved_by!r} 不在 approvers.json 名单中"
        )

    # ── 步骤 5：approved_by 不得与任何生产者相同 ────────────────────────
    catalog_path = effective_data_dir / _CATALOG_FILENAME
    if not catalog_path.exists():
        raise PublicationError(f"asset-catalog.json 缺失: {catalog_path}")
    catalog = load_catalog(catalog_path)

    record = next(
        (r for r in catalog.get("records", []) if r.get("hexagram_id") == hexagram_id),
        None,
    )
    if record is None:
        raise PublicationError(f"asset-catalog.json 中找不到 hexagram_id={hexagram_id}")

    # 收集审查报告中的 verifier（如有）
    all_reviews_data = []
    for rp in (g1_path, g2_path, g3_path, interp_path):
        try:
            all_reviews_data.append(_load_json(rp))
        except Exception:
            pass
    verifiers: set[str] = set()
    for rd in all_reviews_data:
        v = rd.get("verifier")
        if isinstance(v, str) and v:
            verifiers.add(v)

    # 收集 catalog history 中的 actor
    history_actors: set[str] = {
        step["actor"]
        for step in record.get("history", [])
        if isinstance(step, dict) and step.get("actor")
    }

    producers = verifiers | history_actors
    if approved_by in producers:
        raise PublicationError(
            f"approved_by={approved_by!r} 与生产者/验证者重复（{sorted(producers)}）"
        )

    # ── 步骤 6：组装 approval ────────────────────────────────────────────
    release_version = _next_release_version(record)
    # 治理 V2（见 docs/GOVERNANCE.md）：approver 可以是 Agent 身份；
    # Agent approver 在 approval 中带 signed_by_agent=true 的 provenance 标记。
    approver_entry = next(
        (a for a in approvers_data.get("approvers", [])
         if isinstance(a, dict) and a.get("id") == approved_by),
        {},
    )
    approver_notes = approver_entry.get("notes", "")
    signed_by_agent = (
        "autopilot" in approved_by.lower()
        or "agent" in approver_notes.lower()
        or "signed_by_agent=true" in approver_notes
    )
    approval: dict[str, Any] = {
        "approved_by": approved_by,
        "approved_at": approved_at,
        "gates": {"G1": "passed", "G2": "passed", "G3": "passed"},
        "interpretation_review": "passed",
        "review_hashes": review_hashes,
        "canonical_text_version": canonical_text_hash,
        "release_version": release_version,
        "signed_by_agent": signed_by_agent,
        "governance_version": "V2",
    }

    # ── 步骤 7：迁移状态 ─────────────────────────────────────────────────
    new_record = transition(
        record,
        State.PUBLISHED,
        actor=approved_by,
        approval=approval,
        now=approved_at,
    )
    return new_record
