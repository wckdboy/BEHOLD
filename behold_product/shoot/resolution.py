# SPDX-License-Identifier: GPL-3.0-or-later
"""Catalog resolution presets — aspect × size → render resolution.

No Blender import. Square 1:1, Portrait 4:5, and Landscape 16:9 compose with
2048² / 1080p / 4K. Size is the long edge. Pixel aspect stays 1:1 (square
pixels); percentage 100 so the labeled size is the file size. Gobos / logo
are out of scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Never

AspectId = Literal["SQUARE", "PORTRAIT", "LANDSCAPE"]
SizeId = Literal["SQ2048", "HD1080", "UHD4K"]

DEFAULT_ASPECT: AspectId = "SQUARE"
DEFAULT_SIZE: SizeId = "SQ2048"

MIN_RESOLUTION = 4
RESOLUTION_PERCENTAGE = 100
PIXEL_ASPECT_X = 1.0
PIXEL_ASPECT_Y = 1.0

ASPECT_RATIO: dict[AspectId, tuple[int, int]] = {
    "SQUARE": (1, 1),
    "PORTRAIT": (4, 5),
    "LANDSCAPE": (16, 9),
}

SIZE_LONG_EDGE: dict[SizeId, int] = {
    "SQ2048": 2048,
    "HD1080": 1920,
    "UHD4K": 3840,
}

SIZE_LABEL: dict[SizeId, str] = {
    "SQ2048": "2048²",
    "HD1080": "1080p",
    "UHD4K": "4K",
}

ASPECT_LABEL: dict[AspectId, str] = {
    "SQUARE": "Square 1:1",
    "PORTRAIT": "Portrait 4:5",
    "LANDSCAPE": "Landscape 16:9",
}

NO_RENDER_SETTINGS = (
    "No render settings on this scene — pick a scene, then choose a size on Shoot"
)
RESOLUTION_FAILED = (
    "Could not apply that size — check Output Properties, then Apply Size"
)
UNKNOWN_ASPECT = (
    "Unknown aspect — pick Square 1:1, Portrait 4:5, or Landscape 16:9"
)
UNKNOWN_SIZE = "Unknown size — pick 2048², 1080p, or 4K"


@dataclass(frozen=True)
class ResolutionPlan:
    aspect: AspectId
    size: SizeId
    resolution_x: int
    resolution_y: int
    resolution_percentage: int
    pixel_aspect_x: float
    pixel_aspect_y: float

    def rna_pairs(self) -> tuple[tuple[str, object], ...]:
        return (
            ("resolution_x", self.resolution_x),
            ("resolution_y", self.resolution_y),
            ("resolution_percentage", self.resolution_percentage),
            ("pixel_aspect_x", self.pixel_aspect_x),
            ("pixel_aspect_y", self.pixel_aspect_y),
        )


def aspect_enum_items() -> tuple[tuple[str, str, str], ...]:
    return (
        ("SQUARE", "Square 1:1", "Square catalog still (1:1)"),
        ("PORTRAIT", "Portrait 4:5", "Portrait pack / social still (4:5)"),
        ("LANDSCAPE", "Landscape 16:9", "Widescreen / hero still (16:9)"),
    )


def size_enum_items() -> tuple[tuple[str, str, str], ...]:
    return (
        ("SQ2048", "2048²", "2048 px long edge — catalog square / pack shot"),
        ("HD1080", "1080p", "1920 px long edge — Full HD"),
        ("UHD4K", "4K", "3840 px long edge — UHD"),
    )


def is_aspect(value: str) -> bool:
    return value in ASPECT_RATIO


def is_size(value: str) -> bool:
    return value in SIZE_LONG_EDGE


def normalize_aspect(
    value: str, default: AspectId = DEFAULT_ASPECT
) -> AspectId:
    raw = (value or "").strip().upper()
    if raw == "SQUARE":
        return "SQUARE"
    if raw == "PORTRAIT":
        return "PORTRAIT"
    if raw == "LANDSCAPE":
        return "LANDSCAPE"
    if default == "SQUARE":
        return "SQUARE"
    if default == "PORTRAIT":
        return "PORTRAIT"
    if default == "LANDSCAPE":
        return "LANDSCAPE"
    unreachable: Never = default
    raise RuntimeError(f"unhandled aspect default: {unreachable}")


def normalize_size(value: str, default: SizeId = DEFAULT_SIZE) -> SizeId:
    raw = (value or "").strip().upper()
    if raw == "SQ2048":
        return "SQ2048"
    if raw == "HD1080":
        return "HD1080"
    if raw == "UHD4K":
        return "UHD4K"
    if default == "SQ2048":
        return "SQ2048"
    if default == "HD1080":
        return "HD1080"
    if default == "UHD4K":
        return "UHD4K"
    unreachable: Never = default
    raise RuntimeError(f"unhandled size default: {unreachable}")


def aspect_label(aspect: AspectId) -> str:
    if aspect == "SQUARE":
        return ASPECT_LABEL["SQUARE"]
    if aspect == "PORTRAIT":
        return ASPECT_LABEL["PORTRAIT"]
    if aspect == "LANDSCAPE":
        return ASPECT_LABEL["LANDSCAPE"]
    unreachable: Never = aspect
    raise RuntimeError(f"unhandled aspect: {unreachable}")


def size_label(size: SizeId) -> str:
    if size == "SQ2048":
        return SIZE_LABEL["SQ2048"]
    if size == "HD1080":
        return SIZE_LABEL["HD1080"]
    if size == "UHD4K":
        return SIZE_LABEL["UHD4K"]
    unreachable: Never = size
    raise RuntimeError(f"unhandled size: {unreachable}")


def long_edge_for(size: SizeId) -> int:
    if size == "SQ2048":
        return SIZE_LONG_EDGE["SQ2048"]
    if size == "HD1080":
        return SIZE_LONG_EDGE["HD1080"]
    if size == "UHD4K":
        return SIZE_LONG_EDGE["UHD4K"]
    unreachable: Never = size
    raise RuntimeError(f"unhandled size: {unreachable}")


def ratio_for(aspect: AspectId) -> tuple[int, int]:
    if aspect == "SQUARE":
        return ASPECT_RATIO["SQUARE"]
    if aspect == "PORTRAIT":
        return ASPECT_RATIO["PORTRAIT"]
    if aspect == "LANDSCAPE":
        return ASPECT_RATIO["LANDSCAPE"]
    unreachable: Never = aspect
    raise RuntimeError(f"unhandled aspect: {unreachable}")


def _clamp_px(value: int) -> int:
    return max(int(value), MIN_RESOLUTION)


def resolution_wh(aspect: str, size: str) -> tuple[int, int]:
    """Width × height. Size is the long edge; pixels stay square."""
    aid = normalize_aspect(aspect)
    sid = normalize_size(size)
    aw, ah = ratio_for(aid)
    long_edge = long_edge_for(sid)
    if aw == ah:
        return _clamp_px(long_edge), _clamp_px(long_edge)
    if aw > ah:
        width = long_edge
        height = round(long_edge * ah / aw)
        return _clamp_px(width), _clamp_px(height)
    height = long_edge
    width = round(long_edge * aw / ah)
    return _clamp_px(width), _clamp_px(height)


def unknown_aspect_message(aspect_id: str) -> str:
    shown = (aspect_id or "").strip()
    if not shown:
        return UNKNOWN_ASPECT
    return (
        f"Unknown aspect “{shown}” — "
        "pick Square 1:1, Portrait 4:5, or Landscape 16:9"
    )


def unknown_size_message(size_id: str) -> str:
    shown = (size_id or "").strip()
    if not shown:
        return UNKNOWN_SIZE
    return f"Unknown size “{shown}” — pick 2048², 1080p, or 4K"


def plan_resolution(aspect: str, size: str) -> ResolutionPlan | str:
    raw_aspect = (aspect or "").strip()
    raw_size = (size or "").strip()
    if raw_aspect and not is_aspect(raw_aspect.upper()):
        return unknown_aspect_message(raw_aspect)
    if raw_size and not is_size(raw_size.upper()):
        return unknown_size_message(raw_size)
    aid = normalize_aspect(raw_aspect)
    sid = normalize_size(raw_size)
    width, height = resolution_wh(aid, sid)
    return ResolutionPlan(
        aspect=aid,
        size=sid,
        resolution_x=width,
        resolution_y=height,
        resolution_percentage=RESOLUTION_PERCENTAGE,
        pixel_aspect_x=PIXEL_ASPECT_X,
        pixel_aspect_y=PIXEL_ASPECT_Y,
    )


def summary_label(aspect: str, size: str) -> str:
    plan = plan_resolution(aspect, size)
    if isinstance(plan, str):
        return plan
    return f"{plan.resolution_x} × {plan.resolution_y}"


def apply_message(plan: ResolutionPlan) -> str:
    return (
        f"{aspect_label(plan.aspect)} · {size_label(plan.size)} — "
        f"{plan.resolution_x} × {plan.resolution_y} (square pixels)"
    )
