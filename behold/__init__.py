# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD — product studio rendering for Blender."""

from __future__ import annotations

bl_info = {
    "name": "BEHOLD",
    "author": "AMIRITE.studio",
    "version": (0, 24, 0),
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


_MODULES = (
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


def register() -> None:
    for module in _MODULES:
        module.register()


def unregister() -> None:
    for module in reversed(_MODULES):
        module.unregister()


if __name__ == "__main__":
    register()
