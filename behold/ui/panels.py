# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD N-panel UI."""

from __future__ import annotations

import bpy
from bpy.types import Context, Panel

from ..cad import detect as cad_detect
from ..cad import material_assist
from ..materials import blenderkit_bridge, local_rack
from ..product_import import formats


def _has_selected_mesh(context: Context) -> bool:
    return any(obj.type == "MESH" for obj in context.selected_objects)


def _has_imported_product(context: Context) -> bool:
    return any(
        obj.type == "MESH" and material_assist.is_behold_product(obj)
        for obj in context.scene.objects
    )


class BEHOLD_PT_main(Panel):
    bl_label = "BEHOLD"
    bl_idname = "BEHOLD_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"

    def draw(self, context: Context):
        layout = self.layout
        has_mesh = _has_selected_mesh(context)
        if not has_mesh:
            box = layout.box()
            if _has_imported_product(context):
                box.label(text="Select the imported product to continue", icon="INFO")
            else:
                box.label(text="Import a product to begin", icon="INFO")
                box.operator("behold.import_product", icon="IMPORT")


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
        if not _has_selected_mesh(context):
            box = layout.box()
            box.label(text="Import or select a product mesh", icon="INFO")
            box.operator("behold.import_product", icon="IMPORT")
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


class BEHOLD_PT_import(Panel):
    bl_label = "Import"
    bl_idname = "BEHOLD_PT_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"

    def draw(self, context: Context):
        layout = self.layout
        settings = context.scene.behold
        cad = cad_detect.cad_status()

        if not _has_selected_mesh(context) and not _has_imported_product(context):
            empty = layout.box()
            empty.label(text="No product in the scene yet", icon="INFO")
            empty.label(text=f"Mesh: {formats.mesh_format_summary()}")
            empty.label(text=f"CAD: {formats.cad_format_summary()}")

        layout.operator("behold.import_product", icon="IMPORT")
        col = layout.column(align=True)
        col.prop(settings, "import_auto_studio")
        col.prop(settings, "import_auto_material_assist")

        row = layout.row(align=True)
        row.operator("behold.cad_material_assist", icon="MATERIAL")
        row.operator("behold.cad_build_studio", icon="OUTLINER_OB_LIGHT")

        box = layout.box()
        box.label(text="CAD backend", icon="MESH_DATA")
        box.label(text=cad["label"])
        for line in cad["detail"].split(". "):
            if line.strip():
                box.label(text=line.strip().rstrip(".") + ".")
        if not cad["can_import"]:
            box.operator(
                "wm.url_open",
                text="Get STEPper NEXT",
                icon="URL",
            ).url = cad_detect.STEPPER_INSTALL_URL
            box.label(text="Mesh formats never need STEPper")
        else:
            box.operator("behold.import_step", text="Import STEP / IGES…", icon="FILE_3D")


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
        has_camera = context.scene.camera is not None or bool(settings.main_camera_name)
        has_mesh = any(obj.type == "MESH" for obj in context.selected_objects)

        if not has_camera:
            box = layout.box()
            box.label(text="No camera — Build Studio first", icon="ERROR")

        col = layout.column(align=True)
        col.label(text="Look")
        col.prop(settings, "exposure_ev")
        col.prop(settings, "white_balance_kelvin")
        col.prop(settings, "false_color")
        col.operator("behold.apply_exposure", icon="COLOR")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Quality")
        col.prop(settings, "render_quality", text="")
        col.operator("behold.apply_quality", icon="SETTINGS")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Camera")
        row = col.row(align=True)
        row.operator("behold.bookmark_camera", text="Bookmark")
        row.operator("behold.use_main_camera", text="Use Main")
        if settings.main_camera_name:
            col.label(text=f"Main: {settings.main_camera_name}", icon="CAMERA_DATA")

        layout.separator()
        col = layout.column(align=True)
        col.label(text="Output")
        col.prop(settings, "output_directory", text="")
        col.label(text="Tokens: {angle} {camera} {quality}")

        layout.separator()
        if not has_mesh:
            box = layout.box()
            box.label(text="Select mesh(es) for batch / turntable", icon="INFO")
            if not _has_imported_product(context):
                box.operator("behold.import_product", icon="IMPORT")
        layout.operator("behold.render_still", icon="RENDER_STILL")
        layout.operator("behold.batch_angles", icon="CAMERA_DATA")

        layout.separator()
        layout.prop(settings, "turntable_frames")
        layout.operator("behold.setup_turntable", icon="DRIVER_ROTATIONAL_DIFFERENCE")
        layout.operator("behold.render_turntable", icon="RENDER_ANIMATION")


CLASSES = (
    BEHOLD_PT_main,
    BEHOLD_PT_import,
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
