"""Tests for gxwd.composer (three-layer card composition)."""
from __future__ import annotations

import base64
import copy
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from gxwd import composer, domain

# A valid 1x1 PNG (89 bytes) used as placeholder master image.
_MINIMAL_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
    "nGP8z8DwHwAFAAH/VscvDQAAAABJRU5ErkJggg=="
)
_SVG_NS = "{http://www.w3.org/2000/svg}"
_PLACEHOLDER_TEXT = composer.PENDING_TEXT


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture
def master_png(tmp_path: Path) -> Path:
    path = tmp_path / "master.png"
    path.write_bytes(base64.b64decode(_MINIMAL_PNG_B64))
    return path


@pytest.fixture
def jiaren() -> dict:
    return domain.get_hexagram(37)


@pytest.fixture
def art_style() -> dict:
    return {
        "palette": ["#273F52", "#547A83", "#A2B4A1", "#B58C69", "#A74439"],
        "paper": "宣纸肌理",
        "composition": "三远法",
    }


# --------------------------------------------------------------------------- #
# Geometry read-back (per audit R6)
# --------------------------------------------------------------------------- #

def _read_hexagram_geometry(svg_text: str) -> list[str]:
    """Parse hexagram.svg by geometry (no data-* attrs): group rects by y, assume
    yang = 1 rect, yin = 2 rects. Return lines top-to-bottom."""
    root = ET.fromstring(svg_text)
    rects = root.findall(f".//{_SVG_NS}rect")
    groups: dict[int, list] = {}
    for rect in rects:
        y = int(rect.attrib["y"])
        groups.setdefault(y, []).append(rect)
    ordered = [groups[y] for y in sorted(groups)]
    assert len(ordered) == 6, f"expected 6 rows, got {len(ordered)}"
    lines: list[str] = []
    for row in ordered:
        if len(row) == 1:
            lines.append("yang")
        elif len(row) == 2:
            xs = sorted(int(r.attrib["x"]) for r in row)
            widths = sorted(int(r.attrib["width"]) for r in row)
            assert xs[1] > xs[0] + widths[0], "yin row rects must have a gap"
            lines.append("yin")
        else:
            raise AssertionError(f"unexpected rect count per row: {len(row)}")
    return lines


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

class TestComposeCardStructure:
    """compose_card produces all four layers with hashes."""

    def test_all_layers_written(self, tmp_path, jiaren, master_png, art_style):
        out_dir = tmp_path / "card"

        artifact = composer.compose_card(
            hexagram=jiaren,
            master_png=master_png,
            canonical_texts=None,
            art_style=art_style,
            out_dir=out_dir,
            now="2026-10-28T12:00:00Z",
        )

        assert artifact.hexagram_id == 37
        assert set(artifact.layers.keys()) == {"master", "hexagram", "text", "composed"}
        for name, path in artifact.layers.items():
            assert path.exists(), f"{name} not written to {path}"
        assert set(artifact.hashes.keys()) == set(artifact.layers.keys())
        for h in artifact.hashes.values():
            assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)


class TestHexagramGeometry:
    """Hexagram layer is derived from binary (R7) and reads back correctly (R6)."""

    def test_jiaren_geometry_matches_binary(
        self, tmp_path, jiaren, master_png, art_style
    ):
        out_dir = tmp_path / "card"

        artifact = composer.compose_card(
            hexagram=jiaren,
            master_png=master_png,
            canonical_texts=None,
            art_style=art_style,
            out_dir=out_dir,
            now="2026-10-28T12:00:00Z",
        )

        svg = artifact.layers["hexagram"].read_text(encoding="utf-8")
        read_back = _read_hexagram_geometry(svg)
        # 家人卦 binary 101011 → lines top-to-bottom per domain.lines_from_binary
        expected = domain.lines_from_binary("101011")
        assert read_back == expected
        assert read_back == ["yang", "yang", "yin", "yang", "yin", "yang"]

    def test_hexagram_derived_from_binary_not_lines_field(
        self, tmp_path, jiaren, master_png, art_style
    ):
        """Even if hexagram.lines_top_to_bottom is forged, composer uses binary."""
        tampered = copy.deepcopy(jiaren)
        tampered["lines_top_to_bottom"] = ["yin"] * 6  # inconsistent with binary
        out_dir = tmp_path / "card"

        artifact = composer.compose_card(
            hexagram=tampered,
            master_png=master_png,
            canonical_texts=None,
            art_style={"foo": "bar"},
            out_dir=out_dir,
            now="2026-10-28T12:00:00Z",
        )

        svg = artifact.layers["hexagram"].read_text(encoding="utf-8")
        read_back = _read_hexagram_geometry(svg)
        assert read_back == ["yang", "yang", "yin", "yang", "yin", "yang"]


