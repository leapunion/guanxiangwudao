"""Tests for gxwd.renderer."""

from __future__ import annotations

import copy
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from gxwd.domain import load_hexagrams
from gxwd.renderer import render_hexagram_file, render_hexagram_svg

SVG_NS = "{http://www.w3.org/2000/svg}"
JIAREN = ["yang", "yang", "yin", "yang", "yin", "yang"]
ALL_YANG = ["yang"] * 6
ALL_YIN = ["yin"] * 6


def _rects(svg: str) -> list[ET.Element]:
    return list(ET.fromstring(svg).iter(f"{SVG_NS}rect"))


def _read_back(svg: str) -> list[str]:
    """Return line types top to bottom, read via data-position 6..1."""
    by_position: dict[int, set[str]] = {}
    for rect in _rects(svg):
        by_position.setdefault(int(rect.get("data-position")), set()).add(
            rect.get("data-line-type")
        )
    assert all(len(types) == 1 for types in by_position.values())
    return [next(iter(by_position[p])) for p in range(6, 0, -1)]


def _read_back_geometry(svg: str) -> list[str]:
    """Return line types top to bottom from rect geometry only (no data-* attrs)."""
    groups: dict[float, list[tuple[float, float]]] = {}
    for rect in _rects(svg):
        groups.setdefault(float(rect.get("y")), []).append(
            (float(rect.get("x")), float(rect.get("width")))
        )
    ordered = [groups[y] for y in sorted(groups)]  # smallest y first = top
    assert len(ordered) == 6

    yang_widths = [segs[0][1] for segs in ordered if len(segs) == 1]
    result: list[str] = []
    for segs in ordered:
        assert len(segs) in (1, 2)
        if len(segs) == 1:
            result.append("yang")
            continue
        (x1, w1), (x2, w2) = sorted(segs)
        assert x2 > x1 + w1, "yin segments must have a gap between them"
        for yang_width in yang_widths:
            assert w1 + w2 < yang_width, "yin total width must be < yang width"
        result.append("yin")
    return result


def _count(svg: str, position: int) -> int:
    return sum(1 for r in _rects(svg) if r.get("data-position") == str(position))


@pytest.mark.parametrize("lines", [ALL_YANG, ALL_YIN, JIAREN])
def test_round_trips_line_types_by_position(lines: list[str]) -> None:
    svg = render_hexagram_svg(lines)

    assert _read_back(svg) == lines


@pytest.mark.parametrize(
    "hexagram",
    load_hexagrams(),
    ids=lambda h: f"{h['hexagram_id']:02d}-{h['slug']}",
)
def test_geometry_read_back_matches_lines_for_all_64(hexagram: dict) -> None:
    svg = render_hexagram_svg(hexagram["lines_top_to_bottom"])

    assert _read_back_geometry(svg) == hexagram["lines_top_to_bottom"]


def test_all_64_hexagrams_loaded() -> None:
    assert len(load_hexagrams()) == 64


def test_jiaren_matches_binary_101011() -> None:
    svg = render_hexagram_svg(JIAREN)

    bottom_to_top = "".join("1" if t == "yang" else "0" for t in reversed(_read_back(svg)))
    assert bottom_to_top == "101011"


def test_yin_has_two_rects_and_yang_has_one() -> None:
    svg = render_hexagram_svg(JIAREN)

    for index, line_type in enumerate(JIAREN):
        expected = 1 if line_type == "yang" else 2
        assert _count(svg, 6 - index) == expected


def test_root_attributes() -> None:
    root = ET.fromstring(render_hexagram_svg(ALL_YANG, size=100))

    assert root.tag == f"{SVG_NS}svg"
    assert root.get("role") == "img"
    assert root.get("viewBox")


def test_output_is_deterministic() -> None:
    first = render_hexagram_svg(JIAREN, title="x")
    second = render_hexagram_svg(list(JIAREN), title="x")

    assert first == second


def test_title_is_escaped() -> None:
    svg = render_hexagram_svg(JIAREN, title="<a&b>")

    root = ET.fromstring(svg)
    assert "<a&b>" not in svg
    assert root.find(f"{SVG_NS}title").text == "<a&b>"


def test_no_title_element_when_title_missing() -> None:
    root = ET.fromstring(render_hexagram_svg(JIAREN))

    assert root.find(f"{SVG_NS}title") is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"lines_top_to_bottom": ["yang"] * 5},
        {"lines_top_to_bottom": ["yang"] * 5 + ["yan"]},
        {"lines_top_to_bottom": JIAREN, "color": "red;x"},
        {"lines_top_to_bottom": JIAREN, "color": "#12"},
        {"lines_top_to_bottom": JIAREN, "size": 0},
        {"lines_top_to_bottom": JIAREN, "size": -3},
    ],
)
def test_invalid_input_raises_value_error(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        render_hexagram_svg(**kwargs)


@pytest.mark.parametrize("color", ["#abc", "#A1B2C3"])
def test_valid_colors_accepted(color: str) -> None:
    assert color in render_hexagram_svg(JIAREN, color=color)


def _jiaren_dict() -> dict:
    return {
        "hexagram_id": 37,
        "name": "家人",
        "slug": "jiaren",
        "symbol": "䷤",
        "lines_top_to_bottom": list(JIAREN),
    }


def test_render_file_writes_named_utf8_file(tmp_path: Path) -> None:
    out_dir = tmp_path / "nested" / "svg"

    path = render_hexagram_file(_jiaren_dict(), out_dir)

    assert path == out_dir / "37-jiaren.svg"
    content = path.read_text(encoding="utf-8")
    assert "第37卦 家人 ䷤" in content
    assert _read_back(content) == JIAREN


def test_render_file_does_not_mutate_input(tmp_path: Path) -> None:
    hexagram = _jiaren_dict()
    snapshot = copy.deepcopy(hexagram)

    render_hexagram_file(hexagram, tmp_path)

    assert hexagram == snapshot


def test_render_file_pads_single_digit_id(tmp_path: Path) -> None:
    hexagram = {**_jiaren_dict(), "hexagram_id": 1, "slug": "qian"}

    path = render_hexagram_file(hexagram, tmp_path)

    assert path.name == "01-qian.svg"
