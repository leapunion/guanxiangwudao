"""卦象主数据校验。validate_all 不抛异常、不修改入参。"""
from __future__ import annotations

from typing import Any

from gxwd.domain import lines_from_binary, load_trigrams

_BITS = {"0", "1"}
_HEXAGRAM_COUNT = 64
_SYMBOL_BASE = 0x4DC0
_PAIR_RULE = "kingwen_pair"

Error = dict[str, Any]


class HexagramValidationError(ValueError):
    """卦象输入非法或自相矛盾。"""


def _is_binary(value: object, length: int) -> bool:
    return isinstance(value, str) and len(value) == length and set(value) <= _BITS


def _trigram_map(trigrams: list[dict[str, Any]]) -> dict[str, str]:
    return {t["name"]: t["binary"] for t in trigrams}


def validate_hexagram(lower: str, upper: str, binary: str) -> dict[str, Any]:
    table = _trigram_map(load_trigrams())
    for label, name in (("lower", lower), ("upper", upper)):
        if name not in table:
            raise HexagramValidationError(f"unknown {label} trigram: {name!r}")
    if not _is_binary(binary, 6):
        raise HexagramValidationError(f"binary must be 6 chars of 0/1: {binary!r}")
    expected = table[lower] + table[upper]
    if binary != expected:
        raise HexagramValidationError(
            f"binary {binary} does not match lower {lower} + upper {upper} = {expected}"
        )
    return {
        "valid": True,
        "lower": lower,
        "upper": upper,
        "binary": binary,
        "lines_top_to_bottom": lines_from_binary(binary),
    }


def _err(hexagram_id: int | None, rule: str, detail: str) -> Error:
    return {"hexagram_id": hexagram_id, "rule": rule, "detail": detail}


def _check_ids(hexagrams: list[dict[str, Any]]) -> list[Error]:
    ids = [h.get("hexagram_id") for h in hexagrams]
    errors: list[Error] = []
    seen: set[Any] = set()
    for hid in ids:
        if hid in seen:
            errors.append(_err(hid if isinstance(hid, int) else None, "id_unique", f"duplicate id {hid!r}"))
        seen.add(hid)
    if sorted(ids, key=repr) != sorted(range(1, _HEXAGRAM_COUNT + 1), key=repr):
        errors.append(_err(None, "id_sequence", f"ids must be 1..{_HEXAGRAM_COUNT}, got {len(ids)} entries"))
    return errors


def _check_binary_coverage(hexagrams: list[dict[str, Any]]) -> list[Error]:
    errors: list[Error] = []
    seen: dict[str, Any] = {}
    for h in hexagrams:
        b = h.get("binary_bottom_to_top")
        if not _is_binary(b, 6):
            continue
        if b in seen:
            errors.append(_err(h.get("hexagram_id"), "binary_unique", f"{b} duplicates hexagram {seen[b]}"))
        seen[b] = h.get("hexagram_id")
    if len(seen) != _HEXAGRAM_COUNT:
        errors.append(_err(None, "binary_coverage", f"{len(seen)} distinct codes, expected {_HEXAGRAM_COUNT}"))
    return errors


def _check_trigram_ref(h: dict[str, Any], key: str, table: dict[str, str]) -> list[Error]:
    hid = h.get("hexagram_id")
    ref = h.get(key) or {}
    name = ref.get("name")
    if name not in table:
        return [_err(hid, "trigram_name", f"{key} {name!r} not in trigram table")]
    if ref.get("binary") != table[name]:
        return [_err(hid, "trigram_binary", f"{key} {name} binary {ref.get('binary')!r} != {table[name]}")]
    return []


def _check_hexagram(h: dict[str, Any], table: dict[str, str]) -> list[Error]:
    hid = h.get("hexagram_id")
    errors: list[Error] = []
    binary = h.get("binary_bottom_to_top")
    if not _is_binary(binary, 6):
        errors.append(_err(hid, "binary_format", f"binary must be 6 chars of 0/1: {binary!r}"))
    errors += _check_trigram_ref(h, "lower_trigram", table)
    errors += _check_trigram_ref(h, "upper_trigram", table)
    lower = (h.get("lower_trigram") or {}).get("binary", "")
    upper = (h.get("upper_trigram") or {}).get("binary", "")
    if binary != lower + upper:
        errors.append(_err(hid, "binary_composition", f"{binary!r} != lower {lower!r} + upper {upper!r}"))
    if _is_binary(binary, 6) and h.get("lines_top_to_bottom") != lines_from_binary(binary):
        errors.append(_err(hid, "lines_order", "lines_top_to_bottom is not the reverse of binary"))
    if isinstance(hid, int) and h.get("symbol") != chr(_SYMBOL_BASE + hid - 1):
        errors.append(_err(hid, "symbol", f"symbol {h.get('symbol')!r} != U+{_SYMBOL_BASE + hid - 1:04X}"))
    return errors


def _complement(binary: str) -> str:
    return "".join("0" if c == "1" else "1" for c in binary)


def _check_pairs(hexagrams: list[dict[str, Any]]) -> list[Error]:
    by_id = {h.get("hexagram_id"): h for h in hexagrams}
    errors: list[Error] = []
    for odd in range(1, _HEXAGRAM_COUNT, 2):
        a, b = by_id.get(odd), by_id.get(odd + 1)
        if a is None or b is None:
            continue
        ba, bb = a.get("binary_bottom_to_top"), b.get("binary_bottom_to_top")
        if not (_is_binary(ba, 6) and _is_binary(bb, 6)):
            continue
        reversed_a = ba[::-1]
        expected = _complement(ba) if reversed_a == ba else reversed_a
        if bb != expected:
            errors.append(_err(odd, _PAIR_RULE, f"pair {odd}-{odd + 1}: {ba} -> expected {expected}, got {bb}"))
    return errors


def validate_all(hexagrams: list[dict[str, Any]], trigrams: list[dict[str, Any]]) -> dict[str, Any]:
    table = _trigram_map(trigrams)
    errors: list[Error] = []
    errors += _check_ids(hexagrams)
    errors += _check_binary_coverage(hexagrams)
    for h in hexagrams:
        errors += _check_hexagram(h, table)
    errors += _check_pairs(hexagrams)
    return {"valid": not errors, "checked": len(hexagrams), "errors": errors}
