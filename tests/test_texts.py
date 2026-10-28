"""tests/test_texts.py — V5-WP1 经文数据契约与录入校验测试。

测试经文一律使用占位串，严禁出现任何真实卦辞或爻辞。
占位符集合：
  〔测试文本甲〕〔测试文本乙〕〔测试文本丙〕〔测试文本丁〕〔测试文本戊〕
"""

from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

# ---------------------------------------------------------------------------
# 被测模块
# ---------------------------------------------------------------------------
from gxwd.texts import (
    PENDING_SOURCE_ID,
    PENDING_TEXT,
    TEXT_TYPES,
    CanonicalTextError,
    import_canonical_from_csv,
    load_canonical_texts,
    make_text_id,
    validate_canonical_texts,
)

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

SCHEMA_PATH = (
    Path(__file__).parent.parent / "schemas" / "canonical-texts.schema.json"
)


def _load_schema() -> dict:
    with SCHEMA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _make_sources(source_id: str = "SRC-TEST-001", status: str = "selected") -> list[dict]:
    """构造合成 sources 列表，不读取仓库 data/sources.json。"""
    return [{"id": source_id, "status": status}]


def _write_csv(tmp_path: Path, name: str, rows: list[dict]) -> Path:
    """把字典列表写成 CSV，首行为列头。"""
    cols = [
        "text_type",
        "line_position",
        "line_name",
        "original_text",
        "source_id",
        "edition",
        "page",
        "variant_readings_json",
        "verification_status",
    ]
    p = tmp_path / name
    with p.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in cols})
    return p


def _pending_row(text_type: str, line_position: str = "", line_name: str = "") -> dict:
    return {
        "text_type": text_type,
        "line_position": line_position,
        "line_name": line_name,
        "original_text": "",
        "source_id": PENDING_SOURCE_ID,
        "edition": "",
        "page": "",
        "variant_readings_json": "",
        "verification_status": "pending",
    }


# ---------------------------------------------------------------------------
# Schema 自校验
# ---------------------------------------------------------------------------


