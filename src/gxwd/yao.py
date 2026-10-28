"""384 爻记录生成（纯标准库，不修改入参）。"""

from __future__ import annotations

from typing import Any

YANG = "yang"
YIN = "yin"
SOURCE_PENDING = "SOURCE_PENDING"
LINE_COUNT = 6

_POSITION_DIGITS = {2: "二", 3: "三", 4: "四", 5: "五"}
_EXTRA_LINE_NAMES = {1: "用九", 2: "用六"}


def yao_name(position: int, line_type: str) -> str:
    """返回爻名，如 初九、六二、上六。"""
    if isinstance(position, bool) or not isinstance(position, int) or not 1 <= position <= LINE_COUNT:
        raise ValueError(f"position must be an int in 1..6, got {position!r}")
    if line_type not in (YANG, YIN):
        raise ValueError(f"line_type must be 'yang' or 'yin', got {line_type!r}")
    digit = "九" if line_type == YANG else "六"
    if position == 1:
        return f"初{digit}"
    if position == LINE_COUNT:
        return f"上{digit}"
    return f"{digit}{_POSITION_DIGITS[position]}" if line_type == YANG else f"六{_POSITION_DIGITS[position]}"


def _pending_extra(name: str) -> dict[str, Any]:
    return {
        "name": name,
        "original_text": None,
        "source_id": SOURCE_PENDING,
        "verification_status": "pending",
    }


def _build_line(position: int, bit: str) -> dict[str, Any]:
    line_type = YANG if bit == "1" else YIN
    return {
        "position": position,
        "line_type": line_type,
        "line_name": yao_name(position, line_type),
        "original_text": None,
        "source_id": SOURCE_PENDING,
        "edition": None,
        "page": None,
        "variant_readings": [],
        "interpretation": None,
        "historical_story_id": None,
        "verification_status": "pending",
    }


def build_yao_records(hexagrams: list[dict]) -> list[dict]:
    """由卦的 binary_bottom_to_top 推导每卦 6 爻记录。"""
    records: list[dict] = []
    for hexagram in hexagrams:
        binary = hexagram["binary_bottom_to_top"]
        if len(binary) != LINE_COUNT or set(binary) - {"0", "1"}:
            raise ValueError(f"invalid binary_bottom_to_top: {binary!r}")
        hexagram_id = hexagram["hexagram_id"]
        extra_name = _EXTRA_LINE_NAMES.get(hexagram_id)
        records.append(
            {
                "hexagram_id": hexagram_id,
                "lines": [_build_line(i + 1, bit) for i, bit in enumerate(binary)],
                "extra_lines": [_pending_extra(extra_name)] if extra_name else [],
            }
        )
    return records
