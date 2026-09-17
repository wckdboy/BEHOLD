# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD Lighting N-panel."""

from __future__ import annotations

import bpy
from bpy.types import Context, Panel, UILayout

from .. import lights as light_lib
from ..common.chrome import draw_empty_card, draw_parked_heading, draw_section_icon
from ..common.deps import BUILD_STUDIO_OP
from .flow_ids import EMPTY_LIGHTS, SECTION_ICONS


def _settings(context: Context):
    return context.scene.behold_lighting


def draw_lights_section(layout: UILayout, context: Context) -> None:
    """Multi-light inventory + shape + gobo + IES + linking lite + Light Draw."""
    settings = _settings(context)
    lights = light_lib.iter_behold_lights(context)

    if not lights:
        empty = draw_empty_card(layout, EMPTY_LIGHTS)
        empty.prop(settings, "new_light_energy", text="New W")
        empty.operator("behold.add_light", text="Add Light", icon="ADD")
    else:
        active = light_lib.get_active_behold_light(context)
        active_name = active.name if active is not None else ""
        box = layout.box()
        box.label(text="Studio lights", icon="LIGHT_AREA")
        for light in lights:
            row = box.row(align=True)
            is_active = light.name == active_name
            icon = "RADIOBUT_ON" if is_active else "RADIOBUT_OFF"
            op = row.operator("behold.set_active_light", text="", icon=icon, emboss=False)
            op.light_name = light.name
            row.label(text=light_lib.display_light_name(light))
            row.prop(light.data, "energy", text="")
            rm = row.operator("behold.remove_light", text="", icon="X")
            rm.light_name = light.name
        if active is not None:
            box.label(text=f"Active: {light_lib.display_light_name(active)}")
        draw_lights_shape(layout, context)
        draw_lights_gobo(layout, context)
        draw_lights_ies(layout, context)
        draw_lights_linking(layout, context)
        row = layout.row(align=True)
        row.prop(settings, "new_light_energy", text="New W")
        row.operator("behold.add_light", text="Add", icon="ADD")

    layout.separator()
    col = layout.box()
    col.label(text="Light Draw", icon="LIGHT_AREA")
    col.prop(settings, "light_draw_target", text="Aim", expand=True)
    col.prop(settings, "light_draw_mode", text="Mode", expand=True)
    col.prop(settings, "light_draw_distance")
    col.operator("behold.light_draw", icon="LIGHT_AREA")


def draw_lights_shape(layout: UILayout, context: Context) -> None:
    """Size and spread on this light. Falloff waits until Gobo and IES are off."""
    settings = _settings(context)
    card = layout.box()
    card.label(text="Shape", icon="LIGHT_AREA")
    card.label(text="Size and spread. Falloff waits until Gobo and IES are off")
    card.prop(settings, "light_shape_preset", text="", expand=True)
    apply = card.operator(
        "behold.apply_light_preset",
        text="Apply to active",
        icon="CHECKMARK",
    )
    apply.preset = settings.light_shape_preset


def draw_lights_gobo(layout: UILayout, context: Context) -> None:
    """Cookie on this light. Turns IES off."""
    settings = _settings(context)
    card = layout.box()
    card.label(text="Gobo", icon="TEXTURE")
    card.label(text="Cookie on this light. Turns IES off")
    card.prop(settings, "light_gobo_preset", text="", expand=True)
    if settings.light_gobo_preset != "NONE":
        row = card.row(align=True)
        row.prop(settings, "light_gobo_scale", text="Scale")
        row.prop(settings, "light_gobo_strength", text="Strength")


def draw_lights_ies(layout: UILayout, context: Context) -> None:
    """Photometric profile. Turns Gobo off."""
    settings = _settings(context)
    card = layout.box()
    card.label(text="IES", icon="LIGHT_SPOT")
    card.label(text="Photometric profile. Turns Gobo off")
    card.prop(settings, "light_ies_filepath", text="")
    row = card.row(align=True)
    row.operator("behold.load_ies", text="Load", icon="FILE_FOLDER")
    row.operator("behold.load_ies_sample", text="Sample")
    row.operator("behold.clear_ies", text="Clear", icon="X")
    if settings.light_ies_filepath:
        row = card.row(align=True)
        row.prop(settings, "light_ies_strength", text="Strength")
        row.prop(settings, "light_ies_scale", text="Scale")


def draw_lights_linking(layout: UILayout, context: Context) -> None:
    """Who this light hits. Independent of Shape / Gobo / IES."""
    settings = _settings(context)
    card = layout.box()
    card.label(text="Linking", icon="LINKED")
    card.label(text="Who this light hits — not the beam shape")
    card.prop(settings, "light_linking_kind", text="", expand=True)
    row = card.row(align=True)
    link = row.operator("behold.link_selected", text="Link Selected")
    link.kind = settings.light_linking_kind
    unlink = row.operator("behold.unlink_selected", text="Unlink")
    unlink.kind = settings.light_linking_kind
    row.operator("behold.solo_product_link", text="Solo product")


def draw_light_draw_parked(layout: UILayout, context: Context) -> None:
    """Light Draw hotkeys + Apply Gobo / IES (parked — both live on Lights)."""
    settings = _settings(context)
    col = layout.column(align=True)
    col.label(text="While drawing:")
    col.label(text="LMB drag — aim")
    col.label(text="Wheel — power")
    col.label(text="Shift+Wheel — size")
    col.label(text="Ctrl+Wheel — distance")
    col.label(text="1 / 2 / 3 — Reflect / Direct / Orbit")
    col.label(text="S — solo · F — false color · Esc — exit")
    col.separator()
    col.label(text="Open Light Draw from the pie (Shift+Alt+B) or Lights")
    col.separator()
    col.label(text="Gobo")
    col.prop(settings, "light_gobo_preset", text="", expand=True)
    col.prop(settings, "light_gobo_scale")
    col.prop(settings, "light_gobo_strength")
    col.operator("behold.apply_gobo", icon="TEXTURE")
    col.separator()
    col.label(text="IES")
    col.prop(settings, "light_ies_filepath", text="")
    col.prop(settings, "light_ies_strength")
    col.prop(settings, "light_ies_scale")
    col.operator("behold.apply_ies", icon="LIGHT_SPOT")
    col.operator("behold.clear_ies", text="Clear IES")
    col.separator()
    col.label(text="Light Mixer")
    col.prop(settings, "key_power")
    col.prop(settings, "fill_ratio")
    col.prop(settings, "rim_ratio")
    col.prop(settings, "light_temperature")
    col.prop(settings, "studio_light_rig")
    col.operator("behold.refresh_lights", icon="FILE_REFRESH")


class BEHOLD_PT_lights(Panel):
    bl_label = "Lights"
    bl_idname = "BEHOLD_PT_lights"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_order = 30

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, SECTION_ICONS["lights"])

    def draw(self, context: Context):
        draw_lights_section(self.layout, context)


class BEHOLD_PT_lights_advanced(Panel):
    bl_label = "Lights extras"
    bl_idname = "BEHOLD_PT_lights_advanced"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 31

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, "PREFERENCES")

    def draw(self, context: Context):
        draw_parked_heading(
            self.layout, "Light Draw", SECTION_ICONS["lights"], leading_separator=False
        )
        draw_light_draw_parked(self.layout, context)


CLASSES = (
    BEHOLD_PT_lights,
    BEHOLD_PT_lights_advanced,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
