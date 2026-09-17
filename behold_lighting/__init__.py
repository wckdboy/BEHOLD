# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD Lighting — Multi-light, Light Draw, gobo, IES, and linking — BEHOLD by AMIRITE.studio"""

from __future__ import annotations

bl_info = {
    "name": "BEHOLD Lighting",
    "author": "AMIRITE.studio",
    "version": (2, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > BEHOLD",
    "description": "Multi-light, Light Draw, gobo, IES, and linking — BEHOLD by AMIRITE.studio",
    "category": "Render",
    "doc_url": "https://github.com/wckdboy/BEHOLD",
}

from . import operators
from . import preferences
from . import properties
from . import ui
from .common import previews
from .common import updates
from .light_draw import operators as light_draw_ops

_MODULES = (
    previews,
    properties,
    preferences,
    updates,
    operators,
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
