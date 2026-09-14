# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD N-panel UI.

First-ship chrome: Import / Studio / Shoot stay skinny. Lights is the v0.4.0
lighting section. Cameras is the v0.5.0 product-camera kit. Parked mixer, CAD
box, materials, hotkeys, batch, and turntable live in BEHOLD_PT_advanced
(DEFAULT_CLOSED).
"""

from __future__ import annotations

import bpy
from bpy.types import Context, Panel, UILayout

from ..cad import detect as cad_detect
from ..cad import material_assist
from ..materials import blenderkit_bridge, local_rack
from ..product_import import formats
from ..studio import cameras as camera_lib
from ..studio import lights as light_lib


def _has_selected_mesh(context: Context) -> bool:
    return any(obj.type == "MESH" for obj in context.selected_objects)


def _has_imported_product(context: Context) -> bool:
    return any(
        obj.type == "MESH" and material_assist.is_behold_product(obj)
        for obj in context.scene.objects
    )


def draw_import_first_ship(layout: UILayout, context: Context) -> None:
    """Import Product file picker only."""
    del context
    layout.operator("behold.import_product", icon="IMPORT")


def draw_studio_first_ship(layout: UILayout, context: Context) -> None:
    """Backdrop White / Grey / Black + Build."""
    settings = context.scene.behold
    layout.prop(settings, "studio_backdrop_tone", text="Backdrop", expand=True)
    layout.operator("behold.build_studio", text="Build", icon="OUTLINER_OB_LIGHT")


def draw_shoot_first_ship(layout: UILayout, context: Context) -> None:
    """Draft / Final, Still, Render."""
    settings = context.scene.behold
    row = layout.row(align=True)
    row.prop_enum(settings, "render_quality", "DRAFT")
    row.prop_enum(settings, "render_quality", "FINAL")
    layout.operator("behold.render_still", text="Still", icon="RENDER_STILL")
    layout.operator("behold.render_still", text="Render", icon="RENDER_RESULT")


def draw_lights_section(layout: UILayout, context: Context) -> None:
    """Multi-light inventory + Light Draw Active / New."""
    settings = context.scene.behold
    lights = light_lib.iter_behold_lights(context)

    if not lights:
        empty = layout.box()
        empty.label(text="No BEHOLD lights yet", icon="INFO")
        empty.label(text="Build Studio or Add Light")
        empty.prop(settings, "new_light_energy", text="New W")
        row = empty.row(align=True)
        row.operator("behold.build_studio", text="Build Studio", icon="OUTLINER_OB_LIGHT")
        row.operator("behold.add_light", text="Add Light", icon="ADD")
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
        row = layout.row(align=True)
        row.prop(settings, "new_light_energy", text="New W")
        row.operator("behold.add_light", text="Add", icon="ADD")

    layout.separator()
    col = layout.column(align=True)
    col.label(text="Light Draw")
    col.prop(settings, "light_draw_target", text="Aim", expand=True)
    col.prop(settings, "light_draw_mode", text="Mode", expand=True)
    col.prop(settings, "light_draw_distance")
    col.operator("behold.light_draw", icon="LIGHT_AREA")


def draw_cameras_section(layout: UILayout, context: Context) -> None:
    """Product camera inventory: add / active / frame / delete."""
    settings = context.scene.behold
    cameras = camera_lib.iter_behold_cameras(context)

    if not cameras:
        empty = layout.box()
        empty.label(text="No BEHOLD cameras yet", icon="INFO")
        empty.label(text="Build Studio or Add Camera")
        empty.prop(settings, "new_camera_lens", text="mm")
        row = empty.row(align=True)
        row.operator("behold.build_studio", text="Build Studio", icon="OUTLINER_OB_LIGHT")
        row.operator("behold.add_camera", text="Add Camera", icon="ADD")
        return

    active = camera_lib.get_active_behold_camera(context)
    active_name = active.name if active is not None else ""
    box = layout.box()
    box.label(text="Studio cameras", icon="CAMERA_DATA")
    for cam in cameras:
        row = box.row(align=True)
        is_active = cam.name == active_name
        icon = "RADIOBUT_ON" if is_active else "RADIOBUT_OFF"
        op = row.operator("behold.set_active_camera", text="", icon=icon, emboss=False)
        op.camera_name = cam.name
        row.label(text=camera_lib.display_camera_name(cam))
        row.prop(cam.data, "lens", text="")
        fr = row.operator("behold.frame_camera", text="", icon="ZOOM_SELECTED")
        fr.camera_name = cam.name
        rm = row.operator("behold.remove_camera", text="", icon="X")
        rm.camera_name = cam.name
    if active is not None:
        box.label(text=f"Active: {camera_lib.display_camera_name(active)}")
    row = layout.row(align=True)
    row.prop(settings, "new_camera_lens", text="mm")
    row.operator("behold.add_camera", text="Add", icon="ADD")
    row.operator("behold.frame_camera", text="Frame", icon="ZOOM_SELECTED")
    row.operator("behold.clear_cameras", text="Clear", icon="TRASH")


def draw_import_parked(layout: UILayout, context: Context) -> None:
    """Auto-studio / Material Assist toggles and CAD backend (parked)."""
    settings = context.scene.behold
    cad = cad_detect.cad_status()

    if not _has_selected_mesh(context) and not _has_imported_product(context):
        empty = layout.box()
        empty.label(text="No product in the scene yet", icon="INFO")
        empty.label(text=f"Mesh: {formats.mesh_format_summary()}")
        empty.label(text=f"CAD: {formats.cad_format_summary()}")

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


def draw_studio_parked(layout: UILayout, context: Context) -> None:
    """Light rig, shadow catcher, mixer (parked)."""
    settings = context.scene.behold
    if not _has_selected_mesh(context):
        box = layout.box()
        box.label(text="Import or select a product mesh", icon="INFO")
        box.operator("behold.import_product", icon="IMPORT")
    layout.prop(settings, "studio_backdrop")
    layout.prop(settings, "studio_light_rig")
    layout.prop(settings, "include_shadow_catcher")

    col = layout.column(align=True)
    col.label(text="Light Mixer")
    col.prop(settings, "key_power")
    col.prop(settings, "fill_ratio")
    col.prop(settings, "rim_ratio")
    col.prop(settings, "light_temperature")
    col.operator("behold.refresh_lights", icon="FILE_REFRESH")


def draw_materials_parked(layout: UILayout, context: Context) -> None:
    """Local PBR rack + BlenderKit (parked)."""
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


def draw_light_draw_parked(layout: UILayout, context: Context) -> None:
    """Light Draw hotkeys (parked — controls live on Lights)."""
    del context
    col = layout.column(align=True)
    col.label(text="While drawing:")
    col.label(text="LMB drag — aim")
    col.label(text="Wheel — power")
    col.label(text="Shift+Wheel — size")
    col.label(text="Ctrl+Wheel — distance")
    col.label(text="1 / 2 / 3 — Reflect / Direct / Orbit")
    col.label(text="S — solo · F — false color · Esc — exit")


def draw_shoot_parked(layout: UILayout, context: Context) -> None:
    """EV / WB / tokens / bookmark / batch / turntable (parked)."""
    settings = context.scene.behold
    has_camera = context.scene.camera is not None or bool(settings.main_camera_name)
    has_mesh = any(obj.type == "MESH" for obj in context.selected_objects)

    if not has_camera:
        box = layout.box()
        box.label(text="No camera — Build Studio or Add Camera", icon="ERROR")

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
    layout.operator("behold.batch_angles", icon="CAMERA_DATA")

    layout.separator()
    layout.prop(settings, "turntable_frames")
    layout.operator("behold.setup_turntable", icon="DRIVER_ROTATIONAL_DIFFERENCE")
    layout.operator("behold.render_turntable", icon="RENDER_ANIMATION")


class BEHOLD_PT_main(Panel):
    bl_label = "BEHOLD"
    bl_idname = "BEHOLD_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"

    def draw(self, context: Context):
        del context


class BEHOLD_PT_import(Panel):
    bl_label = "Import"
    bl_idname = "BEHOLD_PT_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"

    def draw(self, context: Context):
        draw_import_first_ship(self.layout, context)


class BEHOLD_PT_studio(Panel):
    bl_label = "Studio"
    bl_idname = "BEHOLD_PT_studio"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"

    def draw(self, context: Context):
        draw_studio_first_ship(self.layout, context)


class BEHOLD_PT_shoot(Panel):
    bl_label = "Shoot"
    bl_idname = "BEHOLD_PT_shoot"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"

    def draw(self, context: Context):
        draw_shoot_first_ship(self.layout, context)


class BEHOLD_PT_lights(Panel):
    bl_label = "Lights"
    bl_idname = "BEHOLD_PT_lights"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"

    def draw(self, context: Context):
        draw_lights_section(self.layout, context)


class BEHOLD_PT_cameras(Panel):
    bl_label = "Cameras"
    bl_idname = "BEHOLD_PT_cameras"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"

    def draw(self, context: Context):
        draw_cameras_section(self.layout, context)


class BEHOLD_PT_advanced(Panel):
    bl_label = "Advanced"
    bl_idname = "BEHOLD_PT_advanced"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: Context):
        layout = self.layout
        layout.label(text="Import")
        draw_import_parked(layout, context)
        layout.separator()
        layout.label(text="Studio")
        draw_studio_parked(layout, context)
        layout.separator()
        layout.label(text="Materials")
        draw_materials_parked(layout, context)
        layout.separator()
        layout.label(text="Light Draw")
        draw_light_draw_parked(layout, context)
        layout.separator()
        layout.label(text="Shoot")
        draw_shoot_parked(layout, context)


CLASSES = (
    BEHOLD_PT_main,
    BEHOLD_PT_import,
    BEHOLD_PT_studio,
    BEHOLD_PT_shoot,
    BEHOLD_PT_lights,
    BEHOLD_PT_cameras,
    BEHOLD_PT_advanced,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
