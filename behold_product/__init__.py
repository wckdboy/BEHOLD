# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD Product — Import, materials, cameras, and Shoot — BEHOLD by AMIRITE.studio"""

from __future__ import annotations

bl_info = {
    "name": "BEHOLD Product",
    "author": "AMIRITE.studio",
    "version": (2, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > BEHOLD",
    "description": "Import, materials, cameras, and Shoot — BEHOLD by AMIRITE.studio",
    "category": "Render",
    "doc_url": "https://github.com/wckdboy/BEHOLD",
}

from . import cameras_ops
from . import preferences
from . import properties
from .cad import operators as cad_ops
from .common import previews
from .common import updates
from .materials import blenderkit_bridge, local_rack
from .product_import import operators as product_ops
from .shoot import operators as shoot_ops
from . import ui

_MODULES = (
    previews,
    properties,
    preferences,
    updates,
    local_rack,
    blenderkit_bridge,
    cameras_ops,
    shoot_ops,
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
