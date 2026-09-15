# SPDX-License-Identifier: GPL-3.0-or-later
"""Danish storey wall stack math — no Blender import.

Thickness presets (user-stated Danish practice, millimetres):
- Foundation / bottom: 600–700 (default 700)
- Ground + floors 1–2: 480
- Top floors: 360

Layers are exterior masonry + insulation + interior plaster and always sum
to the storey total. MinAltan section drawings are reference only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Never

from .ids import WALL_LAYER_NAMES

StoreyId = Literal["FOUNDATION", "MID", "TOP"]

FOUNDATION_MIN_MM = 600.0
FOUNDATION_MAX_MM = 700.0
FOUNDATION_DEFAULT_MM = 700.0
MID_THICKNESS_MM = 480.0
TOP_THICKNESS_MM = 360.0

# Typical Danish facade brick (half) / full brick on foundation, plaster leaf.
DEFAULT_EXTERIOR_MID_MM = 108.0
DEFAULT_EXTERIOR_FOUNDATION_MM = 228.0
DEFAULT_INTERIOR_MM = 13.0

DEFAULT_WIDTH_M = 4.0
DEFAULT_HEIGHT_M = 2.8
DEFAULT_DOOR_WIDTH_M = 0.90
DEFAULT_DOOR_HEIGHT_M = 2.10

MM_PER_M = 1000.0

STOREY_LABELS: dict[StoreyId, str] = {
    "FOUNDATION": "Foundation",
    "MID": "Ground–2",
    "TOP": "Top floors",
}


def storey_enum_items() -> tuple[tuple[str, str, str], ...]:
    return (
        (
            "FOUNDATION",
            "Foundation",
            "Bottom / foundation wall, 600–700 mm (default 700)",
        ),
        (
            "MID",
            "Ground–2",
            "Ground floor and floors 1–2, 480 mm",
        ),
        (
            "TOP",
            "Top floors",
            "Upper storeys, 360 mm",
        ),
    )


def is_storey(storey: str) -> bool:
    return storey in STOREY_LABELS


def mm_to_m(mm: float) -> float:
    return mm / MM_PER_M


def m_to_mm(meters: float) -> float:
    return meters * MM_PER_M


def clamp_foundation_mm(value: float) -> float:
    return max(FOUNDATION_MIN_MM, min(FOUNDATION_MAX_MM, float(value)))


def _as_storey(storey: str) -> StoreyId:
    if storey == "FOUNDATION" or storey == "MID" or storey == "TOP":
        return storey
    raise ValueError(f"unknown storey: {storey}")


def thickness_mm_for_storey(
    storey: str,
    *,
    foundation_mm: float = FOUNDATION_DEFAULT_MM,
) -> float:
    typed = _as_storey(storey)
    if typed == "FOUNDATION":
        return clamp_foundation_mm(foundation_mm)
    if typed == "MID":
        return MID_THICKNESS_MM
    if typed == "TOP":
        return TOP_THICKNESS_MM
    unreachable: Never = typed
    raise RuntimeError(f"unhandled storey: {unreachable}")


def default_exterior_mm(storey: str) -> float:
    typed = _as_storey(storey)
    if typed == "FOUNDATION":
        return DEFAULT_EXTERIOR_FOUNDATION_MM
    if typed == "MID":
        return DEFAULT_EXTERIOR_MID_MM
    if typed == "TOP":
        return DEFAULT_EXTERIOR_MID_MM
    unreachable: Never = typed
    raise RuntimeError(f"unhandled storey: {unreachable}")


@dataclass(frozen=True)
class WallLayers:
    exterior_mm: float
    insulation_mm: float
    interior_mm: float

    @property
    def total_mm(self) -> float:
        return self.exterior_mm + self.insulation_mm + self.interior_mm

    @property
    def exterior_m(self) -> float:
        return mm_to_m(self.exterior_mm)

    @property
    def insulation_m(self) -> float:
        return mm_to_m(self.insulation_mm)

    @property
    def interior_m(self) -> float:
        return mm_to_m(self.interior_mm)

    @property
    def total_m(self) -> float:
        return mm_to_m(self.total_mm)


def resolve_layers(
    storey: str,
    *,
    total_mm: float | None = None,
    foundation_mm: float = FOUNDATION_DEFAULT_MM,
    exterior_mm: float = 0.0,
    interior_mm: float = 0.0,
) -> WallLayers:
    """Split a storey thickness into masonry + insulation + plaster.

    ``exterior_mm`` / ``interior_mm`` of 0 mean storey defaults. Insulation
    is the remainder so the three layers always sum to ``total_mm``.
    """
    total = float(total_mm) if total_mm is not None else thickness_mm_for_storey(
        storey, foundation_mm=foundation_mm
    )
    if total <= 0.0:
        raise ValueError("wall thickness must be greater than zero")
    ext = default_exterior_mm(storey) if exterior_mm <= 0.0 else float(exterior_mm)
    inn = DEFAULT_INTERIOR_MM if interior_mm <= 0.0 else float(interior_mm)
    ext = max(ext, 1.0)
    inn = max(inn, 1.0)
    if ext + inn >= total:
        # Keep a 1 mm insulation leaf rather than overshoot the storey total.
        scale = (total - 1.0) / (ext + inn)
        ext *= scale
        inn *= scale
    insulation = total - ext - inn
    return WallLayers(exterior_mm=ext, insulation_mm=insulation, interior_mm=inn)


@dataclass(frozen=True)
class BoxSpec:
    """Axis-aligned box in wall local space (metres). Exterior face at Y=0."""

    name: str
    layer: str
    min_xyz: tuple[float, float, float]
    size_xyz: tuple[float, float, float]


@dataclass(frozen=True)
class WallSpec:
    storey: StoreyId
    width_m: float
    height_m: float
    layers: WallLayers
    include_door: bool = False
    door_width_m: float = DEFAULT_DOOR_WIDTH_M
    door_height_m: float = DEFAULT_DOOR_HEIGHT_M

    @property
    def storey_label(self) -> str:
        return STOREY_LABELS[self.storey]


def make_wall_spec(
    storey: str,
    *,
    width_m: float = DEFAULT_WIDTH_M,
    height_m: float = DEFAULT_HEIGHT_M,
    foundation_mm: float = FOUNDATION_DEFAULT_MM,
    exterior_mm: float = 0.0,
    interior_mm: float = 0.0,
    include_door: bool = False,
    door_width_m: float = DEFAULT_DOOR_WIDTH_M,
    door_height_m: float = DEFAULT_DOOR_HEIGHT_M,
) -> WallSpec:
    typed = _as_storey(storey)
    width = max(float(width_m), 0.0)
    height = max(float(height_m), 0.0)
    layers = resolve_layers(
        typed,
        foundation_mm=foundation_mm,
        exterior_mm=exterior_mm,
        interior_mm=interior_mm,
    )
    door_w = min(max(float(door_width_m), 0.0), width * 0.9 if width else 0.0)
    door_h = min(max(float(door_height_m), 0.0), height * 0.95 if height else 0.0)
    return WallSpec(
        storey=typed,
        width_m=width,
        height_m=height,
        layers=layers,
        include_door=bool(include_door) and door_w > 0.05 and door_h > 0.05,
        door_width_m=door_w,
        door_height_m=door_h,
    )


def _layer_y_ranges(layers: WallLayers) -> dict[str, tuple[float, float]]:
    """Exterior occupies Y in [-ext, 0]; interior is deepest (−Y)."""
    ext = layers.exterior_m
    ins = layers.insulation_m
    inn = layers.interior_m
    return {
        "exterior": (-ext, 0.0),
        "insulation": (-(ext + ins), -ext),
        "interior": (-(ext + ins + inn), -(ext + ins)),
    }


def _boxes_for_layer(
    layer: str,
    name: str,
    *,
    width: float,
    height: float,
    y_min: float,
    y_max: float,
    include_door: bool,
    door_width: float,
    door_height: float,
) -> list[BoxSpec]:
    thickness = y_max - y_min
    if thickness <= 1e-9 or width <= 1e-9 or height <= 1e-9:
        return []
    half = width * 0.5
    if not include_door:
        return [
            BoxSpec(
                name=name,
                layer=layer,
                min_xyz=(-half, y_min, 0.0),
                size_xyz=(width, thickness, height),
            )
        ]

    door_half = door_width * 0.5
    parts: list[BoxSpec] = []
    left_w = half - door_half
    if left_w > 1e-6:
        parts.append(
            BoxSpec(
                name=f"{name}_L",
                layer=layer,
                min_xyz=(-half, y_min, 0.0),
                size_xyz=(left_w, thickness, height),
            )
        )
    right_w = half - door_half
    if right_w > 1e-6:
        parts.append(
            BoxSpec(
                name=f"{name}_R",
                layer=layer,
                min_xyz=(door_half, y_min, 0.0),
                size_xyz=(right_w, thickness, height),
            )
        )
    head_h = height - door_height
    if head_h > 1e-6:
        parts.append(
            BoxSpec(
                name=f"{name}_Head",
                layer=layer,
                min_xyz=(-door_half, y_min, door_height),
                size_xyz=(door_width, thickness, head_h),
            )
        )
    return parts


def wall_boxes(spec: WallSpec) -> list[BoxSpec]:
    """Solid boxes for the three layers, optionally split around a door."""
    ranges = _layer_y_ranges(spec.layers)
    boxes: list[BoxSpec] = []
    for layer in ("exterior", "insulation", "interior"):
        y_min, y_max = ranges[layer]
        boxes.extend(
            _boxes_for_layer(
                layer,
                WALL_LAYER_NAMES[layer],
                width=spec.width_m,
                height=spec.height_m,
                y_min=y_min,
                y_max=y_max,
                include_door=spec.include_door,
                door_width=spec.door_width_m,
                door_height=spec.door_height_m,
            )
        )
    return boxes
