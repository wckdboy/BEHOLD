# SPDX-License-Identifier: GPL-3.0-or-later
"""Utilities feature flag — no Blender import.

Default OFF. The product-render N-panel (Import → Studio → Lights →
Materials → Cameras → Shoot → Advanced) never lists these ids. When the
preference is on, the Utilities panel and operators register as extras.
"""

from __future__ import annotations

from typing import Any

DEFAULT_ENABLE_UTILITIES = False
PREF_ID = "enable_utilities"
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


def show_utilities_panel(prefs: Any | None) -> bool:
    """True when the add-on preference enables the Utilities N-panel."""
    if prefs is None:
        return False
    return bool(getattr(prefs, PREF_ID, DEFAULT_ENABLE_UTILITIES))


def gated_ui_ids(*, enabled: bool) -> tuple[str, ...]:
    """Panel + operator ids registered only while the flag is on."""
    if not enabled:
        return ()
    return (PANEL_ID, *OPERATOR_IDS)
