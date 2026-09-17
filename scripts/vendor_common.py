#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Copy behold_common into each suite add-on's common/ package."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "behold_common"
ADDONS = (
    ROOT / "behold_studio",
    ROOT / "behold_lighting",
    ROOT / "behold_product",
    ROOT / "behold_utilities",
)
SKIP_DIRS = {"__pycache__"}
SKIP_SUFFIXES = {".pyc", ".pyo"}
SKIP_NAMES = {".DS_Store"}


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True)
    for path in src.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_dir():
            continue
        if path.name in SKIP_NAMES or path.suffix in SKIP_SUFFIXES:
            continue
        rel = path.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def main() -> None:
    if not SRC.is_dir():
        raise SystemExit(f"missing {SRC}")
    for addon in ADDONS:
        if not addon.is_dir():
            raise SystemExit(f"missing {addon}")
        copy_tree(SRC, addon / "common")
        print(f"vendored common → {addon.name}/common")


if __name__ == "__main__":
    main()
