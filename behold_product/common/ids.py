# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared object tags and name helpers — no Blender import required for names."""

from __future__ import annotations

from .camera_ids import (
    DEFAULT_FRAME_PADDING,
    DEFAULT_LENS_MM,
    DEFAULT_SENSOR_HEIGHT_MM,
    DEFAULT_SENSOR_WIDTH_MM,
    PRODUCT_VIEW_DIRECTION,
    STUDIO_CAMERA_NAME,
    STUDIO_MESH_BASES,
    bounds_center_size,
    clip_range,
    display_camera_name,
    frame_distance,
    is_behold_camera_name,
    is_studio_mesh_name,
    next_camera_name,
    product_camera_offset,
)
from .light_ids import (
    COLLECTION_NAME as STUDIO_COLLECTION_NAME,
    PREFIX,
    RESERVED_RIG,
    display_light_name,
    is_behold_light_name,
    next_indexed_name,
)
from .utility_ids import (
    COLLECTION_NAME as UTILITIES_COLLECTION_NAME,
    UTIL_PREFIX,
    is_utility_mesh_name,
)

PRODUCT_SOURCE_KEYS = ("BEHOLD_product_source", "BEHOLD_cad_source")


def is_behold_product(obj) -> bool:
    """True when the object was tagged by Import Product / CAD import."""
    return bool(obj.get("BEHOLD_product_source") or obj.get("BEHOLD_cad_source"))


def is_dressable_mesh_name(name: str) -> bool:
    """True for product meshes — skip cyclorama / catcher / utility kits."""
    if is_studio_mesh_name(name):
        return False
    return not is_utility_mesh_name(name)
