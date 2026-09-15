# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD — product studio rendering for Blender."""

from __future__ import annotations

bl_info = {
    "name": "BEHOLD",
    "author": "AMIRITE.studio",
        "version": (1, 5, 1),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > BEHOLD | Shift+Alt+B pie",
    "description": "Product studio lighting and rendering — BEHOLD by AMIRITE.studio",
    "category": "Render",
    "doc_url": "https://github.com/wckdboy/BEHOLD",
}

from . import previews
from . import preferences
from . import properties
from . import updates
from . import ui
from .light_draw import operators as light_draw_ops
from .materials import blenderkit_bridge, local_rack
from .cad import operators as cad_ops
from .product_import import operators as product_ops
from .shoot import operators as shoot_ops
from .studio import operators as studio_ops
from . import utilities


_CORE_MODULES = (
    previews,
    properties,
    preferences,
    updates,
    studio_ops,
    local_rack,
    blenderkit_bridge,
    shoot_ops,
    light_draw_ops,
    cad_ops,
    product_ops,
    ui,
)
# Utilities is feature-flagged; keep it last and isolate load errors so a
# wall/eave helper cannot fail Install from Disk / enable.
_OPTIONAL_MODULES = (utilities,)
_MODULES = _CORE_MODULES + _OPTIONAL_MODULES


def register() -> None:
    for module in _CORE_MODULES:
        module.register()
    for module in _OPTIONAL_MODULES:
        try:
            module.register()
        except Exception:  # noqa: BLE001 — opt-in track must not block enable
            continue


def unregister() -> None:
    for module in reversed(_OPTIONAL_MODULES):
        try:
            module.unregister()
        except Exception:  # noqa: BLE001 — best-effort if register never ran
            continue
    for module in reversed(_CORE_MODULES):
        module.unregister()


if __name__ == "__main__":
    register()
