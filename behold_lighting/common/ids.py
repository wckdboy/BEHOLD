# SPDX-License-Identifier: GPL-3.0-or-later
"""Product tags and dressable-mesh names — no Blender import."""

from __future__ import annotations

from .camera_ids import is_studio_mesh_name
from .utility_ids import is_utility_mesh_name

PRODUCT_SOURCE_KEYS = ("BEHOLD_product_source", "BEHOLD_cad_source")


def is_behold_product(obj) -> bool:
    """True when the object was tagged by Import Product / CAD import."""
    return bool(obj.get("BEHOLD_product_source") or obj.get("BEHOLD_cad_source"))


def is_dressable_mesh_name(name: str) -> bool:
    """True for product meshes — skip cyclorama / catcher / utility kits."""
    if is_studio_mesh_name(name):
        return False
    return not is_utility_mesh_name(name)
