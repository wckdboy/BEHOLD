# SPDX-License-Identifier: GPL-3.0-or-later
"""Utilities ids — no Blender import.

The product-render N-panel (Import → Studio → Lights → Materials →
Cameras → Shoot → Advanced) never registers these. BEHOLD Utilities is
its own add-on; the panel is on whenever that zip is enabled. PREF_ID is
kept as the 1.6.0 migration name (`enable_utilities`).
"""

from __future__ import annotations

from typing import Any

DEFAULT_ENABLE_UTILITIES = True
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
    """Utilities is its own add-on — the panel is always on when this zip is enabled."""
    del prefs
    return True


def gated_ui_ids(*, enabled: bool) -> tuple[str, ...]:
    """Panel + operator ids registered only while the flag is on."""
    if not enabled:
        return ()
    return (PANEL_ID, *OPERATOR_IDS)
