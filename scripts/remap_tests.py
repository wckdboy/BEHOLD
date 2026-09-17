#!/usr/bin/env python3
"""Rewrite test file paths from the monolith onto the v2 suite packages."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

# Longer prefixes first.
REPLACEMENTS = [
    ("behold/product_import/", "behold_product/product_import/"),
    ("behold/materials/", "behold_product/materials/"),
    ("behold/cad/", "behold_product/cad/"),
    ("behold/shoot/", "behold_product/shoot/"),
    ("behold/light_draw/", "behold_lighting/light_draw/"),
    ("behold/utilities/", "behold_utilities/"),
    ("behold/ui/messages.py", "behold_common/messages.py"),
    ("behold/ui/flow.py", "behold_product/ui/flow.py"),
    ("behold/ui/chrome.py", "behold_product/ui/chrome.py"),
    ("behold/ui/scene_scan.py", "behold_product/ui/scene_scan.py"),
    ("behold/ui/pie.py", "behold_product/ui/pie.py"),
    ("behold/ui/__init__.py", "behold_product/ui/__init__.py"),
    ("behold/ui/panels.py", "behold_product/ui/panels.py"),
    ("behold/updates/", "behold_common/updates/"),
    ("behold/draw_cache.py", "behold_common/draw_cache.py"),
    ("behold/brand.py", "behold_common/brand.py"),
    ("behold/studio/world.py", "behold_studio/world.py"),
    ("behold/studio/world_apply.py", "behold_studio/world_apply.py"),
    ("behold/studio/setup.py", "behold_studio/setup.py"),
    ("behold/studio/catcher.py", "behold_studio/catcher.py"),
    ("behold/studio/catcher_apply.py", "behold_studio/catcher_apply.py"),
    ("behold/studio/bake.py", "behold_studio/bake.py"),
    ("behold/studio/bake_apply.py", "behold_studio/bake_apply.py"),
    ("behold/studio/fit.py", "behold_studio/fit.py"),
    ("behold/studio/tones.py", "behold_common/tones.py"),
    ("behold/studio/camera_ids.py", "behold_common/camera_ids.py"),
    ("behold/studio/light_ids.py", "behold_common/light_ids.py"),
    ("behold/studio/cameras.py", "behold_product/cameras.py"),
    ("behold/studio/dof.py", "behold_product/dof.py"),
    ("behold/studio/dof_apply.py", "behold_product/dof_apply.py"),
    ("behold/studio/lights.py", "behold_lighting/lights.py"),
    ("behold/studio/gobos.py", "behold_lighting/gobos.py"),
    ("behold/studio/gobo_apply.py", "behold_lighting/gobo_apply.py"),
    ("behold/studio/ies.py", "behold_lighting/ies.py"),
    ("behold/studio/ies_apply.py", "behold_lighting/ies_apply.py"),
    ("behold/studio/light_presets.py", "behold_lighting/light_presets.py"),
    ("behold/studio/light_shape.py", "behold_lighting/light_shape.py"),
    ("behold/studio/light_linking.py", "behold_lighting/light_linking.py"),
    ("behold/studio/light_linking_apply.py", "behold_lighting/light_linking_apply.py"),
    ("behold/studio/operators.py", "behold_lighting/operators.py"),
    ("behold.product_import", "behold_product.product_import"),
    ("behold.materials", "behold_product.materials"),
    ("behold.cad.", "behold_product.cad."),
    ("behold.cad\"", "behold_product.cad\""),
    ("behold.shoot.", "behold_product.shoot."),
    ("behold.ui.messages", "behold_common.messages"),
    ("behold.ui.flow", "behold_product.ui.flow"),
    ("behold.ui.scene_scan", "behold_product.ui.scene_scan"),
    ("behold.updates.", "behold_common.updates."),
    ("behold.studio.catcher", "behold_studio.catcher"),
    ("behold.utilities.", "behold_utilities."),
    ("behold.utilities\"", "behold_utilities\""),
    ('"behold.brand"', '"behold_common.brand"'),
    ("behold/icons/behold_icon.png", "behold_product/icons/behold_icon.png"),
    ("behold/__init__.py", "behold_product/__init__.py"),
    ("behold/preferences.py", "behold_product/preferences.py"),
    ("behold/properties.py", "behold_product/properties.py"),
]


def main() -> None:
    for path in TESTS.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in REPLACEMENTS:
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")
            print(f"updated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
