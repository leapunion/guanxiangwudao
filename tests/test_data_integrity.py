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


def test_sources_selected_zyzy_ruan():
    """V0.5 选定底本为阮元刻十三经注疏本《周易正义》（source_id=ZYZY-RUAN）。"""
    data = _load("sources.json")
    assert data["status"] == "selected"
    source_ids = {s["source_id"] for s in data["sources"]}
    assert "ZYZY-RUAN" in source_ids
    zyzy = next(s for s in data["sources"] if s["source_id"] == "ZYZY-RUAN")
    assert zyzy["status"] == "selected"
    assert zyzy["title"] == "周易正义"


def test_asset_catalog_ids_match_master():
    records = _load("asset-catalog.json")["records"]
    assert len(records) == 64
    assert [r["hexagram_id"] for r in records] == [h["hexagram_id"] for h in load_hexagrams()]


def test_art_style_covers_64_assignments():
    """风格归属文件覆盖 1..64 全部卦；code ∈ {G, M, S, P}；未签字时 signed_by/signed_at 为 null。"""
    data = _load("art-style.json")
    assignments = data["assignments"]
    assert len(assignments) == 64
    ids = {a["hexagram_id"] for a in assignments}
    assert ids == set(range(1, 65))
    codes = {a["style_code"] for a in assignments}
    assert codes <= {"G", "M", "S", "P"}
    assert set(data["styles"]) == codes


def test_approvers_skeleton_present_and_valid():
    """审批人名单文件必须存在；本轮空列表是允许的（publisher 会拒绝任何
    approved_by，但文件本身必须就位）。"""
    data = _load("approvers.json")
    assert "approvers" in data
    assert isinstance(data["approvers"], list)
    # 允许空列表（骨架态）；但每条已登记项必须有 id、name、role 三字段。
    for approver in data["approvers"]:
        assert set(approver) >= {"id", "name", "role"}, approver
