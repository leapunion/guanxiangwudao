import copy
import unicodedata

import pytest

from gxwd.domain import get_hexagram, lines_from_binary, load_hexagrams, load_trigrams
from gxwd.validator import validate_all

PURE = {1: "乾", 2: "坤", 29: "坎", 30: "离", 51: "震", 52: "艮", 57: "巽", 58: "兑"}


@pytest.fixture(scope="module")
def hexagrams():
    return load_hexagrams()


@pytest.fixture(scope="module")
def trigrams():
    return load_trigrams()


def test_real_data_is_valid(hexagrams, trigrams):
    result = validate_all(hexagrams, trigrams)
    assert result == {"valid": True, "checked": 64, "errors": []}


def test_trigram_encoding_matches_contract(trigrams):
    codes = {t["name"]: t["binary"] for t in trigrams}
    assert codes == {"乾": "111", "坤": "000", "震": "100", "巽": "011",
                     "坎": "010", "离": "101", "艮": "001", "兑": "110"}
    assert [t["virtue"] for t in trigrams] == ["健", "顺", "动", "入", "陷", "丽", "止", "悦"]


def test_symbols_are_in_unicode_hexagram_block(hexagrams):
    for h in hexagrams:
        assert h["symbol"] == chr(0x4DC0 + h["hexagram_id"] - 1)
        assert unicodedata.name(h["symbol"]).startswith("HEXAGRAM FOR")


@pytest.mark.parametrize("hid,name", PURE.items())
def test_pure_hexagrams_have_same_upper_and_lower(hid, name):
    h = get_hexagram(hid)
    assert h["lower_trigram"]["name"] == h["upper_trigram"]["name"] == name
    assert "为" in h["full_name"]


def test_tai_is_lower_qian_upper_kun():
    h = get_hexagram(11)
    assert (h["lower_trigram"]["name"], h["upper_trigram"]["name"]) == ("乾", "坤")


def test_pi_is_lower_kun_upper_qian():
    h = get_hexagram(12)
    assert (h["lower_trigram"]["name"], h["upper_trigram"]["name"]) == ("坤", "乾")


def test_jiji_weiji_codes():
    assert get_hexagram(63)["binary_bottom_to_top"] == "101010"
    assert get_hexagram(64)["binary_bottom_to_top"] == "010101"


def test_jiaren_anchor():
    h = get_hexagram(37)
    assert h["binary_bottom_to_top"] == "101011"
    assert h["full_name"] == "风火家人"
    assert h["lines_top_to_bottom"] == ["yang", "yang", "yin", "yang", "yin", "yang"]


def test_kingwen_pairs_are_reverse_or_complement(hexagrams):
    for odd in range(1, 64, 2):
        a = hexagrams[odd - 1]["binary_bottom_to_top"]
        b = hexagrams[odd]["binary_bottom_to_top"]
        flipped = "".join("0" if c == "1" else "1" for c in a)
        expected = flipped if a[::-1] == a else a[::-1]
        assert b == expected


def test_lines_from_binary_reverses_order():
    assert lines_from_binary("100000") == ["yin"] * 5 + ["yang"]


def test_lines_from_binary_rejects_bad_input():
    with pytest.raises(ValueError):
        lines_from_binary("10201")


def test_get_hexagram_missing_raises_key_error():
    with pytest.raises(KeyError):
        get_hexagram(65)


def test_all_hexagrams_have_pending_status_and_no_classical_text(hexagrams):
    for h in hexagrams:
        assert h["text_verification"] == "pending"
        assert h["artwork_status"] == "not_checked"
        assert set(h) == {"hexagram_id", "name", "full_name", "slug", "symbol", "lower_trigram",
                          "upper_trigram", "binary_bottom_to_top", "lines_top_to_bottom",
                          "text_verification", "artwork_status"}


def test_loading_returns_fresh_objects():
    first = load_hexagrams()
    snapshot = copy.deepcopy(first)
    first[0]["name"] = "改"
    assert load_hexagrams() == snapshot
