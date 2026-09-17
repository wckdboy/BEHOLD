# SPDX-License-Identifier: GPL-3.0-or-later
"""Utilities panel and operator ids — no Blender import."""

PANEL_ID = "BEHOLD_PT_utilities"
OPERATOR_BUILD_WALL = "behold.build_danish_wall"
OPERATOR_BUILD_LEGS = "behold.build_balcony_legs"
OPERATOR_BUILD_BRACKET = "behold.build_balcony_bracket"
OPERATOR_BUILD_EAVE = "behold.build_eave_section"
OPERATOR_EXPORT_SCAD = "behold.export_wall_scad"

OPERATOR_IDS: tuple[str, ...] = (
    OPERATOR_BUILD_WALL,
    OPERATOR_BUILD_LEGS,
    OPERATOR_BUILD_BRACKET,
    OPERATOR_BUILD_EAVE,
    OPERATOR_EXPORT_SCAD,
)
