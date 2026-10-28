"""三层合成器：主图 + 程序生成卦符 + 文字层。

Layer 1：无字国画主图（本轮用占位 PNG）。
Layer 2：卦符 SVG，从 binary_bottom_to_top 推导（审定 R7），不信任入参的 lines。
Layer 3：文字层，只填已核验（verified）字段；pending 字段显示 PENDING_TEXT。

所有函数返回新对象，不修改入参。
"""
from __future__ import annotations

import copy
import hashlib
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from gxwd import domain, renderer

PENDING_TEXT = "（待底本校勘）"
PENDING_SOURCE_ID = "SOURCE_PENDING"
VERSION = "0.1.0"

_TEMPLATE_PATH = Path(__file__).resolve().parents[2] / "templates" / "card" / "text-layer.tmpl.svg"
_MASTER_SLOT = "master.png"
_HEX_SLOT = "hexagram.svg"
_TEXT_SLOT = "text.svg"
_CARD_SLOT = "card.svg"

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


class CompositionError(ValueError):
    """合成失败：final 时还有 pending 文本、模板缺失、master 缺失等。"""


@dataclass(frozen=True)
class CardArtifact:
    hexagram_id: int
    layers: dict
    hashes: dict
    text_source_versions: dict
    final: bool
    version: str
    created_at: str
    pending_slots: tuple = field(default_factory=tuple)


_SLOT_TYPES = {
    "gua_ci": "gua_ci",
    "tuan": "tuan",
    "da_xiang": "da_xiang",
}


def _slot_name_for_entry(entry: dict) -> str | None:
    text_type = entry.get("text_type")
    position = entry.get("line_position")
    if position is None:
        position = entry.get("position")
    if text_type in _SLOT_TYPES:
        return _SLOT_TYPES[text_type]
    if text_type == "yao_ci" and isinstance(position, int) and 1 <= position <= 6:
        return f"yao_ci_{position}"
    if text_type == "xiao_xiang" and isinstance(position, int) and 1 <= position <= 6:
        return f"xiao_xiang_{position}"
    return None


def _is_verified(entry: dict) -> bool:
    text = entry.get("original_text")
    return (
        entry.get("verification_status") == "verified"
        and isinstance(text, str)
        and text.strip() != ""
    )


def _text_slots(
    hexagram: dict,
    canonical_texts: list[dict] | None,
) -> tuple[dict[str, str], dict[str, str], tuple[str, ...]]:
    all_slots = ["gua_ci", "tuan", "da_xiang"]
    all_slots += [f"yao_ci_{i}" for i in range(1, 7)]
    all_slots += [f"xiao_xiang_{i}" for i in range(1, 7)]

    display = {slot: PENDING_TEXT for slot in all_slots}
    sources = {slot: PENDING_SOURCE_ID for slot in all_slots}

    for raw in canonical_texts or []:
        entry = copy.deepcopy(raw)
        slot = _slot_name_for_entry(entry)
        if slot is None or slot not in display:
            continue
        if _is_verified(entry):
            display[slot] = entry["original_text"]
            sources[slot] = entry.get("source_id") or PENDING_SOURCE_ID
    pending = tuple(slot for slot, src in sources.items() if src == PENDING_SOURCE_ID)
    return display, sources, pending


def _load_template() -> str:
    if not _TEMPLATE_PATH.exists():
        raise CompositionError(f"text-layer template missing: {_TEMPLATE_PATH}")
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


def _render_text_layer(hexagram: dict, display: dict[str, str]) -> str:
    tokens = {
        "hexagram_name": hexagram.get("name", ""),
        "full_name": hexagram.get("full_name", ""),
        **display,
    }

    def repl(match: re.Match) -> str:
        name = match.group(1)
        value = tokens.get(name)
        if value is None:
            return match.group(0)
        return escape(value)

    return _PLACEHOLDER_RE.sub(repl, _load_template())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _render_card_svg(hexagram: dict, created_at: str) -> str:
    title = f"第{hexagram['hexagram_id']}卦 {hexagram.get('name', '')} 图卡"
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        'viewBox="0 0 1200 800" width="1200" height="800" role="img">'
        f"<title>{escape(title)}</title>"
        '<desc>Guanxiang Wudao three-layer card; '
        f'generated_at={escape(created_at)}; version={VERSION}</desc>'
        f'<image xlink:href="{_MASTER_SLOT}" x="0" y="0" width="600" height="800"/>'
        f'<image xlink:href="{_HEX_SLOT}" x="600" y="80" width="240" height="240"/>'
        f'<image xlink:href="{_TEXT_SLOT}" x="600" y="0" width="600" height="800"/>'
        "</svg>"
    )


def compose_card(
    *,
    hexagram: dict,
    master_png: Path,
    canonical_texts: list[dict] | None,
    art_style: dict,
    out_dir: Path,
    final: bool = False,
    now: str | None = None,
) -> CardArtifact:
    hexagram = copy.deepcopy(hexagram)
    canonical_texts_copy = copy.deepcopy(canonical_texts) if canonical_texts else None
    _ = copy.deepcopy(art_style)

    hexagram_id = hexagram["hexagram_id"]
    binary = hexagram.get("binary_bottom_to_top")
    if not isinstance(binary, str):
        raise CompositionError("hexagram.binary_bottom_to_top missing")

    master_png = Path(master_png)
    if not master_png.exists():
        raise CompositionError(f"master image missing: {master_png}")

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    created_at = now if now is not None else _utc_now_iso()

    lines = domain.lines_from_binary(binary)
    hex_svg = renderer.render_hexagram_svg(
        lines,
        title=f"第{hexagram_id}卦 {hexagram.get('name', '')} {hexagram.get('symbol', '')}",
    )
    hex_path = out_dir / _HEX_SLOT
    _write_text(hex_path, hex_svg)

    display, sources, pending_slots = _text_slots(hexagram, canonical_texts_copy)
    if final and pending_slots:
        raise CompositionError(
            f"final composition requires all texts verified; pending: {pending_slots}"
        )
    text_svg = _render_text_layer(hexagram, display)
    text_path = out_dir / _TEXT_SLOT
    _write_text(text_path, text_svg)

    master_dst = out_dir / _MASTER_SLOT
    shutil.copyfile(master_png, master_dst)

    card_path = out_dir / _CARD_SLOT
    _write_text(card_path, _render_card_svg(hexagram, created_at))

    layers = {
        "master": master_dst,
        "hexagram": hex_path,
        "text": text_path,
        "composed": card_path,
    }
    hashes = {name: _sha256(path) for name, path in layers.items()}

    return CardArtifact(
        hexagram_id=hexagram_id,
        layers=layers,
        hashes=hashes,
        text_source_versions=sources,
        final=final,
        version=VERSION,
        created_at=created_at,
        pending_slots=pending_slots,
    )
