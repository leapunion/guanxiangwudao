"""SVG hexagram renderer. Pure functions, standard library only."""

from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

YANG = "yang"
YIN = "yin"
LINE_COUNT = 6

_COLOR_PATTERN = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})")

# Fixed logical canvas; `size` only scales width/height, keeping output exact.
_CANVAS = 120
_MARGIN = 4
_LINE_HEIGHT = 12
_LINE_GAP = 8
_YIN_GAP = 16
_BAR_WIDTH = _CANVAS - 2 * _MARGIN
_YIN_SEGMENT = (_BAR_WIDTH - _YIN_GAP) // 2


def _validate_lines(lines: list[str]) -> None:
    if not isinstance(lines, (list, tuple)) or len(lines) != LINE_COUNT:
        raise ValueError(f"lines_top_to_bottom must contain exactly {LINE_COUNT} items")
    for item in lines:
        if item not in (YANG, YIN):
            raise ValueError(f"invalid line type: {item!r}")


def _validate_color(color: str) -> None:
    if not isinstance(color, str) or not _COLOR_PATTERN.fullmatch(color):
        raise ValueError(f"color must be #RGB or #RRGGBB, got {color!r}")


def _validate_size(size: int) -> None:
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        raise ValueError(f"size must be a positive integer, got {size!r}")


def _rect(x: int, y: int, width: int, position: int, line_type: str) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{_LINE_HEIGHT}" '
        f'data-position="{position}" data-line-type="{line_type}"/>'
    )


def _line_rects(index: int, line_type: str) -> list[str]:
    y = _MARGIN + index * (_LINE_HEIGHT + _LINE_GAP)
    position = LINE_COUNT - index
    if line_type == YANG:
        return [_rect(_MARGIN, y, _BAR_WIDTH, position, YANG)]
    right_x = _MARGIN + _YIN_SEGMENT + _YIN_GAP
    return [
        _rect(_MARGIN, y, _YIN_SEGMENT, position, YIN),
        _rect(right_x, y, _YIN_SEGMENT, position, YIN),
    ]


def render_hexagram_svg(
    lines_top_to_bottom: list[str],
    *,
    size: int = 240,
    color: str = "#273F52",
    title: str | None = None,
) -> str:
    """Render six lines (top to bottom) as a deterministic SVG string."""
    _validate_lines(lines_top_to_bottom)
    _validate_color(color)
    _validate_size(size)

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {_CANVAS} {_CANVAS}" width="{size}" height="{size}" role="img">'
    ]
    if title is not None:
        parts.append(f"<title>{escape(title)}</title>")
    parts.append(f'<g fill="{color}">')
    for index, line_type in enumerate(lines_top_to_bottom):
        parts.extend(_line_rects(index, line_type))
    parts.append("</g></svg>")
    return "".join(parts)


def render_hexagram_file(hexagram: dict, out_dir: Path) -> Path:
    """Write `<id:02d>-<slug>.svg` into out_dir and return its path."""
    hexagram_id = hexagram["hexagram_id"]
    title = f"第{hexagram_id}卦 {hexagram['name']} {hexagram['symbol']}"
    svg = render_hexagram_svg(hexagram["lines_top_to_bottom"], title=title)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{hexagram_id:02d}-{hexagram['slug']}.svg"
    path.write_text(svg, encoding="utf-8")
    return path
