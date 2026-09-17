# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene-level BEHOLD Utilities settings."""

from __future__ import annotations

import bpy
from bpy.props import PointerProperty
from bpy.types import Scene

from .settings import BEHOLDUtilitiesSettings

CLASSES = (BEHOLDUtilitiesSettings,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    Scene.behold_utilities = PointerProperty(type=BEHOLDUtilitiesSettings)


def unregister() -> None:
    del Scene.behold_utilities
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
