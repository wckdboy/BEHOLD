# SPDX-License-Identifier: GPL-3.0-or-later
"""Register Utilities operators + panel. Always on in the suite add-on."""

from __future__ import annotations

import bpy


def _classes():
    from .operators import CLASSES as OPERATOR_CLASSES
    from .panel import CLASSES as PANEL_CLASSES

    return OPERATOR_CLASSES + PANEL_CLASSES


def register() -> None:
    for cls in _classes():
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes()):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
