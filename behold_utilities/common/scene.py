# SPDX-License-Identifier: GPL-3.0-or-later
"""Per-add-on scene PropertyGroup accessors."""

from __future__ import annotations

from typing import Any

STUDIO_POINTER = "behold_studio"
LIGHTING_POINTER = "behold_lighting"
PRODUCT_POINTER = "behold_product"
UTILITIES_POINTER = "behold_utilities"


def studio(scene: Any):
    return getattr(scene, STUDIO_POINTER, None)


def lighting(scene: Any):
    return getattr(scene, LIGHTING_POINTER, None)


def product(scene: Any):
    return getattr(scene, PRODUCT_POINTER, None)


def utilities(scene: Any):
    return getattr(scene, UTILITIES_POINTER, None)
