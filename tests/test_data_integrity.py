"""已提交数据文件的完整性与经文红线（PLAN §3.4、§3.5）。"""
import json
from pathlib import Path

from gxwd.domain import load_hexagrams
from gxwd.yao import build_yao_records

DATA = Path(__file__).resolve().parents[1] / "data"
HINT = "请运行 `gxwd init` 生成"


def _load(name):
    path = DATA / name
    assert path.exists(), f"{name} 缺失，{HINT}"
    return json.loads(path.read_text(encoding="utf-8"))


def _all_lines(hexagrams):
    for hexagram in hexagrams:
        yield from hexagram["lines"]
        yield from hexagram.get("extra_lines", [])


def test_yao_texts_equal_generated_records():
    data = _load("yao-texts.json")
    assert data["hexagrams"] == build_yao_records(load_hexagrams())


def test_yao_line_counts():
    hexagrams = _load("yao-texts.json")["hexagrams"]
    assert sum(len(h["lines"]) for h in hexagrams) == 384
    assert sum(len(h.get("extra_lines", [])) for h in hexagrams) == 2


def test_no_original_text_and_source_pending():
    lines = list(_all_lines(_load("yao-texts.json")["hexagrams"]))
    assert len(lines) == 386
    assert all(line["original_text"] is None for line in lines)
    assert all(line["source_id"] == "SOURCE_PENDING" for line in lines)


def test_sources_awaiting_human_selection():
    data = _load("sources.json")
    assert data["status"] == "awaiting_human_selection"
    assert data["sources"] == []


def test_asset_catalog_ids_match_master():
    records = _load("asset-catalog.json")["records"]
    assert len(records) == 64
    assert [r["hexagram_id"] for r in records] == [h["hexagram_id"] for h in load_hexagrams()]
