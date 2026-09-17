# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD Utilities — Danish wall, balcony mounts, and eave sections — BEHOLD by AMIRITE.studio"""

from __future__ import annotations

bl_info = {
    "name": "BEHOLD Utilities",
    "author": "AMIRITE.studio",
    "version": (2, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > BEHOLD",
    "description": "Danish wall, balcony mounts, and eave sections — BEHOLD by AMIRITE.studio",
    "category": "Render",
    "doc_url": "https://github.com/wckdboy/BEHOLD",
}

from . import operators
from . import panel
from . import preferences
from . import properties
from .common import previews
from .common import updates

_MODULES = (
    previews,
    properties,
    preferences,
    updates,
    operators,
    panel,
)



def register() -> None:
    for module in _MODULES:
        module.register()


def unregister() -> None:
    for module in reversed(_MODULES):
        module.unregister()


if __name__ == "__main__":
    register()
