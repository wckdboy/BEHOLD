# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD Studio N-panel."""

from __future__ import annotations

import bpy
from bpy.types import Context, Panel, UILayout

from ..common.chrome import draw_empty_card, draw_parked_heading, draw_section_icon
from ..common.deps import IMPORT_PRODUCT_OP, operator_exists
from ..common.messages import NO_MESH_SELECTED
from .flow_ids import SECTION_ICONS

# Re-exported draw helpers used by tests that read this module.


def _settings(context: Context):
    return context.scene.behold_studio


def draw_studio_first_ship(layout: UILayout, context: Context) -> None:
    """Backdrop White / Grey / Black + Build, Catcher, compact HDRI, compact Bake HDRI."""
    settings = _settings(context)
    card = layout.box()
    card.prop(settings, "studio_backdrop_tone", text="Backdrop", expand=True)
    row = card.row(align=True)
    row.operator("behold.build_studio", text="Build", icon="OUTLINER_OB_LIGHT")
    row.prop(settings, "include_shadow_catcher", text="Catcher", toggle=True)
    draw_studio_hdri(layout, context)
    draw_studio_bake(layout, context)


def draw_studio_hdri(layout: UILayout, context: Context) -> None:
    """World HDRI: load, strength, Z rotation, optional reflections-only."""
    settings = _settings(context)
    card = layout.box()
    card.label(text="HDRI", icon="WORLD")
    card.prop(settings, "hdri_filepath", text="")
    row = card.row(align=True)
    row.operator("behold.load_hdri", text="Load", icon="FILE_IMAGE")
    row.operator("behold.reset_world", text="Reset", icon="LOOP_BACK")
    card.prop(settings, "hdri_strength", text="Strength")
    card.prop(settings, "hdri_rotation", text="Rotation")
    card.prop(settings, "hdri_reflections_only", text="Reflections only")
    if settings.hdri_reflections_only:
        card.prop(settings, "hdri_background_strength", text="Background")


def draw_studio_bake(layout: UILayout, context: Context) -> None:
    """Bake studio lights to an equirectangular HDR/EXR (1K/2K)."""
    settings = _settings(context)
    card = layout.box()
    card.label(text="Bake HDRI", icon="WORLD")
    card.prop(settings, "bake_hdri_filepath", text="")
    row = card.row(align=True)
    row.prop(settings, "bake_hdri_resolution", text="Size", expand=True)
    row = card.row(align=True)
    row.prop(settings, "bake_hdri_include_world", text="Include world")
    row.prop(settings, "bake_hdri_apply", text="Apply after bake")
    card.operator("behold.bake_hdri", text="Bake HDRI", icon="RENDER_STILL")


def draw_studio_parked(layout: UILayout, context: Context) -> None:
    """Backdrop type, catcher apply, studio margin."""
    settings = _settings(context)
    selected = any(obj.type == "MESH" for obj in context.selected_objects)
    if not selected:
        box = layout.box()
        box.label(text=NO_MESH_SELECTED, icon="INFO")
        if operator_exists(IMPORT_PRODUCT_OP):
            box.operator(IMPORT_PRODUCT_OP, icon="IMPORT")
        else:
            box.label(text="Install BEHOLD Product for Import Product")
    layout.prop(settings, "studio_backdrop")
    layout.prop(settings, "include_shadow_catcher", text="Catcher")
    layout.operator("behold.apply_catcher", icon="SHADERFX")
    layout.prop(settings, "studio_margin")


class BEHOLD_PT_studio(Panel):
    bl_label = "Studio"
    bl_idname = "BEHOLD_PT_studio"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_order = 20

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, SECTION_ICONS["studio"])

    def draw(self, context: Context):
        draw_studio_first_ship(self.layout, context)


class BEHOLD_PT_studio_advanced(Panel):
    bl_label = "Studio extras"
    bl_idname = "BEHOLD_PT_studio_advanced"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 21

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, "PREFERENCES")

    def draw(self, context: Context):
        draw_parked_heading(self.layout, "Studio", SECTION_ICONS["studio"], leading_separator=False)
        draw_studio_parked(self.layout, context)


CLASSES = (
    BEHOLD_PT_studio,
    BEHOLD_PT_studio_advanced,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
