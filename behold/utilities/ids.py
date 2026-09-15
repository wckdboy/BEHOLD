# SPDX-License-Identifier: GPL-3.0-or-later
"""Utilities object names — no Blender import.

Walls and mount kits use the BEHOLD_Util_ prefix so they never count as the
imported product or the studio cyclorama.
"""

from __future__ import annotations

PREFIX = "BEHOLD"
UTIL_PREFIX = f"{PREFIX}_Util_"
COLLECTION_NAME = f"{PREFIX}_Utilities"
WALL_ROOT_NAME = f"{UTIL_PREFIX}Wall"
WALL_FACE_EMPTY = f"{UTIL_PREFIX}WallFace"
MOUNT_LEGS_ROOT = f"{UTIL_PREFIX}Mount_Legs"
MOUNT_BRACKET_ROOT = f"{UTIL_PREFIX}Mount_Bracket"
PRODUCT_SNAP_EMPTY = f"{UTIL_PREFIX}Snap"

WALL_LAYER_NAMES = {
    "exterior": f"{UTIL_PREFIX}Wall_Exterior",
    "insulation": f"{UTIL_PREFIX}Wall_Insulation",
    "interior": f"{UTIL_PREFIX}Wall_Interior",
}

CUSTOM_PROP = "BEHOLD_utility"
CUSTOM_KIND = "BEHOLD_utility_kind"


def _name_base(name: str) -> str:
    return name.split(".", 1)[0]


def is_utility_mesh_name(name: str) -> bool:
    return _name_base(name).startswith(UTIL_PREFIX)


def is_wall_name(name: str) -> bool:
    base = _name_base(name)
    return base == WALL_ROOT_NAME or base.startswith(f"{UTIL_PREFIX}Wall")
