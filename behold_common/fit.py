# SPDX-License-Identifier: GPL-3.0-or-later
"""Cyclorama auto-fit math — no Blender import.

Build Studio used to take ``size = max(width, depth, height)`` and pass that as
``make_cyclorama`` radius. Floor then became ``radius * 2.5`` and the wall
``radius * 1.8``. A long bar and a tall tower share the same max-extent so the
sweep either clipped the footprint (wide / diagonal corners) or looked cramped
on the wall, and artists scaled by hand.

Fit is derived from the product world AABB:

1. Horizontal span = max(width, depth, XY diagonal). The diagonal is always
   at least ``max(width, depth)``; taking the max documents both terms so a
   square's corners are covered, not just the axis length.
2. Floor edge = span * margin (default 2.0, Advanced 1.5–2.5×), and at least
   ``height * 0.75`` so a tall part still sits on a usable pad.
3. Wall height = height * headroom (default 1.75), and at least a fraction of
   the floor so a flat sheet still gets a visible sweep.
4. ``rig_size`` scales lights so Key / Fill / Rim sit outside the floor
   half-extent (historical offsets are ~1.4–1.8 × size).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

MIN_EXTENT = 0.1
DEFAULT_MARGIN = 2.0
MIN_MARGIN = 1.0
MAX_MARGIN = 4.0
DEFAULT_HEADROOM = 1.75
FLOOR_FROM_HEIGHT = 0.75
WALL_FROM_FLOOR = 0.4
BEVEL_FROM_FLOOR = 0.12
BEVEL_FROM_WALL = 0.28
FLOOR_FROM_RADIUS = 2.5
RIG_FROM_FLOOR = 2.0
RIG_FROM_WALL = 1.6

# Build Studio light offsets, in units of rig_size, from product center.
KEY_OFFSET = (-1.4, -1.6, 1.8)
FILL_OFFSET = (1.6, -1.1, 1.0)
RIM_OFFSET = (0.2, 1.8, 1.4)


@dataclass(frozen=True)
class CycloramaFit:
    width: float
    depth: float
    height: float
    margin: float
    headroom: float
    horizontal_span: float
    floor_size: float
    wall_height: float
    bevel_width: float
    radius: float
    rig_size: float
    catcher_size: float
    product_size: float

    def scaled_offset(self, factors: tuple[float, float, float]) -> tuple[float, float, float]:
        scale = self.rig_size
        return (factors[0] * scale, factors[1] * scale, factors[2] * scale)


def clamp_margin(margin: float) -> float:
    value = float(margin)
    if math.isnan(value) or math.isinf(value):
        return DEFAULT_MARGIN
    return min(MAX_MARGIN, max(MIN_MARGIN, value))


def clamp_headroom(headroom: float) -> float:
    value = float(headroom)
    if math.isnan(value) or math.isinf(value) or value <= 0.0:
        return DEFAULT_HEADROOM
    return min(4.0, max(1.0, value))


def _positive_extent(value: float) -> float:
    extent = float(value)
    if math.isnan(extent) or math.isinf(extent) or extent <= 0.0:
        return MIN_EXTENT
    return max(extent, MIN_EXTENT)


def extents_from_aabb(
    mins: tuple[float, float, float],
    maxs: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Width (X), depth (Y), height (Z) from a world-space AABB."""
    return (
        max(maxs[0] - mins[0], 0.0),
        max(maxs[1] - mins[1], 0.0),
        max(maxs[2] - mins[2], 0.0),
    )


def horizontal_span(width: float, depth: float) -> float:
    """Larger of axis length and XY diagonal (diagonal always wins)."""
    axis = max(width, depth)
    diagonal = math.hypot(width, depth)
    return max(axis, diagonal, MIN_EXTENT)


def fit_cyclorama(
    width: float,
    depth: float,
    height: float,
    margin: float = DEFAULT_MARGIN,
    headroom: float = DEFAULT_HEADROOM,
) -> CycloramaFit:
    """Return cyclorama / catcher / light-rig sizes for a product AABB."""
    width = _positive_extent(width)
    depth = _positive_extent(depth)
    height = _positive_extent(height)
    margin = clamp_margin(margin)
    headroom = clamp_headroom(headroom)

    span = horizontal_span(width, depth)
    floor_size = max(span * margin, height * FLOOR_FROM_HEIGHT, MIN_EXTENT)
    wall_height = max(height * headroom, floor_size * WALL_FROM_FLOOR, MIN_EXTENT)
    bevel_width = min(floor_size * BEVEL_FROM_FLOOR, wall_height * BEVEL_FROM_WALL)
    bevel_width = max(bevel_width, MIN_EXTENT * 0.2)
    radius = floor_size / FLOOR_FROM_RADIUS
    product_size = max(width, depth, height, MIN_EXTENT)
    rig_size = max(floor_size / RIG_FROM_FLOOR, wall_height / RIG_FROM_WALL, product_size)
    catcher_size = floor_size

    return CycloramaFit(
        width=width,
        depth=depth,
        height=height,
        margin=margin,
        headroom=headroom,
        horizontal_span=span,
        floor_size=floor_size,
        wall_height=wall_height,
        bevel_width=bevel_width,
        radius=radius,
        rig_size=rig_size,
        catcher_size=catcher_size,
        product_size=product_size,
    )


def fit_from_aabb(
    mins: tuple[float, float, float],
    maxs: tuple[float, float, float],
    margin: float = DEFAULT_MARGIN,
    headroom: float = DEFAULT_HEADROOM,
) -> CycloramaFit:
    width, depth, height = extents_from_aabb(mins, maxs)
    return fit_cyclorama(width, depth, height, margin=margin, headroom=headroom)


def xy_outside_floor(offset: tuple[float, float, float], floor_size: float) -> bool:
    """True when an XY offset sits outside the cyclorama floor rectangle."""
    half = floor_size * 0.5
    return abs(offset[0]) > half or abs(offset[1]) > half
