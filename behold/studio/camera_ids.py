# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD camera naming and product-framing math — no Blender import."""

from __future__ import annotations

import math
import re
from typing import Iterable

PREFIX = "BEHOLD"
STUDIO_CAMERA_NAME = f"{PREFIX}_Camera"
STUDIO_MESH_BASES = (f"{PREFIX}_Cyclorama", f"{PREFIX}_ShadowCatcher")

DEFAULT_LENS_MM = 85.0
DEFAULT_SENSOR_WIDTH_MM = 36.0
DEFAULT_SENSOR_HEIGHT_MM = 24.0
DEFAULT_FRAME_PADDING = 1.35

_INDEX_RE = re.compile(rf"^{re.escape(STUDIO_CAMERA_NAME)}_(\d+)$")
_PRODUCT_VIEW = (0.55, -0.78, 0.30)


def _unit(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    x, y, z = vector
    length = math.sqrt(x * x + y * y + z * z)
    if length <= 1e-9:
        return (0.0, -1.0, 0.0)
    return (x / length, y / length, z / length)


PRODUCT_VIEW_DIRECTION = _unit(_PRODUCT_VIEW)


def _name_base(name: str) -> str:
    return name.split(".", 1)[0]


def is_behold_camera_name(name: str) -> bool:
    base = _name_base(name)
    return base == STUDIO_CAMERA_NAME or bool(_INDEX_RE.match(base))


def is_studio_mesh_name(name: str) -> bool:
    return _name_base(name) in STUDIO_MESH_BASES


def display_camera_name(name: str) -> str:
    prefix = f"{PREFIX}_"
    if name.startswith(prefix):
        return name[len(prefix) :]
    return name


def next_camera_name(existing_names: Iterable[str]) -> str:
    bases = {_name_base(name) for name in existing_names}
    if STUDIO_CAMERA_NAME not in bases:
        return STUDIO_CAMERA_NAME
    highest = 0
    for base in bases:
        match = _INDEX_RE.match(base)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{STUDIO_CAMERA_NAME}_{highest + 1:03d}"


def horizontal_fov_rad(lens_mm: float, sensor_width_mm: float = DEFAULT_SENSOR_WIDTH_MM) -> float:
    return 2.0 * math.atan((sensor_width_mm * 0.5) / max(lens_mm, 0.01))


def vertical_fov_rad(lens_mm: float, sensor_height_mm: float = DEFAULT_SENSOR_HEIGHT_MM) -> float:
    return 2.0 * math.atan((sensor_height_mm * 0.5) / max(lens_mm, 0.01))


def frame_distance(
    size: float,
    *,
    lens_mm: float = DEFAULT_LENS_MM,
    sensor_width_mm: float = DEFAULT_SENSOR_WIDTH_MM,
    sensor_height_mm: float = DEFAULT_SENSOR_HEIGHT_MM,
    padding: float = DEFAULT_FRAME_PADDING,
) -> float:
    """Distance from target so a cube of `size` fills a full-frame sensor."""
    half = max(size, 0.1) * 0.5 * padding
    dist_h = half / math.tan(horizontal_fov_rad(lens_mm, sensor_width_mm) / 2.0)
    dist_v = half / math.tan(vertical_fov_rad(lens_mm, sensor_height_mm) / 2.0)
    return max(dist_h, dist_v, 0.1)


def product_camera_offset(
    size: float,
    *,
    lens_mm: float = DEFAULT_LENS_MM,
    sensor_width_mm: float = DEFAULT_SENSOR_WIDTH_MM,
    sensor_height_mm: float = DEFAULT_SENSOR_HEIGHT_MM,
    padding: float = DEFAULT_FRAME_PADDING,
) -> tuple[float, float, float]:
    distance = frame_distance(
        size,
        lens_mm=lens_mm,
        sensor_width_mm=sensor_width_mm,
        sensor_height_mm=sensor_height_mm,
        padding=padding,
    )
    dx, dy, dz = PRODUCT_VIEW_DIRECTION
    return (dx * distance, dy * distance, dz * distance)


def clip_range(size: float, distance: float) -> tuple[float, float]:
    span = max(size, distance, 0.1)
    start = max(span * 0.005, 0.001)
    end = max(span * 20.0, 100.0)
    return start, end


def bounds_center_size(
    mins: tuple[float, float, float],
    maxs: tuple[float, float, float],
) -> tuple[tuple[float, float, float], float]:
    center = (
        (mins[0] + maxs[0]) * 0.5,
        (mins[1] + maxs[1]) * 0.5,
        (mins[2] + maxs[2]) * 0.5,
    )
    size = max(maxs[0] - mins[0], maxs[1] - mins[1], maxs[2] - mins[2], 0.1)
    return center, size