class TestSchemaValidity:
    def test_schema_is_valid_draft2020(self):
        """用 Draft202012Validator.check_schema 校验 schema 本身。"""
        schema = _load_schema()
        Draft202012Validator.check_schema(schema)

    def test_schema_validates_pending_entry(self):
        """合法的 pending 条目通过 schema 校验。"""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        doc = {
            "version": "1",
            "entries": [
                {
                    "text_id": "H37-gua_ci",
                    "hexagram_id": 37,
                    "text_type": "gua_ci",
                    "line_position": None,
                    "line_name": None,
                    "original_text": None,
                    "source_id": "SOURCE_PENDING",
                    "edition": None,
                    "page": None,
                    "variant_readings": [],
                    "verification_status": "pending",
                }
            ],
        }
        errors = list(validator.iter_errors(doc))
        assert errors == [], [str(e) for e in errors]

    def test_schema_validates_yao_ci_entry(self):
        """带爻位的 yao_ci 条目通过 schema 校验。"""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        doc = {
            "version": "1",
            "entries": [
                {
                    "text_id": "H37-yao_ci-L3",
                    "hexagram_id": 37,
                    "text_type": "yao_ci",
                    "line_position": 3,
                    "line_name": "九三",
                    "original_text": None,
                    "source_id": "SOURCE_PENDING",
                    "edition": None,
                    "page": None,
                    "variant_readings": [],
                    "verification_status": "pending",
                }
            ],
        }
        errors = list(validator.iter_errors(doc))
        assert errors == [], [str(e) for e in errors]

    def test_schema_validates_yong_entry(self):
        """用九条目通过 schema 校验。"""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        doc = {
            "version": "1",
            "entries": [
                {
                    "text_id": "H01-yong-用九",
                    "hexagram_id": 1,
                    "text_type": "yong",
                    "line_position": "用九",
                    "line_name": None,
                    "original_text": None,
                    "source_id": "SOURCE_PENDING",
                    "edition": None,
                    "page": None,
                    "variant_readings": [],
                    "verification_status": "pending",
                }
            ],
        }
        errors = list(validator.iter_errors(doc))
        assert errors == [], [str(e) for e in errors]

    def test_schema_rejects_original_text_without_source(self):
        """original_text 非 null 但 source_id = SOURCE_PENDING 时 schema 应报错。"""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        doc = {
            "version": "1",
            "entries": [
                {
                    "text_id": "H37-gua_ci",
                    "hexagram_id": 37,
                    "text_type": "gua_ci",
                    "line_position": None,
                    "line_name": None,
                    "original_text": "〔测试文本甲〕",
                    "source_id": "SOURCE_PENDING",
                    "edition": None,
                    "page": None,
                    "variant_readings": [],
                    "verification_status": "pending",
                }
            ],
        }
        errors = list(validator.iter_errors(doc))
        assert errors, "应有 schema 错误但没有"

    def test_schema_rejects_original_text_without_edition(self):
        """original_text 非 null 但 edition 为 null 时 schema 应报错。"""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        doc = {
            "version": "1",
            "entries": [
                {
                    "text_id": "H37-gua_ci",
                    "hexagram_id": 37,
                    "text_type": "gua_ci",
                    "line_position": None,
                    "line_name": None,
                    "original_text": "〔测试文本乙〕",
                    "source_id": "SRC-REAL-001",
                    "edition": None,
                    "page": 1,
                    "variant_readings": [],
                    "verification_status": "verified",
                }
            ],
        }
        errors = list(validator.iter_errors(doc))
        assert errors, "应有 schema 错误但没有"

    def test_schema_accepts_verified_entry_with_full_fields(self):
        """original_text 非 null 且 source_id/edition/page/verification_status 全部合法时通过。"""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        doc = {
            "version": "1",
            "entries": [
                {
                    "text_id": "H37-gua_ci",
                    "hexagram_id": 37,
                    "text_type": "gua_ci",
                    "line_position": None,
                    "line_name": None,
                    "original_text": "〔测试文本丙〕",
                    "source_id": "SRC-REAL-001",
                    "edition": "测试版本甲",
                    "page": 42,
                    "variant_readings": [],
                    "verification_status": "verified",
                }
            ],
        }
        errors = list(validator.iter_errors(doc))
        assert errors == [], [str(e) for e in errors]

    def test_schema_rejects_invalid_text_type(self):
        """text_type 非法时 schema 报错。"""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        doc = {
            "version": "1",
            "entries": [
                {
                    "text_id": "H37-unknown_type",
                    "hexagram_id": 37,
                    "text_type": "unknown_type",
                    "line_position": None,
                    "line_name": None,
                    "original_text": None,
                    "source_id": "SOURCE_PENDING",
                    "edition": None,
                    "page": None,
                    "variant_readings": [],
                    "verification_status": "pending",
                }
            ],
        }
        errors = list(validator.iter_errors(doc))
        assert errors, "应有 schema 错误但没有"


# ---------------------------------------------------------------------------
# make_text_id
# ---------------------------------------------------------------------------


