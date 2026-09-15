# SPDX-License-Identifier: GPL-3.0-or-later
"""Roof / eave section context — no Blender import.

MinAltan snit 6.01 presets (vejledende millimetres, not planning rules):
- UNDER_EAVE: balcony under the eaves (Altan under tagrende)
- OVER_EAVE: balcony over the eaves (Altan over tagrende)
- MURKRONE_REMOVED: under eaves with the wall crown gone
- RECESSED_SKUNK: over eaves with a recessed attic/skunk volume
- ROOF_INCLUSION: over eaves with the roof cut around the balcony

Local space matches the Danish wall: exterior face at Y=0, balcony in +Y,
Z up, X along the facade. Deck sits at ``deck_z`` (wall top).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Never

SectionId = Literal[
    "UNDER_EAVE",
    "OVER_EAVE",
    "MURKRONE_REMOVED",
    "RECESSED_SKUNK",
    "ROOF_INCLUSION",
]

# Vejledende millimetres from MinAltan A/S snit 6.01 (converted to metres).
DEFAULT_PROJECTION_M = 1.0
DEFAULT_PITCH_DEG = 45.0
DEFAULT_SLOPE_LENGTH_M = 3.5
GUTTER_WIDTH_M = 0.10
GUTTER_THICK_M = 0.08
ROOF_THICK_M = 0.08
DECK_THICK_M = 0.12
PARAPET_HEIGHT_M = 0.36
PARAPET_DEPTH_M = 0.18
CHEEK_THICK_M = 0.12
BACK_WALL_THICK_M = 0.12
MIN_WIDTH_M = 1.0
MIN_PROJECTION_M = 0.5
PITCH_MIN_DEG = 20.0
PITCH_MAX_DEG = 60.0

HEADROOM_UNDER_M = 0.60
HEADROOM_MURKRONE_M = 1.00
HEADROOM_OVER_M = 0.85
HEADROOM_SKUNK_M = 1.50
OVERHANG_UNDER_M = 0.15
OVERHANG_OVER_M = 0.20
RECESS_SKUNK_M = 0.50

SECTION_LABELS: dict[SectionId, str] = {
    "UNDER_EAVE": "Under eaves",
    "OVER_EAVE": "Over eaves",
    "MURKRONE_REMOVED": "Wall crown off",
    "RECESSED_SKUNK": "Recessed skunk",
    "ROOF_INCLUSION": "Roof inclusion",
}


def section_enum_items() -> tuple[tuple[str, str, str], ...]:
    return (
        (
            "UNDER_EAVE",
            "Under eaves",
            "Altan under tagrende — roof and gutter over the balcony",
        ),
        (
            "OVER_EAVE",
            "Over eaves",
            "Altan over tagrende — balcony at the cut eaves, roof behind",
        ),
        (
            "MURKRONE_REMOVED",
            "Wall crown off",
            "Under eaves with the murkrone / wall crown removed",
        ),
        (
            "RECESSED_SKUNK",
            "Recessed skunk",
            "Over eaves with a recessed skunk / attic volume (indraget skunk)",
        ),
        (
            "ROOF_INCLUSION",
            "Roof inclusion",
            "Over eaves with the roof cut around the balcony (inddragelse af tag)",
        ),
    )


def is_section(section: str) -> bool:
    return section in SECTION_LABELS


def clamp_pitch_deg(value: float) -> float:
    return max(PITCH_MIN_DEG, min(PITCH_MAX_DEG, float(value)))


def _as_section(section: str) -> SectionId:
    if (
        section == "UNDER_EAVE"
        or section == "OVER_EAVE"
        or section == "MURKRONE_REMOVED"
        or section == "RECESSED_SKUNK"
        or section == "ROOF_INCLUSION"
    ):
        return section
    raise ValueError(f"unknown eave section: {section}")


@dataclass(frozen=True)
class EavePart:
    name: str
    center: tuple[float, float, float]
    size: tuple[float, float, float]
    rotation_euler: tuple[float, float, float] = (0.0, 0.0, 0.0)
    layer: str = "roof"


@dataclass(frozen=True)
class EaveSpec:
    section: SectionId
    width_m: float
    deck_z: float
    pitch_deg: float = DEFAULT_PITCH_DEG
    projection_m: float = DEFAULT_PROJECTION_M

    @property
    def section_label(self) -> str:
        return SECTION_LABELS[self.section]

    @property
    def pitch_rad(self) -> float:
        return math.radians(self.pitch_deg)

    @property
    def under_eaves(self) -> bool:
        return self.section in {"UNDER_EAVE", "MURKRONE_REMOVED"}

    @property
    def has_parapet(self) -> bool:
        return self.section == "UNDER_EAVE"

    @property
    def has_cheeks(self) -> bool:
        return self.section == "ROOF_INCLUSION"

    @property
    def recess_m(self) -> float:
        return RECESS_SKUNK_M if self.section == "RECESSED_SKUNK" else 0.0

    @property
    def headroom_m(self) -> float:
        typed = self.section
        if typed == "UNDER_EAVE":
            return HEADROOM_UNDER_M
        if typed == "MURKRONE_REMOVED":
            return HEADROOM_MURKRONE_M
        if typed == "OVER_EAVE":
            return HEADROOM_OVER_M
        if typed == "RECESSED_SKUNK":
            return HEADROOM_SKUNK_M
        if typed == "ROOF_INCLUSION":
            return HEADROOM_MURKRONE_M
        unreachable: Never = typed
        raise RuntimeError(f"unhandled eave section: {unreachable}")

    @property
    def overhang_m(self) -> float:
        return OVERHANG_UNDER_M if self.under_eaves else OVERHANG_OVER_M

    @property
    def eave_y(self) -> float:
        """World-local Y of the gutter / roof eave line."""
        if self.under_eaves:
            return self.projection_m + self.overhang_m
        return self.overhang_m


def make_eave_spec(
    section: str,
    *,
    width_m: float,
    deck_z: float,
    pitch_deg: float = DEFAULT_PITCH_DEG,
    projection_m: float = DEFAULT_PROJECTION_M,
) -> EaveSpec:
    typed = _as_section(section)
    width = max(float(width_m), MIN_WIDTH_M)
    projection = max(float(projection_m), MIN_PROJECTION_M)
    return EaveSpec(
        section=typed,
        width_m=width,
        deck_z=float(deck_z),
        pitch_deg=clamp_pitch_deg(pitch_deg),
        projection_m=projection,
    )


def eave_spec_from_bounds(
    section: str,
    mins: tuple[float, float, float],
    maxs: tuple[float, float, float],
    *,
    deck_z: float,
    pitch_deg: float = DEFAULT_PITCH_DEG,
) -> EaveSpec:
    width = max(maxs[0] - mins[0], MIN_WIDTH_M)
    depth = max(maxs[1] - mins[1], MIN_PROJECTION_M)
    return make_eave_spec(
        section,
        width_m=width,
        deck_z=deck_z,
        pitch_deg=pitch_deg,
        projection_m=depth,
    )


def _roof_board(
    name: str,
    *,
    eave: tuple[float, float, float],
    width: float,
    slope_length: float,
    thick: float,
    pitch_deg: float,
) -> EavePart:
    """Roof slab from the eave inward (−Y) and up (+Z) along the pitch."""
    pitch = math.radians(pitch_deg)
    half = slope_length * 0.5
    mid = (
        eave[0],
        eave[1] - math.cos(pitch) * half,
        eave[2] + math.sin(pitch) * half,
    )
    # Rx(π − pitch) maps local +Y to world (0, −cos(pitch), sin(pitch)).
    theta = math.pi - pitch
    return EavePart(
        name=name,
        center=mid,
        size=(width, slope_length, thick),
        rotation_euler=(theta, 0.0, 0.0),
        layer="roof",
    )


def _deck_part(spec: EaveSpec) -> EavePart:
    y_min = -spec.recess_m
    y_max = spec.projection_m
    depth = y_max - y_min
    return EavePart(
        name="Deck",
        center=(0.0, y_min + depth * 0.5, spec.deck_z - DECK_THICK_M * 0.5),
        size=(spec.width_m, depth, DECK_THICK_M),
        layer="deck",
    )


def _gutter_part(spec: EaveSpec, eave_z: float) -> EavePart:
    return EavePart(
        name="Gutter",
        center=(0.0, spec.eave_y, eave_z),
        size=(spec.width_m, GUTTER_WIDTH_M, GUTTER_THICK_M),
        layer="gutter",
    )


def _parapet_part(spec: EaveSpec) -> EavePart:
    return EavePart(
        name="Parapet",
        center=(
            0.0,
            -PARAPET_DEPTH_M * 0.5,
            spec.deck_z + PARAPET_HEIGHT_M * 0.5,
        ),
        size=(spec.width_m, PARAPET_DEPTH_M, PARAPET_HEIGHT_M),
        layer="masonry",
    )


def _back_wall_part(spec: EaveSpec) -> EavePart:
    y = -spec.recess_m - BACK_WALL_THICK_M * 0.5
    return EavePart(
        name="BackWall",
        center=(0.0, y, spec.deck_z + spec.headroom_m * 0.5),
        size=(spec.width_m, BACK_WALL_THICK_M, spec.headroom_m),
        layer="masonry",
    )


def _cheek_parts(spec: EaveSpec) -> list[EavePart]:
    half = spec.width_m * 0.5 - CHEEK_THICK_M * 0.5
    z = spec.deck_z + spec.headroom_m * 0.5
    y = spec.projection_m * 0.5
    parts: list[EavePart] = []
    for name, x in (("Cheek_L", -half), ("Cheek_R", half)):
        parts.append(
            EavePart(
                name=name,
                center=(x, y, z),
                size=(CHEEK_THICK_M, spec.projection_m, spec.headroom_m),
                layer="masonry",
            )
        )
    return parts


def eave_parts(spec: EaveSpec) -> list[EavePart]:
    """Solid boxes for the selected snit preset."""
    typed = spec.section
    eave_z = spec.deck_z + spec.headroom_m
    if spec.under_eaves and spec.has_parapet:
        eave_z = spec.deck_z + PARAPET_HEIGHT_M + spec.headroom_m * 0.25
    parts: list[EavePart] = [
        _deck_part(spec),
        _gutter_part(spec, eave_z),
        _roof_board(
            "Roof",
            eave=(0.0, spec.eave_y, eave_z),
            width=spec.width_m,
            slope_length=DEFAULT_SLOPE_LENGTH_M,
            thick=ROOF_THICK_M,
            pitch_deg=spec.pitch_deg,
        ),
    ]
    if spec.has_parapet:
        parts.append(_parapet_part(spec))
    if not spec.under_eaves:
        parts.append(_back_wall_part(spec))
    if spec.has_cheeks:
        parts.extend(_cheek_parts(spec))
    if typed == "UNDER_EAVE" or typed == "OVER_EAVE" or typed == "MURKRONE_REMOVED" or typed == "RECESSED_SKUNK" or typed == "ROOF_INCLUSION":
        return parts
    unreachable: Never = typed
    raise RuntimeError(f"unhandled eave section: {unreachable}")
