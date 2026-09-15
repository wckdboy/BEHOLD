# SPDX-License-Identifier: GPL-3.0-or-later
"""Utilities N-panel — poll-gated, not part of the first-ship CLASSES tuple."""

from __future__ import annotations

from bpy.types import Context, Panel

from ..preferences import get_prefs
from .flag import PANEL_ID, show_utilities_panel
from .wall import resolve_layers, thickness_mm_for_storey


class BEHOLD_PT_utilities(Panel):
    bl_label = "Utilities"
    bl_idname = PANEL_ID
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"
    bl_order = 80
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return show_utilities_panel(get_prefs(context))

    def draw_header(self, context: Context) -> None:
        del context
        self.layout.label(text="", icon="MOD_BUILD")

    def draw(self, context: Context) -> None:
        layout = self.layout
        settings = context.scene.behold.utilities
        card = layout.box()
        card.label(text="Danish wall", icon="MOD_BUILD")
        card.prop(settings, "storey", text="")
        card.prop(settings, "wall_width")
        card.prop(settings, "wall_height")
        if settings.storey == "FOUNDATION":
            card.prop(settings, "foundation_mm")
        total = thickness_mm_for_storey(
            settings.storey, foundation_mm=settings.foundation_mm
        )
        layers = resolve_layers(
            settings.storey,
            total_mm=total,
            foundation_mm=settings.foundation_mm,
            exterior_mm=settings.exterior_mm,
            interior_mm=settings.interior_mm,
        )
        card.label(text=f"{layers.total_mm:.0f} mm  ·  {layers.exterior_mm:.0f} / {layers.insulation_mm:.0f} / {layers.interior_mm:.0f}")
        row = card.row(align=True)
        row.prop(settings, "exterior_mm")
        row.prop(settings, "interior_mm")
        card.prop(settings, "include_door")
        if settings.include_door:
            card.prop(settings, "door_width")
            card.prop(settings, "door_height")
        card.operator("behold.build_danish_wall", icon="MESH_CUBE")
        card.operator("behold.export_wall_scad", icon="EXPORT")

        mount = layout.box()
        mount.label(text="Balcony mount", icon="EMPTY_ARROWS")
        mount.prop(settings, "leg_height")
        mount.prop(settings, "mount_inset")
        row = mount.row(align=True)
        row.operator("behold.build_balcony_legs", icon="EMPTY_SINGLE_ARROW")
        row.operator("behold.build_balcony_bracket", icon="MOD_TRIANGULATE")
        mount.label(text="Needs a wall + balcony mesh")

        eave = layout.box()
        eave.label(text="Eave / roof", icon="LINCURVE")
        eave.prop(settings, "eave_section", text="")
        eave.prop(settings, "eave_pitch")
        eave.operator("behold.build_eave_section", icon="MESH_CUBE")
        eave.label(text="Needs a wall · balcony mesh optional")
        layout.label(text="MinAltan snit are vejledende")


CLASSES = (BEHOLD_PT_utilities,)