class TestMakeTextId:
    def test_gua_ci_no_position(self):
        assert make_text_id(37, "gua_ci", None) == "H37-gua_ci"

    def test_yao_ci_with_position(self):
        assert make_text_id(37, "yao_ci", 3) == "H37-yao_ci-L3"

    def test_yao_ci_position_1(self):
        assert make_text_id(1, "yao_ci", 1) == "H01-yao_ci-L1"

    def test_yao_ci_position_6(self):
        assert make_text_id(64, "yao_ci", 6) == "H64-yao_ci-L6"

    def test_yong_yong_jiu(self):
        assert make_text_id(1, "yong", "用九") == "H01-yong-用九"

    def test_yong_yong_liu(self):
        assert make_text_id(2, "yong", "用六") == "H02-yong-用六"

    def test_tuan_no_position(self):
        assert make_text_id(37, "tuan", None) == "H37-tuan"

    def test_da_xiang_no_position(self):
        assert make_text_id(37, "da_xiang", None) == "H37-da_xiang"

    def test_xiao_xiang_with_position(self):
        assert make_text_id(37, "xiao_xiang", 5) == "H37-xiao_xiang-L5"

    def test_xiao_xiang_null_position(self):
        assert make_text_id(37, "xiao_xiang", None) == "H37-xiao_xiang"

    def test_hexagram_id_zero_padded(self):
        assert make_text_id(1, "gua_ci", None) == "H01-gua_ci"

    def test_invalid_text_type_raises(self):
        with pytest.raises(CanonicalTextError, match="无效 text_type"):
            make_text_id(37, "bad_type", None)

    def test_invalid_hexagram_id_too_low_raises(self):
        with pytest.raises(CanonicalTextError, match="超出范围"):
            make_text_id(0, "gua_ci", None)

    def test_invalid_hexagram_id_too_high_raises(self):
        with pytest.raises(CanonicalTextError, match="超出范围"):
            make_text_id(65, "gua_ci", None)

    def test_yong_invalid_position_raises(self):
        with pytest.raises(CanonicalTextError, match="用九.*用六"):
            make_text_id(1, "yong", 1)

    def test_yao_ci_invalid_position_raises(self):
        with pytest.raises(CanonicalTextError, match="1..6"):
            make_text_id(37, "yao_ci", 7)

    def test_yao_ci_none_position_raises(self):
        with pytest.raises(CanonicalTextError):
            make_text_id(37, "yao_ci", None)


# ---------------------------------------------------------------------------
# load_canonical_texts
# ---------------------------------------------------------------------------


class TestLoadCanonicalTexts:
    def test_returns_empty_list_when_file_missing(self, tmp_path: Path):
        result = load_canonical_texts(data_dir=tmp_path)
        assert result == []

    def test_returns_entries_when_file_exists(self, tmp_path: Path):
        data = {
            "version": "1",
            "entries": [
                {
                    "text_id": "H37-gua_ci",
                    "hexagram_id": 37,
                    "text_type": "gua_ci",
                    "line_position": None,
                    "line_name": None,
                    "original_text": None,
                    "source_id": "SOURCE_PENDING",
                    "edition": None,
                    "page": None,
                    "variant_readings": [],
                    "verification_status": "pending",
                }
            ],
        }
        (tmp_path / "canonical-texts.json").write_text(
            json.dumps(data), encoding="utf-8"
        )
        result = load_canonical_texts(data_dir=tmp_path)
        assert len(result) == 1
        assert result[0]["text_id"] == "H37-gua_ci"

    def test_does_not_write_file(self, tmp_path: Path):
        data = {"version": "1", "entries": []}
        p = tmp_path / "canonical-texts.json"
        p.write_text(json.dumps(data), encoding="utf-8")
        original_mtime = p.stat().st_mtime
        load_canonical_texts(data_dir=tmp_path)
        assert p.stat().st_mtime == original_mtime


# ---------------------------------------------------------------------------
# import_canonical_from_csv — 正例
# ---------------------------------------------------------------------------


