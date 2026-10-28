from __future__ import annotations

import copy
from itertools import product

import pytest

from gxwd.yao import build_yao_records, yao_name

QIAN = {"hexagram_id": 1, "binary_bottom_to_top": "111111"}
KUN = {"hexagram_id": 2, "binary_bottom_to_top": "000000"}
JIAREN = {"hexagram_id": 37, "binary_bottom_to_top": "101011"}


def _by_id(records: list[dict]) -> dict[int, dict]:
    return {r["hexagram_id"]: r for r in records}


@pytest.mark.parametrize(
    ("position", "line_type", "expected"),
    [(1, "yang", "初九"), (1, "yin", "初六"), (2, "yang", "九二"),
     (2, "yin", "六二"), (5, "yang", "九五"), (6, "yang", "上九"), (6, "yin", "上六")],
)
def test_yao_name_returns_expected_name(position: int, line_type: str, expected: str) -> None:
    assert yao_name(position, line_type) == expected


@pytest.mark.parametrize(("position", "line_type"), [(0, "yang"), (7, "yin"), (1, "x"), (True, "yang")])
def test_yao_name_raises_on_invalid_arguments(position: int, line_type: str) -> None:
    with pytest.raises(ValueError):
        yao_name(position, line_type)


def test_jiaren_lines_derive_from_binary_bottom_to_top() -> None:
    records = build_yao_records([JIAREN])

    lines = records[0]["lines"]

    assert (lines[0]["position"], lines[0]["line_name"], lines[0]["line_type"]) == (1, "初九", "yang")
    assert (lines[1]["position"], lines[1]["line_name"], lines[1]["line_type"]) == (2, "六二", "yin")
    assert (lines[5]["position"], lines[5]["line_name"]) == (6, "上九")


def test_pending_fields_are_placeholders() -> None:
    line = build_yao_records([JIAREN])[0]["lines"][0]

    assert line["original_text"] is None
    assert line["source_id"] == "SOURCE_PENDING"
    assert line["verification_status"] == "pending"
    assert line["variant_readings"] == []


def test_extra_lines_only_for_qian_and_kun() -> None:
    records = _by_id(build_yao_records([QIAN, KUN, JIAREN]))

    assert records[1]["extra_lines"] == [
        {"name": "用九", "original_text": None, "source_id": "SOURCE_PENDING", "verification_status": "pending"}
    ]
    assert records[2]["extra_lines"][0]["name"] == "用六"
    assert records[37]["extra_lines"] == []


def test_input_is_not_mutated() -> None:
    hexagrams = [copy.deepcopy(QIAN), copy.deepcopy(KUN), copy.deepcopy(JIAREN)]
    snapshot = copy.deepcopy(hexagrams)

    build_yao_records(hexagrams)

    assert hexagrams == snapshot


def test_all_64_binaries_yield_384_lines_excluding_extra_lines() -> None:
    hexagrams = [
        {"hexagram_id": i + 1, "binary_bottom_to_top": "".join(bits)}
        for i, bits in enumerate(product("01", repeat=6))
    ]

    records = build_yao_records(hexagrams)

    assert len(records) == 64
    assert sum(len(r["lines"]) for r in records) == 384
    assert sum(len(r["extra_lines"]) for r in records) == 2
