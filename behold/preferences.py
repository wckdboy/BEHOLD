# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD add-on preferences — branding, docs, lean scene defaults."""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty
from bpy.types import AddonPreferences, Context, UILayout

from .brand import (
    DOCS_URL,
    PRODUCT_CREDIT,
    PRODUCT_NAME,
    PRODUCT_TAGLINE,
    RELEASES_URL,
)


def addon_id() -> str:
    """Classic `behold` or Blender 4.2+ extension `bl_ext.<repo>.behold`."""
    pkg = __package__ or "behold"
    parts = pkg.split(".")
    if parts[0] == "bl_ext" and len(parts) >= 3:
        return ".".join(parts[:3])
    return parts[0]


def get_prefs(context: Context):
    addons = context.preferences.addons
    addon = addons.get(addon_id())
    if addon is None:
        addon = addons.get("behold")
    if addon is None:
        return None
    return addon.preferences


class BEHOLDAddonPreferences(AddonPreferences):
    bl_idname = addon_id()

    show_header_shortcuts: BoolProperty(
        name="3D View header shortcuts",
        description="Show BEHOLD pie + Import / Build / Still on the 3D Viewport header",
        default=True,
    )
    show_flow_strip: BoolProperty(
        name="Workflow strip",
        description="Show Import → Studio → Dress → Shoot on the BEHOLD sidebar",
        default=True,
    )

    def draw(self, context: Context) -> None:
        layout = self.layout
        _draw_branding(layout)
        _draw_links(layout)
        _draw_chrome_toggles(layout, self)
        _draw_scene_defaults(layout, context)


def _draw_branding(layout: UILayout) -> None:
    box = layout.box()
    box.label(text=PRODUCT_NAME, icon="RENDER_STILL")
    box.label(text=PRODUCT_CREDIT)
    box.label(text=PRODUCT_TAGLINE)


def _draw_links(layout: UILayout) -> None:
    row = layout.row(align=True)
    row.operator("wm.url_open", text="Docs", icon="HELP").url = DOCS_URL
    row.operator("wm.url_open", text="Releases", icon="URL").url = RELEASES_URL


def _draw_chrome_toggles(layout: UILayout, prefs: AddonPreferences) -> None:
    box = layout.box()
    box.label(text="Chrome", icon="PREFERENCES")
    box.prop(prefs, "show_flow_strip")
    box.prop(prefs, "show_header_shortcuts")


def _draw_scene_defaults(layout: UILayout, context: Context) -> None:
    settings = getattr(context.scene, "behold", None)
    if settings is None:
        return
    box = layout.box()
    box.label(text="This scene", icon="SCENE_DATA")
    box.prop(settings, "import_auto_studio")
    box.prop(settings, "import_auto_material_assist")
    box.prop(settings, "render_quality", text="Quality")


CLASSES = (BEHOLDAddonPreferences,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