class TestImportCanonicalFromCsvPositive:
    def test_all_pending_rows_imported(self, tmp_path: Path):
        sources = _make_sources()
        rows = (
            [
                _pending_row("gua_ci"),
                _pending_row("tuan"),
                _pending_row("da_xiang"),
            ]
            + [_pending_row("yao_ci", str(i)) for i in range(1, 7)]
        )
        p = _write_csv(tmp_path, "test.csv", rows)
        result = import_canonical_from_csv(p, sources, 37)
        assert len(result) == 9
        assert result[0]["text_id"] == "H37-gua_ci"
        assert result[3]["text_id"] == "H37-yao_ci-L1"

    def test_verified_row_with_real_source(self, tmp_path: Path):
        sources = _make_sources("SRC-001")
        rows = [
            {
                "text_type": "gua_ci",
                "line_position": "",
                "line_name": "",
                "original_text": "〔测试文本甲〕",
                "source_id": "SRC-001",
                "edition": "测试版本甲",
                "page": "1",
                "variant_readings_json": "",
                "verification_status": "verified",
            }
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        result = import_canonical_from_csv(p, sources, 37)
        assert len(result) == 1
        assert result[0]["original_text"] == "〔测试文本甲〕"
        assert result[0]["verification_status"] == "verified"

    def test_variant_readings_parsed_from_json(self, tmp_path: Path):
        sources = _make_sources()
        vr = [{"text": "〔测试文本乙〕", "source_id": "SOURCE_PENDING", "note": None}]
        rows = [
            {
                "text_type": "gua_ci",
                "line_position": "",
                "line_name": "",
                "original_text": "",
                "source_id": PENDING_SOURCE_ID,
                "edition": "",
                "page": "",
                "variant_readings_json": json.dumps(vr, ensure_ascii=False),
                "verification_status": "pending",
            }
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        result = import_canonical_from_csv(p, sources, 37)
        assert result[0]["variant_readings"] == vr

    def test_empty_variant_readings_json_becomes_empty_list(self, tmp_path: Path):
        sources = _make_sources()
        rows = [_pending_row("gua_ci")]
        p = _write_csv(tmp_path, "test.csv", rows)
        result = import_canonical_from_csv(p, sources, 37)
        assert result[0]["variant_readings"] == []

    def test_returns_new_list_does_not_modify_sources(self, tmp_path: Path):
        """确认函数返回新列表，不修改入参 sources。"""
        sources = _make_sources()
        sources_copy = copy.deepcopy(sources)
        rows = [_pending_row("gua_ci")]
        p = _write_csv(tmp_path, "test.csv", rows)
        _ = import_canonical_from_csv(p, sources, 37)
        assert sources == sources_copy

    def test_yong_row_imported(self, tmp_path: Path):
        sources = _make_sources()
        rows = [
            {
                "text_type": "yong",
                "line_position": "用九",
                "line_name": "",
                "original_text": "",
                "source_id": PENDING_SOURCE_ID,
                "edition": "",
                "page": "",
                "variant_readings_json": "",
                "verification_status": "pending",
            }
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        result = import_canonical_from_csv(p, sources, 1)
        assert result[0]["text_id"] == "H01-yong-用九"
        assert result[0]["line_position"] == "用九"

    def test_page_parsed_as_integer_when_numeric(self, tmp_path: Path):
        sources = _make_sources("SRC-001")
        rows = [
            {
                "text_type": "gua_ci",
                "line_position": "",
                "line_name": "",
                "original_text": "〔测试文本丙〕",
                "source_id": "SRC-001",
                "edition": "测试版本乙",
                "page": "42",
                "variant_readings_json": "",
                "verification_status": "verified",
            }
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        result = import_canonical_from_csv(p, sources, 37)
        assert result[0]["page"] == 42


# ---------------------------------------------------------------------------
# import_canonical_from_csv — 反例
# ---------------------------------------------------------------------------


class TestImportCanonicalFromCsvNegative:
    def test_raises_on_unregistered_source_id(self, tmp_path: Path):
        sources = _make_sources("SRC-KNOWN")
        rows = [
            {
                "text_type": "gua_ci",
                "line_position": "",
                "line_name": "",
                "original_text": "〔测试文本甲〕",
                "source_id": "SRC-UNKNOWN",
                "edition": "测试版本甲",
                "page": "1",
                "variant_readings_json": "",
                "verification_status": "verified",
            }
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        with pytest.raises(CanonicalTextError, match="未在 sources 中登记"):
            import_canonical_from_csv(p, sources, 37)

    def test_raises_when_source_status_not_selected(self, tmp_path: Path):
        sources = _make_sources("SRC-DRAFT", status="draft")
        rows = [
            {
                "text_type": "gua_ci",
                "line_position": "",
                "line_name": "",
                "original_text": "〔测试文本乙〕",
                "source_id": "SRC-DRAFT",
                "edition": "测试版本甲",
                "page": "1",
                "variant_readings_json": "",
                "verification_status": "verified",
            }
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        with pytest.raises(CanonicalTextError, match="status.*不是.*selected"):
            import_canonical_from_csv(p, sources, 37)

    def test_raises_when_edition_empty_with_original_text(self, tmp_path: Path):
        sources = _make_sources("SRC-001")
        rows = [
            {
                "text_type": "gua_ci",
                "line_position": "",
                "line_name": "",
                "original_text": "〔测试文本丙〕",
                "source_id": "SRC-001",
                "edition": "",
                "page": "1",
                "variant_readings_json": "",
                "verification_status": "verified",
            }
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        with pytest.raises(CanonicalTextError, match="edition"):
            import_canonical_from_csv(p, sources, 37)

    def test_raises_when_page_empty_with_original_text(self, tmp_path: Path):
        sources = _make_sources("SRC-001")
        rows = [
            {
                "text_type": "gua_ci",
                "line_position": "",
                "line_name": "",
                "original_text": "〔测试文本丁〕",
                "source_id": "SRC-001",
                "edition": "测试版本甲",
                "page": "",
                "variant_readings_json": "",
                "verification_status": "verified",
            }
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        with pytest.raises(CanonicalTextError, match="page"):
            import_canonical_from_csv(p, sources, 37)

    def test_raises_on_duplicate_yao_ci_position(self, tmp_path: Path):
        sources = _make_sources()
        rows = [
            _pending_row("yao_ci", "3"),
            _pending_row("yao_ci", "3"),
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        with pytest.raises(CanonicalTextError, match="重复"):
            import_canonical_from_csv(p, sources, 37)

    def test_raises_on_invalid_text_type(self, tmp_path: Path):
        sources = _make_sources()
        rows = [
            {
                "text_type": "not_a_type",
                "line_position": "",
                "line_name": "",
                "original_text": "",
                "source_id": PENDING_SOURCE_ID,
                "edition": "",
                "page": "",
                "variant_readings_json": "",
                "verification_status": "pending",
            }
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        with pytest.raises(CanonicalTextError, match="text_type"):
            import_canonical_from_csv(p, sources, 37)

    def test_raises_on_line_position_mismatch_gua_ci_with_position(self, tmp_path: Path):
        """gua_ci 给了非空 line_position 时抛出 CanonicalTextError。"""
        sources = _make_sources()
        rows = [
            {
                "text_type": "gua_ci",
                "line_position": "3",
                "line_name": "",
                "original_text": "",
                "source_id": PENDING_SOURCE_ID,
                "edition": "",
                "page": "",
                "variant_readings_json": "",
                "verification_status": "pending",
            }
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        with pytest.raises(CanonicalTextError):
            import_canonical_from_csv(p, sources, 37)

    def test_raises_on_yao_ci_position_out_of_range(self, tmp_path: Path):
        sources = _make_sources()
        rows = [
            {
                "text_type": "yao_ci",
                "line_position": "7",
                "line_name": "",
                "original_text": "",
                "source_id": PENDING_SOURCE_ID,
                "edition": "",
                "page": "",
                "variant_readings_json": "",
                "verification_status": "pending",
            }
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        with pytest.raises(CanonicalTextError):
            import_canonical_from_csv(p, sources, 37)

    def test_raises_on_duplicate_gua_ci(self, tmp_path: Path):
        sources = _make_sources()
        rows = [_pending_row("gua_ci"), _pending_row("gua_ci")]
        p = _write_csv(tmp_path, "test.csv", rows)
        with pytest.raises(CanonicalTextError, match="重复"):
            import_canonical_from_csv(p, sources, 37)

    def test_does_not_modify_sources_on_error(self, tmp_path: Path):
        """即使导入失败，sources 入参也不被修改。"""
        sources = _make_sources("SRC-KNOWN")
        original_sources = copy.deepcopy(sources)
        rows = [
            {
                "text_type": "gua_ci",
                "line_position": "",
                "line_name": "",
                "original_text": "〔测试文本戊〕",
                "source_id": "SRC-UNKNOWN",
                "edition": "测试版本甲",
                "page": "1",
                "variant_readings_json": "",
                "verification_status": "verified",
            }
        ]
        p = _write_csv(tmp_path, "test.csv", rows)
        with pytest.raises(CanonicalTextError):
            import_canonical_from_csv(p, sources, 37)
        assert sources == original_sources


# ---------------------------------------------------------------------------
# import_canonical_from_csv — 使用 fixtures 目录中的 CSV
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "texts"


class TestImportFromFixtures:
    def test_valid_h37_csv_imported(self):
        """fixtures/texts/h37_valid.csv 能正常导入（全部 pending 条目）。"""
        csv_path = FIXTURES_DIR / "h37_valid.csv"
        sources: list[dict] = []  # 全部 SOURCE_PENDING，无需真实 source
        result = import_canonical_from_csv(csv_path, sources, 37)
        text_types_found = {e["text_type"] for e in result}
        assert "gua_ci" in text_types_found
        assert "yao_ci" in text_types_found
        assert "tuan" in text_types_found
        assert "da_xiang" in text_types_found
        assert "xiao_xiang" in text_types_found

    def test_invalid_csv_raises_on_missing_edition(self):
        """fixtures/texts/h37_invalid_missing_edition.csv 应抛出 CanonicalTextError。"""
        csv_path = FIXTURES_DIR / "h37_invalid_missing_edition.csv"
        sources = [{"id": "SRC-TEST-001", "status": "selected"}]
        with pytest.raises(CanonicalTextError, match="edition"):
            import_canonical_from_csv(csv_path, sources, 37)

    def test_pending_json_fixture_validates_against_schema(self):
        """pending.json fixture 通过 schema 校验。"""
        schema = _load_schema()
        validator = Draft202012Validator(schema)
        with (FIXTURES_DIR / "pending.json").open(encoding="utf-8") as fh:
            doc = json.load(fh)
        errors = list(validator.iter_errors(doc))
        assert errors == [], [str(e) for e in errors]


# ---------------------------------------------------------------------------
# validate_canonical_texts
# ---------------------------------------------------------------------------


def _make_hexagrams_stub(ids: list[int] | None = None) -> list[dict]:
    if ids is None:
        ids = list(range(1, 65))
    return [{"hexagram_id": i} for i in ids]


def _pending_entry(
    hexagram_id: int,
    text_type: str,
    line_position: int | str | None = None,
    line_name: str | None = None,
) -> dict:
    return {
        "text_id": make_text_id(hexagram_id, text_type, line_position),
        "hexagram_id": hexagram_id,
        "text_type": text_type,
        "line_position": line_position,
        "line_name": line_name,
        "original_text": None,
        "source_id": PENDING_SOURCE_ID,
        "edition": None,
        "page": None,
        "variant_readings": [],
        "verification_status": "pending",
    }


def _full_h37_pending() -> list[dict]:
    entries = [
        _pending_entry(37, "gua_ci"),
        _pending_entry(37, "tuan"),
        _pending_entry(37, "da_xiang"),
    ]
    for i in range(1, 7):
        entries.append(_pending_entry(37, "yao_ci", i))
    return entries


class TestValidateCanonicalTexts:
    def test_no_errors_for_complete_pending_set(self):
        entries = _full_h37_pending()
        hexagrams = _make_hexagrams_stub()
        errors = validate_canonical_texts(entries, hexagrams)
        assert errors == []

    def test_detects_incomplete_yao_ci(self):
        entries = [_pending_entry(37, "gua_ci")] + [
            _pending_entry(37, "yao_ci", i) for i in range(1, 6)
        ]
        hexagrams = _make_hexagrams_stub()
        errors = validate_canonical_texts(entries, hexagrams)
        rules = [e["rule"] for e in errors]
        assert "yao_ci_incomplete" in rules

    def test_detects_duplicate_yao_ci_position(self):
        e1 = _pending_entry(37, "yao_ci", 3)
        e2 = copy.deepcopy(e1)
        hexagrams = _make_hexagrams_stub()
        errors = validate_canonical_texts([e1, e2], hexagrams)
        rules = [e["rule"] for e in errors]
        assert "yao_ci_duplicate_position" in rules

    def test_detects_duplicate_gua_ci(self):
        entries = [
            _pending_entry(37, "gua_ci"),
            _pending_entry(37, "gua_ci"),
        ]
        hexagrams = _make_hexagrams_stub()
        errors = validate_canonical_texts(entries, hexagrams)
        rules = [e["rule"] for e in errors]
        assert "gua_ci_duplicate" in rules

    def test_detects_original_text_with_source_pending(self):
        entry = _pending_entry(37, "gua_ci")
        entry["original_text"] = "〔测试文本甲〕"
        hexagrams = _make_hexagrams_stub()
        errors = validate_canonical_texts([entry], hexagrams)
        rules = [e["rule"] for e in errors]
        assert "original_text_requires_real_source" in rules

    def test_detects_original_text_missing_edition(self):
        entry = _pending_entry(37, "gua_ci")
        entry["original_text"] = "〔测试文本乙〕"
        entry["source_id"] = "SRC-001"
        entry["page"] = 1
        entry["verification_status"] = "verified"
        hexagrams = _make_hexagrams_stub()
        errors = validate_canonical_texts([entry], hexagrams)
        rules = [e["rule"] for e in errors]
        assert "original_text_requires_edition" in rules

    def test_detects_original_text_missing_page(self):
        entry = _pending_entry(37, "gua_ci")
        entry["original_text"] = "〔测试文本丙〕"
        entry["source_id"] = "SRC-001"
        entry["edition"] = "测试版本甲"
        entry["verification_status"] = "verified"
        hexagrams = _make_hexagrams_stub()
        errors = validate_canonical_texts([entry], hexagrams)
        rules = [e["rule"] for e in errors]
        assert "original_text_requires_page" in rules

    def test_detects_variant_readings_duplicate(self):
        entry = _pending_entry(37, "gua_ci")
        vr = {"text": "〔测试文本丁〕", "source_id": "SRC-001", "note": None}
        entry["variant_readings"] = [vr, copy.deepcopy(vr)]
        hexagrams = _make_hexagrams_stub()
        errors = validate_canonical_texts([entry], hexagrams)
        rules = [e["rule"] for e in errors]
        assert "variant_readings_duplicate" in rules

    def test_detects_out_of_range_hexagram_id(self):
        entry = _pending_entry(37, "gua_ci")
        entry["hexagram_id"] = 99
        hexagrams = _make_hexagrams_stub()
        errors = validate_canonical_texts([entry], hexagrams)
        rules = [e["rule"] for e in errors]
        assert "hexagram_id_range" in rules

    def test_no_errors_for_verified_entry_with_full_fields(self):
        entry = _pending_entry(37, "gua_ci")
        entry["original_text"] = "〔测试文本戊〕"
        entry["source_id"] = "SRC-001"
        entry["edition"] = "测试版本乙"
        entry["page"] = 99
        entry["verification_status"] = "verified"
        hexagrams = _make_hexagrams_stub()
        errors = validate_canonical_texts([entry], hexagrams)
        assert errors == []

    def test_does_not_modify_entries_input(self):
        entries = _full_h37_pending()
        entries_copy = copy.deepcopy(entries)
        hexagrams = _make_hexagrams_stub()
        validate_canonical_texts(entries, hexagrams)
        assert entries == entries_copy

    def test_returns_list_not_raises_on_error(self):
        """validate_canonical_texts 遇到错误时返回错误列表，不抛异常。"""
        entry = _pending_entry(37, "gua_ci")
        entry["hexagram_id"] = 0
        hexagrams = _make_hexagrams_stub()
        result = validate_canonical_texts([entry], hexagrams)
        assert isinstance(result, list)
        assert len(result) > 0


# ---------------------------------------------------------------------------
# 常量与模块级属性
# ---------------------------------------------------------------------------


class TestConstants:
    def test_pending_source_id_value(self):
        assert PENDING_SOURCE_ID == "SOURCE_PENDING"

    def test_pending_text_is_placeholder(self):
        assert "待底本校勘" in PENDING_TEXT

    def test_text_types_tuple(self):
        assert set(TEXT_TYPES) == {
            "gua_ci",
            "yao_ci",
            "yong",
            "tuan",
            "da_xiang",
            "xiao_xiang",
        }
