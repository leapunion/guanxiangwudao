#!/usr/bin/env python3
"""scripts/build-web.py — 薄壳 shim；核心逻辑在 src/gxwd/web.py。

保留本脚本是为了命令行历史兼容：
    .venv/bin/python scripts/build-web.py

新的入口是：
    .venv/bin/gxwd web build
"""
from __future__ import annotations

from gxwd.web import main

if __name__ == "__main__":
    raise SystemExit(main())
