# SPDX-License-Identifier: GPL-3.0-or-later
"""Official mark via bpy.utils.previews — loaded on register."""

from __future__ import annotations

import bpy
import bpy.utils.previews
from bpy.types import UILayout

from .brand import (
    HERO_ICON,
    ICON_LOGO_ID,
    ICON_LOGO_PATH,
    ICON_MARK_ID,
    ICON_MARK_PATH,
)

_preview_collection = None


def icon_id(name: str = ICON_MARK_ID) -> int:
    """Preview icon_id for N-panel / pie / operators, or 0 if unloaded."""
    if _preview_collection is None:
        return 0
    preview = _preview_collection.get(name)
    if preview is None:
        return 0
    return int(preview.icon_id)


def mark_icon_kwargs() -> dict[str, int | str]:
    """Keyword args for layout.operator / label: custom mark or built-in fallback."""
    mark = icon_id()
    if mark:
        return {"icon_value": mark}
    return {"icon": HERO_ICON}


def draw_mark_label(layout: UILayout, text: str) -> None:
    kwargs = mark_icon_kwargs()
    layout.label(text=text, **kwargs)


def register() -> None:
    global _preview_collection
    if _preview_collection is not None:
        return
    pcoll = bpy.utils.previews.new()
    if ICON_MARK_PATH.is_file():
        pcoll.load(ICON_MARK_ID, str(ICON_MARK_PATH), "IMAGE")
    if ICON_LOGO_PATH.is_file():
        pcoll.load(ICON_LOGO_ID, str(ICON_LOGO_PATH), "IMAGE")
    _preview_collection = pcoll


def unregister() -> None:
    global _preview_collection
    if _preview_collection is None:
        return
    bpy.utils.previews.remove(_preview_collection)
    _preview_collection = None
