# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD pie menu, keymap, and 3D View header shortcuts."""

from __future__ import annotations

import bpy
from bpy.types import Context, Menu, UILayout

from ..brand import PIE_KEY, PIE_MENU_ID
from ..preferences import get_prefs
from ..previews import mark_icon_kwargs

_keymaps: list[tuple] = []


class BEHOLD_MT_pie(Menu):
    bl_idname = PIE_MENU_ID
    bl_label = "BEHOLD"
    bl_description = "Import, Build Studio, Light Draw, Still, Turntable Setup"

    def draw(self, context: Context) -> None:
        del context
        pie = self.layout.menu_pie()
        # West, East, South, North, then NW / NE / SW / SE.
        pie.operator("behold.import_product", text="Import", icon="IMPORT")
        pie.operator("behold.render_still", text="Still", icon="RENDER_STILL")
        pie.operator("behold.light_draw", text="Light Draw", icon="LIGHT_AREA")
        build_icon = mark_icon_kwargs()
        if "icon_value" not in build_icon:
            build_icon = {"icon": "OUTLINER_OB_LIGHT"}
        pie.operator("behold.build_studio", text="Build Studio", **build_icon)
        pie.operator(
            "behold.setup_turntable",
            text="Turntable Setup",
            icon="RECOVER_LAST",
        )


def draw_view3d_header(self, context: Context) -> None:
    prefs = get_prefs(context)
    if prefs is not None and not prefs.show_header_shortcuts:
        return
    layout: UILayout = self.layout
    row = layout.row(align=True)
    pie = row.operator("wm.call_menu_pie", text="", **mark_icon_kwargs())
    pie.name = PIE_MENU_ID
    row.operator("behold.import_product", text="", icon="IMPORT")
    row.operator("behold.build_studio", text="", icon="OUTLINER_OB_LIGHT")
    row.operator("behold.render_still", text="", icon="RENDER_STILL")


CLASSES = (BEHOLD_MT_pie,)


def _register_keymaps() -> None:
    wm = bpy.context.window_manager
    if wm is None:
        return
    kc = wm.keyconfigs.addon
    if kc is None:
        return
    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    kmi = km.keymap_items.new("wm.call_menu_pie", PIE_KEY, "PRESS", shift=True, alt=True)
    kmi.properties.name = PIE_MENU_ID
    _keymaps.append((km, kmi))


def _unregister_keymaps() -> None:
    for km, kmi in _keymaps:
        km.keymap_items.remove(kmi)
    _keymaps.clear()


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_HT_header.append(draw_view3d_header)
    _register_keymaps()


def unregister() -> None:
    _unregister_keymaps()
    try:
        bpy.types.VIEW3D_HT_header.remove(draw_view3d_header)
    except ValueError:
        pass
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
