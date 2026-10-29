from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schemas"
DATA_DIR = ROOT / "data"
SCHEMA_NAMES = ["trigrams", "hexagrams", "yao-texts", "sources", "asset-catalog", "approvers"]


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(_load(SCHEMA_DIR / f"{name}.schema.json"))


def _hexagram(hexagram_id: int = 37) -> dict:
    return {
        "hexagram_id": hexagram_id, "name": "家人", "full_name": "风火家人",
        "slug": "jiaren", "symbol": "䷤",
        "lower_trigram": {"name": "离", "binary": "101"},
        "upper_trigram": {"name": "巽", "binary": "011"},
        "binary_bottom_to_top": "101011",
        "lines_top_to_bottom": ["yang", "yang", "yin", "yang", "yin", "yang"],
        "text_verification": "pending", "artwork_status": "not_checked",
    }


def _yao_entry(original_text: Any = None) -> dict:
    line = {
        "position": 1, "line_type": "yang", "line_name": "初九",
        "original_text": original_text, "source_id": "SOURCE_PENDING",
        "edition": None, "page": None, "variant_readings": [],
        "interpretation": None, "historical_story_id": None,
        "verification_status": "pending",
    }
    return {"hexagram_id": 37, "lines": [dict(line, position=i) for i in range(1, 7)], "extra_lines": []}


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_is_valid_draft_2020_12(name: str) -> None:
    Draft202012Validator.check_schema(_load(SCHEMA_DIR / f"{name}.schema.json"))


def test_sources_json_conforms_to_schema() -> None:
    _validator("sources").validate(_load(DATA_DIR / "sources.json"))


def test_hexagram_item_accepts_valid_sample() -> None:
    schema = _load(SCHEMA_DIR / "hexagrams.schema.json")
    item_validator = Draft202012Validator({"$ref": "#/$defs/hexagram", "$defs": schema["$defs"]})

    assert list(item_validator.iter_errors(_hexagram())) == []


@pytest.mark.parametrize(
    "mutation",
    [
        {"hexagram_id": 0}, {"hexagram_id": 65},
        {"binary_bottom_to_top": "10101"}, {"binary_bottom_to_top": "10101x"},
        {"lines_top_to_bottom": ["yang"] * 5},
        {"lines_top_to_bottom": ["yang"] * 5 + ["dragon"]},
    ],
)
def test_hexagram_item_rejects_invalid_samples(mutation: dict) -> None:
    schema = _load(SCHEMA_DIR / "hexagrams.schema.json")
    item_validator = Draft202012Validator({"$ref": "#/$defs/hexagram", "$defs": schema["$defs"]})

    errors = list(item_validator.iter_errors({**_hexagram(), **mutation}))

    assert errors


def test_hexagrams_array_requires_64_items() -> None:
    assert list(_validator("hexagrams").iter_errors([_hexagram()]))


def test_yao_schema_accepts_null_original_text() -> None:
    document = {"version": "1", "hexagrams": [_yao_entry(None)]}

    assert list(_validator("yao-texts").iter_errors(document)) == []


def test_yao_schema_rejects_non_string_original_text() -> None:
    document = {"version": "1", "hexagrams": [_yao_entry(123)]}

    assert list(_validator("yao-texts").iter_errors(document))


def test_asset_catalog_state_enum() -> None:
    validator = _validator("asset-catalog")
    record = {"hexagram_id": 1, "state": "DRAFT", "version": "0.1.0", "history": []}

    assert list(validator.iter_errors({"version": "1", "records": [record]})) == []
    assert list(validator.iter_errors({"version": "1", "records": [{**record, "state": "NOPE"}]}))


@pytest.mark.parametrize("name", ["trigrams", "hexagrams", "yao-texts", "asset-catalog"])
def test_existing_data_conforms_to_schema(name: str) -> None:
    path = DATA_DIR / f"{name}.json"
    assert path.exists(), f"{path.name} 缺失，请运行 `gxwd init` 生成"

    _validator(name).validate(_load(path))
