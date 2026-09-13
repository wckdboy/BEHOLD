# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD N-panel UI."""

from __future__ import annotations

import bpy
from bpy.types import Context, Panel

from ..materials import blenderkit_bridge, local_rack


class BEHOLD_PT_main(Panel):
    bl_label = "BEHOLD"
    bl_idname = "BEHOLD_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"

    def draw(self, context: Context):
        layout = self.layout
        has_mesh = any(obj.type == "MESH" for obj in context.selected_objects)
        if not has_mesh:
            box = layout.box()
            box.label(text="Select a mesh product to begin", icon="INFO")


class BEHOLD_PT_studio(Panel):
    bl_label = "Studio"
    bl_idname = "BEHOLD_PT_studio"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"

    def draw(self, context: Context):
        layout = self.layout
        settings = context.scene.behold
        layout.prop(settings, "studio_backdrop")
        layout.prop(settings, "studio_light_rig")
        layout.prop(settings, "include_shadow_catcher")
        layout.operator("behold.build_studio", icon="OUTLINER_OB_LIGHT")

        col = layout.column(align=True)
        col.label(text="Light Mixer")
        col.prop(settings, "key_power")
        col.prop(settings, "fill_ratio")
        col.prop(settings, "rim_ratio")
        col.prop(settings, "light_temperature")
        col.operator("behold.refresh_lights", icon="FILE_REFRESH")


class BEHOLD_PT_materials(Panel):
    bl_label = "Materials"
    bl_idname = "BEHOLD_PT_materials"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"

    def draw(self, context: Context):
        layout = self.layout
        settings = context.scene.behold

        layout.label(text="Local PBR rack")
        grid = layout.grid_flow(columns=3, align=True)
        for key, data in local_rack.PRESETS.items():
            op = grid.operator("behold.apply_local_material", text=data["label"])
            op.preset = key

        layout.separator()
        status = blenderkit_bridge.blenderkit_status()
        box = layout.box()
        box.label(text="BlenderKit", icon="IMPORT")
        box.label(text=status["label"])
        for line in status["detail"].split(". "):
            if line.strip():
                box.label(text=line.strip().rstrip(".") + ".")

        if not status["installed"]:
            box.operator("wm.url_open", text="Get BlenderKit", icon="URL").url = (
                "https://www.blenderkit.com/get-blenderkit/"
            )
        else:
            if not status["logged_in"]:
                box.operator("behold.blenderkit_login", icon="USER")
            else:
                box.label(text="Account ready", icon="CHECKMARK")
            box.prop(settings, "blenderkit_query", text="")
            row = box.row(align=True)
            row.operator("behold.blenderkit_search", icon="VIEWZOOM")
            row.operator("behold.blenderkit_apply", icon="MATERIAL")


class BEHOLD_PT_light_draw(Panel):
    bl_label = "Light Draw"
    bl_idname = "BEHOLD_PT_light_draw"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"

    def draw(self, context: Context):
        layout = self.layout
        settings = context.scene.behold

        has_light = any(obj.type == "LIGHT" for obj in context.scene.objects)
        if not has_light:
            box = layout.box()
            box.label(text="Build Studio first (or add a light)", icon="INFO")

        layout.prop(settings, "light_draw_mode", text="Mode")
        layout.prop(settings, "light_draw_distance")
        layout.operator("behold.light_draw", icon="LIGHT_AREA")
        layout.operator("behold.light_draw_cycle_mode", icon="FILE_REFRESH")

        col = layout.column(align=True)
        col.label(text="While drawing:")
        col.label(text="LMB drag — aim")
        col.label(text="Wheel — power")
        col.label(text="Shift+Wheel — size")
        col.label(text="Ctrl+Wheel — distance")
        col.label(text="1 / 2 / 3 — Reflect / Direct / Orbit")
        col.label(text="S — solo · F — false color · Esc — exit")


class BEHOLD_PT_shoot(Panel):
    bl_label = "Shoot"
    bl_idname = "BEHOLD_PT_shoot"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"

    def draw(self, context: Context):
        layout = self.layout
        settings = context.scene.behold

        col = layout.column(align=True)
        col.prop(settings, "exposure_ev")
        col.prop(settings, "false_color")
        col.operator("behold.apply_exposure", icon="COLOR")

        layout.separator()
        layout.operator("behold.render_still", icon="RENDER_STILL")

        layout.separator()
        layout.prop(settings, "turntable_frames")
        layout.operator("behold.setup_turntable", icon="DRIVER_ROTATIONAL_DIFFERENCE")
        layout.operator("behold.render_turntable", icon="RENDER_ANIMATION")


CLASSES = (
    BEHOLD_PT_main,
    BEHOLD_PT_studio,
    BEHOLD_PT_materials,
    BEHOLD_PT_light_draw,
    BEHOLD_PT_shoot,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
