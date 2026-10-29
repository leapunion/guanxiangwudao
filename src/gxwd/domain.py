"""卦象领域层：数据加载与爻线转换。所有函数返回新对象，不修改入参。"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

YANG = "yang"
YIN = "yin"

_ENV_DATA_DIR = "GXWD_DATA_DIR"


def get_data_dir() -> Path:
    """返回当前环境下的 data 目录。GXWD_DATA_DIR 环境变量优先。"""
    override = os.environ.get(_ENV_DATA_DIR)
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "data"


# 向后兼容：首次导入时的默认 data 目录。应使用 get_data_dir() 获取最新值。
DATA_DIR: Path = get_data_dir()


def _load_json_list(filename: str, data_dir: Path | None) -> list[dict[str, Any]]:
    base = Path(data_dir) if data_dir is not None else get_data_dir()
    with (base / filename).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_trigrams(data_dir: Path | None = None) -> list[dict[str, Any]]:
    return _load_json_list("trigrams.json", data_dir)


def load_hexagrams(data_dir: Path | None = None) -> list[dict[str, Any]]:
    return _load_json_list("hexagrams.json", data_dir)


def get_hexagram(hexagram_id: int, data_dir: Path | None = None) -> dict[str, Any]:
    for hexagram in load_hexagrams(data_dir):
        if hexagram["hexagram_id"] == hexagram_id:
            return hexagram
    raise KeyError(hexagram_id)


def lines_from_binary(binary_bottom_to_top: str) -> list[str]:
    """自下而上的二进制串 -> 自上而下的 yang/yin 列表。"""
    if not binary_bottom_to_top or set(binary_bottom_to_top) - {"0", "1"}:
        raise ValueError(f"binary must contain only 0/1: {binary_bottom_to_top!r}")
    return [YANG if bit == "1" else YIN for bit in reversed(binary_bottom_to_top)]
