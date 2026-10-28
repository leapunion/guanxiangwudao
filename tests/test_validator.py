import copy

import pytest

from gxwd.domain import load_hexagrams, load_trigrams
from gxwd.validator import HexagramValidationError, validate_all, validate_hexagram


@pytest.fixture()
def data():
    return load_hexagrams(), load_trigrams()


def rules(result):
    return {e["rule"] for e in result["errors"]}


def test_validate_hexagram_returns_jiaren_details():
    result = validate_hexagram("离", "巽", "101011")
    assert result["valid"] is True
    assert result["binary"] == "101011"
    assert result["lines_top_to_bottom"] == ["yang", "yang", "yin", "yang", "yin", "yang"]


@pytest.mark.parametrize("lower,upper,binary", [
    ("龙", "巽", "101011"),
    ("离", "龙", "101011"),
    ("离", "巽", "10101"),
    ("离", "巽", "10101x"),
    ("离", "巽", "011101"),
])
def test_validate_hexagram_rejects_bad_input(lower, upper, binary):
    with pytest.raises(HexagramValidationError):
        validate_hexagram(lower, upper, binary)


def test_validation_error_is_value_error():
    assert issubclass(HexagramValidationError, ValueError)


def test_tampered_binary_is_detected(data):
    hexagrams, trigrams = data
    bad = copy.deepcopy(hexagrams)
    bad[36]["binary_bottom_to_top"] = "101010"
    assert not validate_all(bad, trigrams)["valid"]
    assert "binary_composition" in rules(validate_all(bad, trigrams))


def test_swapped_upper_lower_is_detected(data):
    hexagrams, trigrams = data
    bad = copy.deepcopy(hexagrams)
    h = bad[10]
    h["lower_trigram"], h["upper_trigram"] = h["upper_trigram"], h["lower_trigram"]
    result = validate_all(bad, trigrams)
    assert not result["valid"]
    assert "binary_composition" in rules(result)


def test_lines_not_reversed_is_detected(data):
    hexagrams, trigrams = data
    bad = copy.deepcopy(hexagrams)
    bad[36]["lines_top_to_bottom"] = list(reversed(bad[36]["lines_top_to_bottom"]))
    assert "lines_order" in rules(validate_all(bad, trigrams))


def test_duplicate_id_is_detected(data):
    hexagrams, trigrams = data
    bad = copy.deepcopy(hexagrams)
    bad[5]["hexagram_id"] = 5
    result = validate_all(bad, trigrams)
    assert {"id_unique", "id_sequence"} <= rules(result)


def test_wrong_symbol_is_detected(data):
    hexagrams, trigrams = data
    bad = copy.deepcopy(hexagrams)
    bad[0]["symbol"] = bad[1]["symbol"]
    assert "symbol" in rules(validate_all(bad, trigrams))


def test_unknown_trigram_name_is_detected(data):
    hexagrams, trigrams = data
    bad = copy.deepcopy(hexagrams)
    bad[0]["upper_trigram"]["name"] = "龙"
    assert "trigram_name" in rules(validate_all(bad, trigrams))


def test_duplicate_code_breaks_coverage_and_pairs(data):
    hexagrams, trigrams = data
    bad = copy.deepcopy(hexagrams)
    bad[2]["binary_bottom_to_top"] = bad[3]["binary_bottom_to_top"]
    assert {"binary_unique", "binary_coverage"} <= rules(validate_all(bad, trigrams))


def test_pair_invariant_violation_is_detected(data):
    hexagrams, trigrams = data
    bad = copy.deepcopy(hexagrams)
    bad[2]["hexagram_id"], bad[4]["hexagram_id"] = 5, 3
    assert "kingwen_pair" in rules(validate_all(bad, trigrams))


def test_missing_hexagram_is_reported_without_raising(data):
    hexagrams, trigrams = data
    result = validate_all(copy.deepcopy(hexagrams)[:63], trigrams)
    assert result["valid"] is False
    assert result["checked"] == 63


def test_validate_all_does_not_mutate_inputs(data):
    hexagrams, trigrams = data
    h_before, t_before = copy.deepcopy(hexagrams), copy.deepcopy(trigrams)
    validate_all(hexagrams, trigrams)
    assert hexagrams == h_before and trigrams == t_before
