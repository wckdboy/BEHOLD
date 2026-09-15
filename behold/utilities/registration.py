# SPDX-License-Identifier: GPL-3.0-or-later
"""Register Utilities operators + panel only while the preference is on.

Operators and the panel are imported inside sync_registration when the flag
is on. A NameError in those modules cannot brick core enable.
"""

from __future__ import annotations

import bpy

from .flag import gated_ui_ids, show_utilities_panel

_registered = False


def _prefs_enabled() -> bool:
    from ..preferences import get_prefs

    try:
        return show_utilities_panel(get_prefs(bpy.context))
    except Exception:
        return False


def _classes():
    from .operators import CLASSES as OPERATOR_CLASSES
    from .panel import CLASSES as PANEL_CLASSES

    return OPERATOR_CLASSES + PANEL_CLASSES


def sync_registration(enabled: bool) -> None:
    """Register or unregister Utilities UI/operators to match the flag."""
    global _registered
    ids = gated_ui_ids(enabled=enabled)
    if enabled and ids and not _registered:
        for cls in _classes():
            bpy.utils.register_class(cls)
        _registered = True
        return
    if not enabled and _registered:
        for cls in reversed(_classes()):
            try:
                bpy.utils.unregister_class(cls)
            except RuntimeError:
                pass
        _registered = False


def register() -> None:
    sync_registration(_prefs_enabled())


def unregister() -> None:
    sync_registration(False)
