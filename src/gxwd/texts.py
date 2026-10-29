"""经文数据契约与录入校验 — V5-WP1.

功能：
- make_text_id：生成规范 text_id 字符串
- load_canonical_texts：从 canonical-texts.json 载入条目列表
- import_canonical_from_csv：从人工录入 CSV 导入并校验经文条目
- validate_canonical_texts：对条目列表做完整性校验，返回错误列表

红线：此模块不包含任何卦辞、爻辞或《彖传》《象传》原文。
"""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

PENDING_SOURCE_ID: str = "SOURCE_PENDING"
PENDING_TEXT: str = "（待底本校勘）"
TEXT_TYPES: tuple[str, ...] = (
    "gua_ci",
    "yao_ci",
    "yong",
    "tuan",
    "da_xiang",
    "xiao_xiang",
)

# text_type 中允许 line_position 为整数 1..6 的类型
_POSITIONAL_INT_TYPES: frozenset[str] = frozenset({"yao_ci", "xiao_xiang"})
# text_type 中 line_position 必须为 null 的类型
_NULL_POSITION_TYPES: frozenset[str] = frozenset({"gua_ci", "tuan", "da_xiang"})
# text_type 中 line_position 必须为 "用九"/"用六" 的类型
_YONG_TYPES: frozenset[str] = frozenset({"yong"})
_YONG_POSITIONS: frozenset[str] = frozenset({"用九", "用六"})

# text_type 中每卦最多一条的类型（唯一条目）
_UNIQUE_PER_HEXAGRAM: frozenset[str] = frozenset({"gua_ci", "tuan", "da_xiang"})


# ---------------------------------------------------------------------------
# 异常
# ---------------------------------------------------------------------------


class CanonicalTextError(ValueError):
    """经文录入或来源校验错误。"""


# ---------------------------------------------------------------------------
# text_id 生成
# ---------------------------------------------------------------------------


def make_text_id(
    hexagram_id: int,
    text_type: str,
    line_position: int | str | None,
) -> str:
    """生成规范 text_id 字符串。

    Args:
        hexagram_id: 卦序，1..64。
        text_type: 文字类型，必须在 TEXT_TYPES 中。
        line_position: 爻位或 "用九"/"用六"，无爻位时为 None。

    Returns:
        格式 ``H<id:02d>-<text_type>[-L<line_position>]``。
        对于 yong 类型，后缀为 ``-<line_position>``（如 ``-用九``）。
        对于带整数爻位的类型，后缀为 ``-L<line_position>``。

    Raises:
        CanonicalTextError: text_type 不合法，或参数组合无效。
    """
    if text_type not in TEXT_TYPES:
        raise CanonicalTextError(f"无效 text_type: {text_type!r}，合法值为 {TEXT_TYPES}")
    if hexagram_id < 1 or hexagram_id > 64:
        raise CanonicalTextError(f"hexagram_id 超出范围 1..64: {hexagram_id}")

    prefix = f"H{hexagram_id:02d}-{text_type}"

    if text_type in _NULL_POSITION_TYPES:
        return prefix

    if text_type in _YONG_TYPES:
        if line_position not in _YONG_POSITIONS:
            raise CanonicalTextError(
                f"yong 类型的 line_position 必须是 '用九' 或 '用六'，得到: {line_position!r}"
            )
        return f"{prefix}-{line_position}"

    if text_type in _POSITIONAL_INT_TYPES:
        if line_position is None:
            # xiao_xiang 允许 null（整体象传无爻位）
            if text_type == "xiao_xiang":
                return prefix
            raise CanonicalTextError(
                f"{text_type} 类型的 line_position 不能为 None"
            )
        if not isinstance(line_position, int) or line_position < 1 or line_position > 6:
            raise CanonicalTextError(
                f"{text_type} 类型的 line_position 必须是整数 1..6，得到: {line_position!r}"
            )
        return f"{prefix}-L{line_position}"

    return prefix  # 兜底（正常不会到达）


# ---------------------------------------------------------------------------
# 载入
# ---------------------------------------------------------------------------

_DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _resolve_data_dir(data_dir: Path | None) -> Path:
    env_dir = __import__("os").environ.get("GXWD_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    if data_dir is not None:
        return data_dir
    return _DEFAULT_DATA_DIR


def load_canonical_texts(data_dir: Path | None = None) -> list[dict]:
    """从 data/canonical-texts.json 载入条目列表。

    文件不存在时返回空列表（而不是报错），因为 V0.5 批次 A
    尚未执行人工录入步骤 H2。

    Returns:
        条目列表（list[dict]），文件缺失时为 []。
    """
    resolved = _resolve_data_dir(data_dir)
    path = resolved / "canonical-texts.json"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    return list(data.get("entries", []))


# ---------------------------------------------------------------------------
# CSV 导入
# ---------------------------------------------------------------------------

# CSV 列头（顺序固定，工具读取时按列名索引）
_CSV_COLUMNS = (
    "text_type",
    "line_position",
    "line_name",
    "original_text",
    "source_id",
    "edition",
    "page",
    "variant_readings_json",
    "verification_status",
)


def _parse_line_position(raw: str, text_type: str) -> int | str | None:
    """将 CSV 中的 line_position 字段解析为适当类型。"""
    if raw == "":
        return None
    if text_type in _YONG_TYPES:
        if raw not in _YONG_POSITIONS:
            raise CanonicalTextError(
                f"yong 类型的 line_position 必须是 '用九' 或 '用六'，得到: {raw!r}"
            )
        return raw
    try:
        val = int(raw)
    except ValueError:
        raise CanonicalTextError(
            f"line_position 无法解析为整数: {raw!r}"
        )
    return val


def _validate_line_position_consistency(
    text_type: str, line_position: int | str | None
) -> None:
    """校验 line_position 与 text_type 的对应关系。"""
    if text_type in _NULL_POSITION_TYPES:
        if line_position is not None:
            raise CanonicalTextError(
                f"{text_type} 类型不允许 line_position，但得到: {line_position!r}"
            )
    elif text_type in _YONG_TYPES:
        if line_position not in _YONG_POSITIONS:
            raise CanonicalTextError(
                f"yong 类型的 line_position 必须是 '用九'/'用六'，得到: {line_position!r}"
            )
    elif text_type == "yao_ci":
        if not isinstance(line_position, int) or line_position < 1 or line_position > 6:
            raise CanonicalTextError(
                f"yao_ci 类型的 line_position 必须是整数 1..6，得到: {line_position!r}"
            )
    elif text_type == "xiao_xiang":
        if line_position is not None:
            if not isinstance(line_position, int) or line_position < 1 or line_position > 6:
                raise CanonicalTextError(
                    f"xiao_xiang 类型的 line_position 若不为 null，必须是整数 1..6，"
                    f"得到: {line_position!r}"
                )


def import_canonical_from_csv(
    csv_path: Path,
    sources: list[dict],
    hexagram_id: int,
) -> list[dict]:
    """从人工录入 CSV 导入并校验单卦经文条目。

    Args:
        csv_path: CSV 文件路径，第一行为列头。
        sources: data/sources.json 中的 sources 列表（每项需有 id、status 字段）。
        hexagram_id: 所属卦序，1..64。

    Returns:
        新的 list[dict]，每项含 text_id 字段；不修改入参。

    Raises:
        CanonicalTextError: 任何校验失败时。
    """
    # 深拷贝入参，确保不修改原始对象
    sources_copy: list[dict] = copy.deepcopy(sources)

    # 建立 source_id → status 的映射
    source_map: dict[str, str] = {
        s["source_id"]: s.get("status", "") for s in sources_copy
    }

    if hexagram_id < 1 or hexagram_id > 64:
        raise CanonicalTextError(f"hexagram_id 超出范围 1..64: {hexagram_id}")

    with csv_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        rows: list[dict[str, str]] = list(reader)

    # 唯一类型计数器：gua_ci / tuan / da_xiang 每卦最多各一条
    unique_counts: dict[str, int] = {t: 0 for t in _UNIQUE_PER_HEXAGRAM}
    # yao_ci 爻位去重
    yao_positions: set[int] = set()

    entries: list[dict] = []

    for row_idx, row in enumerate(rows, start=2):  # 行号从 2 起（1 是列头）
        ctx = f"第 {row_idx} 行"

        # text_type 校验
        text_type = row.get("text_type", "").strip()
        if text_type not in TEXT_TYPES:
            raise CanonicalTextError(
                f"{ctx}: 无效 text_type {text_type!r}，合法值为 {TEXT_TYPES}"
            )

        # line_position 解析与校验
        raw_lp = row.get("line_position", "").strip()
        line_position = _parse_line_position(raw_lp, text_type)
        _validate_line_position_consistency(text_type, line_position)

        # source_id 校验
        source_id = row.get("source_id", "").strip()
        if not source_id:
            raise CanonicalTextError(f"{ctx}: source_id 不能为空")
        if source_id != PENDING_SOURCE_ID:
            if source_id not in source_map:
                raise CanonicalTextError(
                    f"{ctx}: source_id {source_id!r} 未在 sources 中登记"
                )
            if source_map[source_id] != "selected":
                raise CanonicalTextError(
                    f"{ctx}: source_id {source_id!r} 的 status 不是 'selected'"
                    f"（当前为 {source_map[source_id]!r}）"
                )

        # original_text 非 null 时，edition 和 page 必须非空
        original_text_raw = row.get("original_text", "").strip()
        original_text: str | None = original_text_raw if original_text_raw else None

        edition_raw = row.get("edition", "").strip()
        page_raw = row.get("page", "").strip()

        if original_text is not None:
            if not edition_raw:
                raise CanonicalTextError(
                    f"{ctx}: original_text 非空时 edition 不得为空"
                )
            if not page_raw:
                raise CanonicalTextError(
                    f"{ctx}: original_text 非空时 page 不得为空"
                )

        edition: str | None = edition_raw if edition_raw else None
        # page 尝试转为整数，否则保留字符串
        page: int | str | None
        if page_raw:
            try:
                page = int(page_raw)
            except ValueError:
                page = page_raw
        else:
            page = None

        # variant_readings 解析
        vr_raw = row.get("variant_readings_json", "").strip()
        if vr_raw:
            try:
                variant_readings: list[dict] = json.loads(vr_raw)
            except json.JSONDecodeError as exc:
                raise CanonicalTextError(
                    f"{ctx}: variant_readings_json 解析失败: {exc}"
                ) from exc
        else:
            variant_readings = []

        # verification_status
        verification_status = row.get("verification_status", "pending").strip()
        if verification_status not in ("pending", "verified", "rejected"):
            raise CanonicalTextError(
                f"{ctx}: 无效 verification_status {verification_status!r}"
            )

        # line_name
        line_name_raw = row.get("line_name", "").strip()
        line_name: str | None = line_name_raw if line_name_raw else None

        # 唯一约束
        if text_type in _UNIQUE_PER_HEXAGRAM:
            unique_counts[text_type] += 1
            if unique_counts[text_type] > 1:
                raise CanonicalTextError(
                    f"{ctx}: {text_type} 类型每卦最多一条，已出现重复"
                )

        # yao_ci 爻位去重
        if text_type == "yao_ci":
            assert isinstance(line_position, int)
            if line_position in yao_positions:
                raise CanonicalTextError(
                    f"{ctx}: yao_ci 爻位 {line_position} 重复"
                )
            yao_positions.add(line_position)

        # 生成 text_id
        text_id = make_text_id(hexagram_id, text_type, line_position)

        entries.append(
            {
                "text_id": text_id,
                "hexagram_id": hexagram_id,
                "text_type": text_type,
                "line_position": line_position,
                "line_name": line_name,
                "original_text": original_text,
                "source_id": source_id,
                "edition": edition,
                "page": page,
                "variant_readings": variant_readings,
                "verification_status": verification_status,
            }
        )

    return entries


# ---------------------------------------------------------------------------
# 整体校验
# ---------------------------------------------------------------------------


def validate_canonical_texts(
    entries: list[dict],
    hexagrams: list[dict],
) -> list[dict[str, Any]]:
    """对条目列表做完整性校验。

    Args:
        entries: TextEntry 字典列表（通常来自 load_canonical_texts 或 import_canonical_from_csv）。
        hexagrams: hexagrams.json 中的 64 卦记录列表（用于检查 hexagram_id 合法性）。

    Returns:
        错误列表，每项为 ``{"text_id": str, "rule": str, "detail": str}``。
        无错误时返回空列表。不修改入参。
    """
    valid_ids: set[int] = {h["hexagram_id"] for h in hexagrams}
    errors: list[dict[str, Any]] = []

    # 按 hexagram_id 分组
    groups: dict[int, list[dict]] = {}
    for entry in entries:
        hid = entry.get("hexagram_id")
        if not isinstance(hid, int) or hid < 1 or hid > 64:
            errors.append(
                {
                    "text_id": entry.get("text_id", "<unknown>"),
                    "rule": "hexagram_id_range",
                    "detail": f"hexagram_id {hid!r} 不在 1..64 范围内",
                }
            )
            continue
        if hid not in valid_ids:
            errors.append(
                {
                    "text_id": entry.get("text_id", "<unknown>"),
                    "rule": "hexagram_id_unknown",
                    "detail": f"hexagram_id {hid} 在 hexagrams 数据中不存在",
                }
            )
        groups.setdefault(hid, []).append(entry)

    for hid, group in groups.items():
        # ---- yao_ci 爻位完整性 ----
        yao_positions = [
            e["line_position"]
            for e in group
            if e.get("text_type") == "yao_ci"
        ]
        if yao_positions:
            present = set(yao_positions)
            if len(present) != len(yao_positions):
                errors.append(
                    {
                        "text_id": f"H{hid:02d}-yao_ci",
                        "rule": "yao_ci_duplicate_position",
                        "detail": f"第 {hid} 卦 yao_ci 爻位有重复: {yao_positions}",
                    }
                )
            missing = set(range(1, 7)) - present
            if missing:
                errors.append(
                    {
                        "text_id": f"H{hid:02d}-yao_ci",
                        "rule": "yao_ci_incomplete",
                        "detail": f"第 {hid} 卦 yao_ci 缺少爻位: {sorted(missing)}",
                    }
                )

        # ---- 唯一类型重复检查 ----
        for utype in _UNIQUE_PER_HEXAGRAM:
            count = sum(1 for e in group if e.get("text_type") == utype)
            if count > 1:
                errors.append(
                    {
                        "text_id": f"H{hid:02d}-{utype}",
                        "rule": f"{utype}_duplicate",
                        "detail": f"第 {hid} 卦 {utype} 条目重复（共 {count} 条）",
                    }
                )

        # ---- original_text 非 null 时的 if/then 规则 ----
        for entry in group:
            if entry.get("original_text") is not None:
                sid = entry.get("source_id", "")
                if sid == PENDING_SOURCE_ID:
                    errors.append(
                        {
                            "text_id": entry.get("text_id", "<unknown>"),
                            "rule": "original_text_requires_real_source",
                            "detail": "original_text 非 null 时 source_id 不能是 SOURCE_PENDING",
                        }
                    )
                if not entry.get("edition"):
                    errors.append(
                        {
                            "text_id": entry.get("text_id", "<unknown>"),
                            "rule": "original_text_requires_edition",
                            "detail": "original_text 非 null 时 edition 不能为空",
                        }
                    )
                if entry.get("page") is None:
                    errors.append(
                        {
                            "text_id": entry.get("text_id", "<unknown>"),
                            "rule": "original_text_requires_page",
                            "detail": "original_text 非 null 时 page 不能为 null",
                        }
                    )
                if entry.get("verification_status") != "verified":
                    errors.append(
                        {
                            "text_id": entry.get("text_id", "<unknown>"),
                            "rule": "original_text_requires_verified",
                            "detail": "original_text 非 null 时 verification_status 必须是 verified",
                        }
                    )

        # ---- variant_readings 去重 ----
        for entry in group:
            variants = entry.get("variant_readings", [])
            seen: set[tuple[str, str]] = set()
            for vr in variants:
                key = (vr.get("text", ""), vr.get("source_id", ""))
                if key in seen:
                    errors.append(
                        {
                            "text_id": entry.get("text_id", "<unknown>"),
                            "rule": "variant_readings_duplicate",
                            "detail": f"variant_readings 中 (text, source_id) 组合重复: {key}",
                        }
                    )
                    break
                seen.add(key)

    return errors
