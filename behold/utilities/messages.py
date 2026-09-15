# SPDX-License-Identifier: GPL-3.0-or-later
"""Utilities operator copy — no Blender import."""

from __future__ import annotations

WARNING = "WARNING"
ERROR = "ERROR"

NO_UTILITIES = (
    "Utilities is off — enable Utilities panel in BEHOLD add-on preferences"
)
NO_WALL = "No Danish wall — Build Wall in Utilities, or select a wall mesh"
NO_PRODUCT = (
    "No balcony product — import a mesh or select the balcony, then Build Mount"
)
WALL_NEEDS_SIZE = "Wall width and height must be greater than zero"
UNKNOWN_STOREY = "Unknown storey preset — pick Foundation, Ground–2, or Top floors"
UNKNOWN_MOUNT = "Unknown mount method — pick Legs or L-bracket"

PREREQUISITE_MESSAGES = frozenset(
    {NO_UTILITIES, NO_WALL, NO_PRODUCT, WALL_NEEDS_SIZE, UNKNOWN_STOREY, UNKNOWN_MOUNT}
)


def report_type(message: str) -> str:
    if message in PREREQUISITE_MESSAGES:
        return WARNING
    return ERROR


def report_set(message: str) -> set[str]:
    return {report_type(message)}


def wall_built_message(storey_label: str, total_mm: float) -> str:
    return f"Built Danish wall ({storey_label}, {total_mm:.0f} mm)"


def mount_built_message(method_label: str) -> str:
    return f"Built {method_label} mount against the wall"


def scad_exported_message(path: str) -> str:
    shown = path.strip() or "a text block"
    return f"Wrote wall stack OpenSCAD to {shown}"
