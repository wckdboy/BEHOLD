# SPDX-License-Identifier: GPL-3.0-or-later
"""Soft-dependency helpers. Never import another BEHOLD add-on by Python name."""

from __future__ import annotations

from typing import Any

MISSING_STUDIO = "Install BEHOLD Studio for Build Studio"
MISSING_LIGHTING = "Install BEHOLD Lighting for lights"
MISSING_PRODUCT = "Install BEHOLD Product for Import, materials, cameras, and Shoot"
MISSING_UTILITIES = "Install BEHOLD Utilities for the Danish wall and mounts"

BUILD_STUDIO_OP = "behold.build_studio"
SEED_LIGHTS_OP = "behold.seed_studio_lights"
SEED_CAMERA_OP = "behold.seed_studio_camera"
APPLY_QUALITY_OP = "behold.apply_quality"
APPLY_RESOLUTION_OP = "behold.apply_resolution"
LOAD_HDRI_OP = "behold.load_hdri"
RESET_WORLD_OP = "behold.reset_world"
APPLY_STUDIO_LOOK_OP = "behold.apply_studio_look"
IMPORT_PRODUCT_OP = "behold.import_product"
ADD_LIGHT_OP = "behold.add_light"
ADD_CAMERA_OP = "behold.add_camera"
RENDER_STILL_OP = "behold.render_still"
LIGHT_DRAW_OP = "behold.light_draw"


def operator_exists(idname: str) -> bool:
    """True when ``bpy.ops.<idname>`` is registered."""
    try:
        import bpy
    except ImportError:
        return False
    try:
        path, name = idname.split(".", 1)
    except ValueError:
        return False
    try:
        getattr(getattr(bpy.ops, path), name)
    except AttributeError:
        return False
    return True


def try_operator(idname: str, **kwargs: Any) -> set[str] | None:
    """Invoke an operator if it exists. Returns the result set, or None."""
    if not operator_exists(idname):
        return None
    import bpy

    path, name = idname.split(".", 1)
    op = getattr(getattr(bpy.ops, path), name)
    try:
        return set(op(**kwargs))
    except Exception:  # noqa: BLE001 — missing add-on must not brick the caller
        return None