class TestPendingTexts:
    """When canonical_texts missing or pending, placeholder appears in text.svg."""

    def test_none_canonical_texts_show_placeholder(
        self, tmp_path, jiaren, master_png, art_style
    ):
        out_dir = tmp_path / "card"

        artifact = composer.compose_card(
            hexagram=jiaren,
            master_png=master_png,
            canonical_texts=None,
            art_style=art_style,
            out_dir=out_dir,
            now="2026-10-28T12:00:00Z",
        )

        text_svg = artifact.layers["text"].read_text(encoding="utf-8")
        assert _PLACEHOLDER_TEXT in text_svg
        assert all(
            src == composer.PENDING_SOURCE_ID
            for src in artifact.text_source_versions.values()
        )
        # All 15 slots pending.
        assert len(artifact.pending_slots) == 15

    def test_verified_gua_ci_appears_other_slots_pending(
        self, tmp_path, jiaren, master_png, art_style
    ):
        out_dir = tmp_path / "card"
        canonical = [
            {
                "text_type": "gua_ci",
                "line_position": None,
                "original_text": "〔测试文本甲〕",
                "source_id": "TEST-SOURCE-001",
                "edition": "测试版本甲",
                "page": "p.1",
                "verification_status": "verified",
                "variant_readings": [],
            },
        ]

        artifact = composer.compose_card(
            hexagram=jiaren,
            master_png=master_png,
            canonical_texts=canonical,
            art_style=art_style,
            out_dir=out_dir,
            now="2026-10-28T12:00:00Z",
        )

        text_svg = artifact.layers["text"].read_text(encoding="utf-8")
        assert "〔测试文本甲〕" in text_svg
        assert _PLACEHOLDER_TEXT in text_svg  # other slots still pending
        assert artifact.text_source_versions["gua_ci"] == "TEST-SOURCE-001"
        assert artifact.text_source_versions["tuan"] == composer.PENDING_SOURCE_ID
        assert "gua_ci" not in artifact.pending_slots
        assert "tuan" in artifact.pending_slots


class TestFinalRequiresAllVerified:
    """final=True rejects any pending slot; accepts fully verified set."""

    def test_final_with_pending_raises(
        self, tmp_path, jiaren, master_png, art_style
    ):
        out_dir = tmp_path / "card"

        with pytest.raises(composer.CompositionError):
            composer.compose_card(
                hexagram=jiaren,
                master_png=master_png,
                canonical_texts=None,
                art_style=art_style,
                out_dir=out_dir,
                final=True,
            )

    def test_final_with_all_verified_succeeds(
        self, tmp_path, jiaren, master_png, art_style
    ):
        out_dir = tmp_path / "card"

        placeholders = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        canonical: list[dict] = []
        for slot_type in ("gua_ci", "tuan", "da_xiang"):
            canonical.append({
                "text_type": slot_type,
                "line_position": None,
                "original_text": f"〔测试文本{slot_type}〕",
                "source_id": f"TEST-{slot_type.upper()}",
                "edition": "测试版本甲",
                "page": "p.1",
                "verification_status": "verified",
                "variant_readings": [],
            })
        for i in range(1, 7):
            canonical.append({
                "text_type": "yao_ci",
                "line_position": i,
                "original_text": f"〔yao{i}·{placeholders[i-1]}〕",
                "source_id": f"TEST-YAO-{i}",
                "edition": "测试版本甲",
                "page": "p.1",
                "verification_status": "verified",
                "variant_readings": [],
            })
            canonical.append({
                "text_type": "xiao_xiang",
                "line_position": i,
                "original_text": f"〔xx{i}·{placeholders[i-1]}〕",
                "source_id": f"TEST-XX-{i}",
                "edition": "测试版本甲",
                "page": "p.1",
                "verification_status": "verified",
                "variant_readings": [],
            })

        artifact = composer.compose_card(
            hexagram=jiaren,
            master_png=master_png,
            canonical_texts=canonical,
            art_style=art_style,
            out_dir=out_dir,
            final=True,
            now="2026-10-28T12:00:00Z",
        )

        assert artifact.final is True
        assert artifact.pending_slots == ()
        text_svg = artifact.layers["text"].read_text(encoding="utf-8")
        assert _PLACEHOLDER_TEXT not in text_svg


class TestImmutability:
    """Inputs must not be mutated by compose_card."""

    def test_inputs_not_mutated(
        self, tmp_path, jiaren, master_png, art_style
    ):
        canonical = [
            {
                "text_type": "gua_ci",
                "line_position": None,
                "original_text": "〔测试文本甲〕",
                "source_id": "TEST-SOURCE-001",
                "edition": "测试版本甲",
                "page": "p.1",
                "verification_status": "verified",
                "variant_readings": [],
            }
        ]
        snapshot_hex = copy.deepcopy(jiaren)
        snapshot_canonical = copy.deepcopy(canonical)
        snapshot_style = copy.deepcopy(art_style)

        composer.compose_card(
            hexagram=jiaren,
            master_png=master_png,
            canonical_texts=canonical,
            art_style=art_style,
            out_dir=tmp_path / "card",
            now="2026-10-28T12:00:00Z",
        )

        assert jiaren == snapshot_hex
        assert canonical == snapshot_canonical
        assert art_style == snapshot_style


class TestDeterminism:
    """Fixed inputs produce byte-identical output."""

    def test_same_inputs_same_card_svg(
        self, tmp_path, jiaren, master_png, art_style
    ):
        out_a = tmp_path / "a"
        out_b = tmp_path / "b"
        kwargs = dict(
            hexagram=jiaren,
            master_png=master_png,
            canonical_texts=None,
            art_style=art_style,
            now="2026-10-28T12:00:00Z",
        )

        artifact_a = composer.compose_card(out_dir=out_a, **kwargs)
        artifact_b = composer.compose_card(out_dir=out_b, **kwargs)

        assert artifact_a.layers["composed"].read_bytes() == artifact_b.layers["composed"].read_bytes()
        assert artifact_a.hashes == artifact_b.hashes


class TestMasterMissing:
    """Missing master image raises CompositionError."""

    def test_missing_master_raises(
        self, tmp_path, jiaren, art_style
    ):
        with pytest.raises(composer.CompositionError):
            composer.compose_card(
                hexagram=jiaren,
                master_png=tmp_path / "nope.png",
                canonical_texts=None,
                art_style=art_style,
                out_dir=tmp_path / "card",
            )
