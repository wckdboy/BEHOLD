# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD — product studio rendering for Blender."""

from __future__ import annotations

bl_info = {
    "name": "BEHOLD",
    "author": "wckdboy",
    "version": (0, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > BEHOLD",
    "description": "Product studio, Light Draw, materials, and shoot tools",
    "category": "Render",
    "doc_url": "https://cursor.com/codebase/wckdboy/BEHOLD",
}

from . import properties
from . import ui
from .light_draw import operators as light_draw_ops
from .materials import blenderkit_bridge, local_rack
from .shoot import operators as shoot_ops
from .studio import operators as studio_ops


_MODULES = (
    properties,
    studio_ops,
    local_rack,
    blenderkit_bridge,
    shoot_ops,
    light_draw_ops,
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
