"""文王卦序双盲交叉校验：独立 fixture vs data/hexagrams.json 逐卦 diff。"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "kingwen_independent.json"
MASTER = ROOT / "data" / "hexagrams.json"

# 阳 1 阴 0，自下而上
TRIGRAM_BITS = {
    "乾": "111", "坤": "000", "震": "100", "巽": "011",
    "坎": "010", "离": "101", "艮": "001", "兑": "110",
}
ARBITRATION = "需人工裁定，禁止单边修改迁就"


def _load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _lines(entry):
    """六爻自下而上，下卦在前。"""
    return TRIGRAM_BITS[entry["lower"]] + TRIGRAM_BITS[entry["upper"]]


FIXTURE_BY_ID = {e["hexagram_id"]: e for e in _load_fixture()}


@pytest.fixture(scope="module")
def master_by_id():
    assert MASTER.exists(), f"主数据 {MASTER} 缺失，请运行 `gxwd init` 生成"
    data = json.loads(MASTER.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("hexagrams", list(data.values()))
    return {h["hexagram_id"]: h for h in data}


@pytest.mark.parametrize("hid", range(1, 65))
def test_master_matches_independent_table(hid, master_by_id):
    # Arrange
    expected = FIXTURE_BY_ID[hid]
    actual = master_by_id.get(hid)
    assert actual is not None, f"主数据缺少第 {hid} 卦。{ARBITRATION}"

    # Act
    got = {
        "name": actual["name"],
        "upper": actual["upper_trigram"]["name"],
        "lower": actual["lower_trigram"]["name"],
    }
    want = {k: expected[k] for k in ("name", "upper", "lower")}

    # Assert
    assert got == want, (
        f"第 {hid} 卦不一致：主数据={got} 独立表={want}。{ARBITRATION}"
    )


def test_fixture_has_64_unique_combinations():
    # Arrange
    entries = _load_fixture()

    # Act
    combos = {(e["upper"], e["lower"]) for e in entries}
    ids = [e["hexagram_id"] for e in entries]

    # Assert
    assert len(entries) == 64
    assert ids == list(range(1, 65))
    assert len(combos) == 64
    assert len({e["name"] for e in entries}) == 64


@pytest.mark.parametrize("k", range(1, 33))
def test_fixture_pairs_are_reverse_or_inverse(k):
    # Arrange
    a, b = FIXTURE_BY_ID[2 * k - 1], FIXTURE_BY_ID[2 * k]
    la, lb = _lines(a), _lines(b)

    # Act
    reversed_a = la[::-1]
    inverted_a = "".join("1" if c == "0" else "0" for c in la)

    # Assert
    if reversed_a != la:
        assert lb == reversed_a, f"{a['name']}/{b['name']} 应互为反卦"
    else:
        assert lb == inverted_a, f"{a['name']}/{b['name']} 颠倒不变，应互为错卦"
