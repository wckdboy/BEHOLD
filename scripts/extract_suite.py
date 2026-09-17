#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""One-shot extractor: copy monolith modules into the v2.0.0 suite layout."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "behold"

ADDONS = {
    "studio": ROOT / "behold_studio",
    "lighting": ROOT / "behold_lighting",
    "product": ROOT / "behold_product",
    "utilities": ROOT / "behold_utilities",
}
COMMON = ROOT / "behold_common"


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store"),
    )


def main() -> None:
    for path in list(ADDONS.values()) + [COMMON]:
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True)

    # Shared source of truth (vendored into each addon as common/).
    for name in (
        "brand.py",
        "draw_cache.py",
        "previews.py",
    ):
        copy_file(SRC / name, COMMON / name)
    copy_file(SRC / "studio" / "camera_ids.py", COMMON / "camera_ids.py")
    copy_file(SRC / "studio" / "light_ids.py", COMMON / "light_ids.py")
    copy_file(SRC / "studio" / "tones.py", COMMON / "tones.py")
    copy_file(SRC / "utilities" / "ids.py", COMMON / "utility_ids.py")
    copy_tree(SRC / "updates", COMMON / "updates")
    copy_tree(SRC / "icons", COMMON / "icons")

    # Studio
    studio = ADDONS["studio"]
    for name in (
        "fit.py",
        "world.py",
        "world_apply.py",
        "catcher.py",
        "catcher_apply.py",
        "bake.py",
        "bake_apply.py",
        "setup.py",
    ):
        copy_file(SRC / "studio" / name, studio / name)
    copy_tree(SRC / "assets", studio / "assets")

    # Lighting
    lighting = ADDONS["lighting"]
    for name in (
        "lights.py",
        "light_presets.py",
        "light_shape.py",
        "gobos.py",
        "gobo_apply.py",
        "ies.py",
        "ies_apply.py",
        "light_linking.py",
        "light_linking_apply.py",
    ):
        copy_file(SRC / "studio" / name, lighting / name)
    copy_tree(SRC / "light_draw", lighting / "light_draw")
    copy_tree(SRC / "ies", lighting / "ies")
    copy_tree(SRC / "assets", lighting / "assets")

    # Product
    product = ADDONS["product"]
    copy_tree(SRC / "product_import", product / "product_import")
    copy_tree(SRC / "cad", product / "cad")
    copy_tree(SRC / "materials", product / "materials")
    copy_tree(SRC / "shoot", product / "shoot")
    copy_file(SRC / "studio" / "cameras.py", product / "cameras.py")
    copy_file(SRC / "studio" / "dof.py", product / "dof.py")
    copy_file(SRC / "studio" / "dof_apply.py", product / "dof_apply.py")
    copy_tree(SRC / "assets", product / "assets")

    # Utilities
    utilities = ADDONS["utilities"]
    copy_tree(SRC / "utilities", utilities / "utilities")
    copy_tree(SRC / "assets", utilities / "assets")

    print("copied suite packages")


if __name__ == "__main__":
    main()
