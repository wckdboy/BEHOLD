# SPDX-License-Identifier: GPL-3.0-or-later
"""Balcony mount kit layout — no Blender import.

Method A (Legs): front posts + base plates + rear wall brackets.
Method B (L-bracket): under-frame L with a diagonal brace.

Local space matches the Danish wall: exterior face at Y=0, balcony in +Y,
Z up, X along the facade.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, Never

MethodId = Literal["LEGS", "BRACKET"]

DEFAULT_WIDTH_M = 3.0
DEFAULT_DEPTH_M = 1.4
DEFAULT_LEG_HEIGHT_M = 2.5
DEFAULT_INSET_M = 0.15
POST_SECTION_M = 0.05
PLATE_SIZE_M = 0.16
PLATE_THICK_M = 0.012
BRACKET_ARM_M = 0.12
BRACKET_DROP_M = 0.10
L_VERTICAL_M = 0.36
L_HORIZONTAL_M = 0.42
L_SECTION_M = 0.04
MIN_SPAN_M = 0.5
MIN_DEPTH_M = 0.35
MIN_LEG_HEIGHT_M = 0.5

METHOD_LABELS: dict[MethodId, str] = {
    "LEGS": "Legs",
    "BRACKET": "L-bracket",
}


def method_enum_items() -> tuple[tuple[str, str, str], ...]:
    return (
        (
            "LEGS",
            "Legs",
            "Front posts with base plates and rear wall brackets",
        ),
        (
            "BRACKET",
            "L-bracket",
            "Under-frame L-bracket with a diagonal brace",
        ),
    )


def is_method(method: str) -> bool:
    return method in METHOD_LABELS


@dataclass(frozen=True)
class MountPart:
    name: str
    center: tuple[float, float, float]
    size: tuple[float, float, float]
    rotation_euler: tuple[float, float, float] = (0.0, 0.0, 0.0)


@dataclass(frozen=True)
class MountSpec:
    method: MethodId
    width_m: float
    depth_m: float
    deck_z: float
    ground_z: float
    inset_m: float = DEFAULT_INSET_M

    @property
    def method_label(self) -> str:
        return METHOD_LABELS[self.method]

    @property
    def leg_height(self) -> float:
        return max(self.deck_z - self.ground_z, MIN_LEG_HEIGHT_M)


def make_mount_spec(
    method: str,
    *,
    width_m: float,
    depth_m: float,
    deck_z: float,
    ground_z: float = 0.0,
    inset_m: float = DEFAULT_INSET_M,
) -> MountSpec:
    if method == "LEGS" or method == "BRACKET":
        typed: MethodId = method
    else:
        raise ValueError(f"unknown mount method: {method}")
    width = max(float(width_m), MIN_SPAN_M)
    depth = max(float(depth_m), MIN_DEPTH_M)
    inset = min(max(float(inset_m), 0.05), width * 0.4)
    deck = float(deck_z)
    ground = float(ground_z)
    if deck - ground < MIN_LEG_HEIGHT_M:
        deck = ground + MIN_LEG_HEIGHT_M
    return MountSpec(
        method=typed,
        width_m=width,
        depth_m=depth,
        deck_z=deck,
        ground_z=ground,
        inset_m=inset,
    )


def mount_spec_from_bounds(
    method: str,
    mins: tuple[float, float, float],
    maxs: tuple[float, float, float],
    *,
    leg_height_m: float = DEFAULT_LEG_HEIGHT_M,
) -> MountSpec:
    width = max(maxs[0] - mins[0], MIN_SPAN_M)
    depth = max(maxs[1] - mins[1], MIN_DEPTH_M)
    product_bottom = float(mins[2])
    ground = 0.0
    if product_bottom >= MIN_LEG_HEIGHT_M * 0.4:
        deck = product_bottom
    else:
        deck = max(float(leg_height_m), MIN_LEG_HEIGHT_M)
    return make_mount_spec(
        method,
        width_m=width,
        depth_m=depth,
        deck_z=deck,
        ground_z=ground,
    )


def _post_xs(spec: MountSpec) -> tuple[float, float]:
    half = spec.width_m * 0.5 - spec.inset_m
    return (-half, half)


def _legs_parts(spec: MountSpec) -> list[MountPart]:
    height = spec.leg_height
    post_z = spec.ground_z + height * 0.5
    front_y = spec.depth_m - POST_SECTION_M * 0.5
    plate_z = spec.ground_z + PLATE_THICK_M * 0.5
    bracket_y = BRACKET_ARM_M * 0.5
    bracket_z = spec.deck_z - BRACKET_DROP_M * 0.5
    parts: list[MountPart] = []
    for index, x in enumerate(_post_xs(spec), start=1):
        parts.append(
            MountPart(
                name=f"Leg_{index}",
                center=(x, front_y, post_z),
                size=(POST_SECTION_M, POST_SECTION_M, height),
            )
        )
        parts.append(
            MountPart(
                name=f"BasePlate_{index}",
                center=(x, front_y, plate_z),
                size=(PLATE_SIZE_M, PLATE_SIZE_M, PLATE_THICK_M),
            )
        )
        parts.append(
            MountPart(
                name=f"WallBracket_{index}",
                center=(x, bracket_y, spec.deck_z - PLATE_THICK_M * 0.5),
                size=(POST_SECTION_M * 1.4, BRACKET_ARM_M, PLATE_THICK_M),
            )
        )
        parts.append(
            MountPart(
                name=f"WallBracketDrop_{index}",
                center=(x, PLATE_THICK_M * 0.5, bracket_z),
                size=(POST_SECTION_M * 1.4, PLATE_THICK_M, BRACKET_DROP_M),
            )
        )
    return parts


def _brace_pose(
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
) -> tuple[tuple[float, float, float], tuple[float, float, float], float]:
    """Midpoint, Euler XYZ, length. Aligns local +Y to p0→p1."""
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    dz = p1[2] - p0[2]
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    mid = ((p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, (p0[2] + p1[2]) * 0.5)
    yaw = math.atan2(dx, dy)
    hyp = math.hypot(dx, dy)
    pitch = math.atan2(-dz, hyp) if hyp > 1e-9 or abs(dz) > 1e-9 else 0.0
    return mid, (pitch, 0.0, -yaw), length


def _bracket_parts(spec: MountSpec) -> list[MountPart]:
    parts: list[MountPart] = []
    for index, x in enumerate(_post_xs(spec), start=1):
        vert_z = spec.deck_z - L_VERTICAL_M * 0.5
        horz_y = L_HORIZONTAL_M * 0.5
        parts.append(
            MountPart(
                name=f"LVertical_{index}",
                center=(x, L_SECTION_M * 0.5, vert_z),
                size=(L_SECTION_M, L_SECTION_M, L_VERTICAL_M),
            )
        )
        parts.append(
            MountPart(
                name=f"LHorizontal_{index}",
                center=(x, horz_y, spec.deck_z - L_SECTION_M * 0.5),
                size=(L_SECTION_M, L_HORIZONTAL_M, L_SECTION_M),
            )
        )
        p0 = (x, L_HORIZONTAL_M - L_SECTION_M * 0.5, spec.deck_z - L_SECTION_M)
        p1 = (x, L_SECTION_M, spec.deck_z - L_VERTICAL_M + L_SECTION_M)
        mid, euler, length = _brace_pose(p0, p1)
        parts.append(
            MountPart(
                name=f"LBrace_{index}",
                center=mid,
                size=(L_SECTION_M * 0.7, length, L_SECTION_M * 0.7),
                rotation_euler=euler,
            )
        )
    return parts


def mount_parts(spec: MountSpec) -> list[MountPart]:
    if spec.method == "LEGS":
        return _legs_parts(spec)
    if spec.method == "BRACKET":
        return _bracket_parts(spec)
    unreachable: Never = spec.method
    raise RuntimeError(f"unhandled mount method: {unreachable}")
