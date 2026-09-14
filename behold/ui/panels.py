# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD N-panel UI.

Studio chrome (v0.9.0) + workflow order (v0.12.0): branded hero + Import →
Studio → Dress → Shoot strip on the main panel; physical child order is
Import → Studio → Lights → Materials → Cameras → Shoot → Advanced so Shoot
is last. Easy update (v0.10.0): a dismissible GitHub notice on the main
panel when a newer stable zip is cached. Cyclorama auto-fit (v0.11.0).
Section header icons; box cards and one-CTA empty states. First-ship
Import / Studio / Shoot stay skinny. Import shows the picker plus one CAD
backend line (v0.7.0). Lights is the v0.4.0 lighting section. Cameras is the
v0.5.0 product-camera kit. Shoot carries a compact Turntable row (v0.6.0).
Materials is the v0.8.0 local-look rack (Assist applies without BlenderKit).
Parked mixer, CAD box extras, BlenderKit chrome, hotkeys, batch, and
turntable extras (plus Studio Margin in 0.11.0) live in BEHOLD_PT_advanced
(DEFAULT_CLOSED). Compact Studio HDRI (v0.13.0): load / strength / Z rotation
/ reflections-only + Reset world — not a new first-class panel. Compact Shot
Manager on Shoot (v0.14.0): named presets for camera + quality + HDRI +
backdrop + output tokens. v0.15.0 draw-once cache: CAD status + scene flags
once per N-panel pass.
"""

from __future__ import annotations

from typing import Never

import bpy
from bpy.types import Context, Panel, UILayout

from ..cad import detect as cad_detect
from ..cad.stepper_api import import_panel_copy
from ..materials import blenderkit_bridge, local_rack
from ..materials.presets import EMPTY_NO_MESH, empty_state
from ..previews import mark_icon_kwargs
from ..product_import import formats
from ..shoot import turntable as turntable_lib
from ..studio import cameras as camera_lib
from ..studio import lights as light_lib
from .chrome import (
    draw_empty_card,
    draw_flow_strip,
    draw_hero,
    draw_parked_heading,
    draw_section_icon,
    draw_update_notice,
    scene_snap_from_context,
)
from .flow import (
    CHILD_PANEL_BL_ORDER,
    EMPTY_CAMERAS,
    EMPTY_LIGHTS,
    EMPTY_MATERIALS,
    EMPTY_SHOTS,
    SECTION_ICONS,
)
from .messages import BATCH_NO_MESH, NO_MESH_SELECTED, NO_PRODUCT


def _has_selected_mesh(context: Context) -> bool:
    return scene_snap_from_context(context).has_selected_mesh


def _has_imported_product(context: Context) -> bool:
    return scene_snap_from_context(context).has_imported_product


def draw_cad_status_line(layout: UILayout, cad: dict) -> None:
    """One CAD backend line + optional Install STEPper NEXT (not STEPper's dialog)."""
    copy = import_panel_copy(
        cad["backend"],
        stepper_needs_enable=bool(cad.get("stepper_needs_enable")),
    )
    backend = cad["backend"]
    if backend == "STEPPER":
        icon = "CHECKMARK"
    elif backend == "OCP":
        icon = "INFO"
    elif backend == "NONE":
        icon = "ERROR"
    else:
        unreachable: Never = backend
        raise RuntimeError(f"unhandled CAD backend: {unreachable}")
    box = layout.box()
    box.label(text=copy["line"], icon=icon)
    if copy["detail"]:
        box.label(text=copy["detail"])
    if copy["show_install"]:
        box.operator(
            "behold.open_stepper_install",
            text=copy["install_label"],
            icon="URL",
        )


def draw_import_first_ship(layout: UILayout, context: Context) -> None:
    """Import Product picker plus CAD backend status."""
    del context
    card = layout.box()
    card.operator("behold.import_product", icon="IMPORT")
    draw_cad_status_line(layout, cad_detect.cad_status_for_draw())


def draw_studio_first_ship(layout: UILayout, context: Context) -> None:
    """Backdrop White / Grey / Black + Build, then compact HDRI world."""
    settings = context.scene.behold
    card = layout.box()
    card.prop(settings, "studio_backdrop_tone", text="Backdrop", expand=True)
    card.operator("behold.build_studio", text="Build", icon="OUTLINER_OB_LIGHT")
    draw_studio_hdri(layout, context)


def draw_studio_hdri(layout: UILayout, context: Context) -> None:
    """World HDRI: load, strength, Z rotation, optional reflections-only."""
    settings = context.scene.behold
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


def draw_shoot_first_ship(layout: UILayout, context: Context) -> None:
    """Draft / Final, Still, Render, compact Shots list, compact Turntable row."""
    settings = context.scene.behold
    card = layout.box()
    row = card.row(align=True)
    row.prop_enum(settings, "render_quality", "DRAFT")
    row.prop_enum(settings, "render_quality", "FINAL")
    row = card.row(align=True)
    row.operator("behold.render_still", text="Still", icon="RENDER_STILL")
    row.operator("behold.render_still", text="Render", icon="RENDER_RESULT")
    layout.separator()
    draw_shots_compact(layout, context)
    layout.separator()
    draw_turntable_compact(layout, context)


def draw_shots_compact(layout: UILayout, context: Context) -> None:
    """Named shots: list, Add from current, Apply, inline rename, Delete."""
    settings = context.scene.behold
    collection = settings.shots
    if len(collection) == 0:
        draw_empty_card(layout, EMPTY_SHOTS)
        return
    card = layout.box()
    card.label(text="Shots", icon="SEQUENCE")
    active_index = int(getattr(settings, "active_shot_index", -1))
    for index, item in enumerate(collection):
        row = card.row(align=True)
        is_active = index == active_index
        icon = "RADIOBUT_ON" if is_active else "RADIOBUT_OFF"
        select = row.operator(
            "behold.apply_shot", text="", icon=icon, emboss=False
        )
        select.shot_index = index
        row.prop(item, "name", text="")
        apply = row.operator("behold.apply_shot", text="Apply")
        apply.shot_index = index
        remove = row.operator("behold.remove_shot", text="", icon="X")
        remove.shot_index = index
    card.operator("behold.add_shot", text="Add", icon="ADD")


def draw_turntable_compact(layout: UILayout, context: Context) -> None:
    """One row: seconds + Setup + Play. Empty-state if no camera or product."""
    settings = context.scene.behold
    cam = camera_lib.resolve_shoot_camera(context)
    snap = scene_snap_from_context(context)
    message = turntable_lib.empty_state(
        has_camera=cam is not None,
        has_product=snap.has_product,
    )
    if message == turntable_lib.EMPTY_NO_CAMERA:
        box = layout.box()
        box.label(text=message, icon="INFO")
        box.operator("behold.build_studio", text="Build Studio", icon="OUTLINER_OB_LIGHT")
        box.operator("behold.add_camera", text="Add Camera", icon="ADD")
        return
    if message == turntable_lib.EMPTY_NO_PRODUCT:
        box = layout.box()
        box.label(text=message, icon="INFO")
        box.operator("behold.import_product", icon="IMPORT")
        return
    if message is not None:
        box = layout.box()
        box.label(text=message, icon="INFO")
        return
    card = layout.box()
    row = card.row(align=True)
    row.label(text="Turntable", icon="RECOVER_LAST")
    row.prop(settings, "turntable_seconds", text="")
    row.operator("behold.setup_turntable", text="Setup")
    row.operator("behold.play_turntable", text="Play", icon="PLAY")


def draw_lights_section(layout: UILayout, context: Context) -> None:
    """Multi-light inventory + Light Draw Active / New."""
    settings = context.scene.behold
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


def draw_materials_section(layout: UILayout, context: Context) -> None:
    """Local PBR rack + Assist. Empty-state if nothing dressable is selected."""
    meshes = local_rack.dressable_meshes(context.selected_objects)
    message = empty_state(has_product_mesh=bool(meshes))
    if message == EMPTY_NO_MESH:
        draw_empty_card(layout, EMPTY_MATERIALS)
        return
    if message is not None:
        box = layout.box()
        box.label(text=message, icon="INFO")
        return

    card = layout.box()
    card.label(text="Looks", icon="MATERIAL")
    grid = card.grid_flow(columns=3, align=True)
    for key, data in local_rack.PRESETS.items():
        op = grid.operator("behold.apply_local_material", text=data["label"])
        op.preset = key
    card.operator("behold.cad_material_assist", text="Assist", icon="MATERIAL")

    status = blenderkit_bridge.blenderkit_status()
    if status["installed"] and status["logged_in"]:
        card.label(text="BlenderKit signed in — Assist also searches")
    else:
        card.label(text="Local looks — no BlenderKit account needed")


def draw_cameras_section(layout: UILayout, context: Context) -> None:
    """Product camera inventory: add / active / frame / delete."""
    settings = context.scene.behold
    cameras = camera_lib.iter_behold_cameras(context)

    if not cameras:
        empty = draw_empty_card(layout, EMPTY_CAMERAS)
        empty.prop(settings, "new_camera_lens", text="mm")
        empty.operator("behold.add_camera", text="Add Camera", icon="ADD")
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
    cad = cad_detect.cad_status_for_draw()

    if not _has_selected_mesh(context) and not _has_imported_product(context):
        empty = layout.box()
        empty.label(text=NO_PRODUCT, icon="INFO")
        empty.label(text=f"Mesh: {formats.mesh_format_summary()}")
        empty.label(text=f"CAD: {formats.cad_format_summary()}")
        empty.operator("behold.import_product", icon="IMPORT")

    col = layout.column(align=True)
    col.prop(settings, "import_auto_studio")
    col.prop(settings, "import_auto_material_assist")

    row = layout.row(align=True)
    row.operator("behold.cad_material_assist", icon="MATERIAL")
    row.operator("behold.cad_build_studio", icon="OUTLINER_OB_LIGHT")

    box = layout.box()
    box.label(text="CAD backend", icon="MESH_DATA")
    copy = import_panel_copy(
        cad["backend"],
        stepper_needs_enable=bool(cad.get("stepper_needs_enable")),
    )
    box.label(text=copy["line"])
    if copy["detail"]:
        box.label(text=copy["detail"])
    if copy["show_install"]:
        box.operator(
            "behold.open_stepper_install",
            text=copy["install_label"],
            icon="URL",
        )
        box.label(text="Mesh formats never need STEPper")
    if cad["can_import"]:
        box.operator("behold.import_step", text="Import STEP / IGES…", icon="FILE_3D")


def draw_studio_parked(layout: UILayout, context: Context) -> None:
    """Light rig, shadow catcher, mixer (parked)."""
    settings = context.scene.behold
    if not _has_selected_mesh(context):
        box = layout.box()
        box.label(text=NO_MESH_SELECTED, icon="INFO")
        box.operator("behold.import_product", icon="IMPORT")
    layout.prop(settings, "studio_backdrop")
    layout.prop(settings, "studio_light_rig")
    layout.prop(settings, "include_shadow_catcher")
    layout.prop(settings, "studio_margin")

    col = layout.column(align=True)
    col.label(text="Light Mixer")
    col.prop(settings, "key_power")
    col.prop(settings, "fill_ratio")
    col.prop(settings, "rim_ratio")
    col.prop(settings, "light_temperature")
    col.operator("behold.refresh_lights", icon="FILE_REFRESH")


def draw_materials_parked(layout: UILayout, context: Context) -> None:
    """BlenderKit chrome (parked). Local rack buttons stay for Advanced users."""
    settings = context.scene.behold

    layout.label(text="Local PBR rack")
    grid = layout.grid_flow(columns=3, align=True)
    for key, data in local_rack.PRESETS.items():
        op = grid.operator("behold.apply_local_material", text=data["label"])
        op.preset = key
    layout.operator("behold.cad_material_assist", text="Assist", icon="MATERIAL")

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
        box.label(text="Local looks still apply without an account")
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
    col.separator()
    col.label(text="Open Light Draw from the pie (Shift+Alt+B) or Lights")


def draw_shoot_parked(layout: UILayout, context: Context) -> None:
    """EV / WB / tokens / bookmark / batch / turntable extras (parked)."""
    settings = context.scene.behold
    has_camera = context.scene.camera is not None or bool(settings.main_camera_name)
    has_mesh = _has_selected_mesh(context)

    if not has_camera:
        box = layout.box()
        box.label(text=turntable_lib.EMPTY_NO_CAMERA, icon="ERROR")
        box.operator("behold.build_studio", text="Build Studio", icon="OUTLINER_OB_LIGHT")

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
        box.label(text=BATCH_NO_MESH, icon="INFO")
        if not _has_imported_product(context):
            box.operator("behold.import_product", icon="IMPORT")
    layout.operator("behold.batch_angles", icon="CAMERA_DATA")

    layout.separator()
    col = layout.column(align=True)
    col.label(text="Turntable")
    col.prop(settings, "turntable_interpolation", text="Spin")
    row = col.row(align=True)
    row.operator("behold.bake_turntable", text="Bake")
    row.operator("behold.clear_turntable", text="Clear")
    col.operator("behold.render_turntable", icon="RENDER_ANIMATION")


class BEHOLD_PT_main(Panel):
    bl_label = "BEHOLD"
    bl_idname = "BEHOLD_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"

    def draw_header(self, context: Context):
        del context
        kwargs = mark_icon_kwargs()
        if "icon_value" in kwargs:
            self.layout.label(text="", icon_value=int(kwargs["icon_value"]))

    def draw(self, context: Context):
        draw_hero(self.layout)
        draw_update_notice(self.layout, context)
        draw_flow_strip(self.layout, context)


class BEHOLD_PT_import(Panel):
    bl_label = "Import"
    bl_idname = "BEHOLD_PT_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"
    bl_order = CHILD_PANEL_BL_ORDER["BEHOLD_PT_import"]

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, SECTION_ICONS["import"])

    def draw(self, context: Context):
        draw_import_first_ship(self.layout, context)


class BEHOLD_PT_studio(Panel):
    bl_label = "Studio"
    bl_idname = "BEHOLD_PT_studio"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"
    bl_order = CHILD_PANEL_BL_ORDER["BEHOLD_PT_studio"]

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, SECTION_ICONS["studio"])

    def draw(self, context: Context):
        draw_studio_first_ship(self.layout, context)


class BEHOLD_PT_shoot(Panel):
    bl_label = "Shoot"
    bl_idname = "BEHOLD_PT_shoot"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"
    bl_order = CHILD_PANEL_BL_ORDER["BEHOLD_PT_shoot"]

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, SECTION_ICONS["shoot"])

    def draw(self, context: Context):
        draw_shoot_first_ship(self.layout, context)


class BEHOLD_PT_lights(Panel):
    bl_label = "Lights"
    bl_idname = "BEHOLD_PT_lights"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"
    bl_order = CHILD_PANEL_BL_ORDER["BEHOLD_PT_lights"]

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, SECTION_ICONS["lights"])

    def draw(self, context: Context):
        draw_lights_section(self.layout, context)


class BEHOLD_PT_cameras(Panel):
    bl_label = "Cameras"
    bl_idname = "BEHOLD_PT_cameras"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"
    bl_order = CHILD_PANEL_BL_ORDER["BEHOLD_PT_cameras"]

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, SECTION_ICONS["cameras"])

    def draw(self, context: Context):
        draw_cameras_section(self.layout, context)


class BEHOLD_PT_materials(Panel):
    bl_label = "Materials"
    bl_idname = "BEHOLD_PT_materials"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"
    bl_order = CHILD_PANEL_BL_ORDER["BEHOLD_PT_materials"]

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, SECTION_ICONS["materials"])

    def draw(self, context: Context):
        draw_materials_section(self.layout, context)


class BEHOLD_PT_advanced(Panel):
    bl_label = "Advanced"
    bl_idname = "BEHOLD_PT_advanced"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_parent_id = "BEHOLD_PT_main"
    bl_order = CHILD_PANEL_BL_ORDER["BEHOLD_PT_advanced"]
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, SECTION_ICONS["advanced"])

    def draw(self, context: Context):
        layout = self.layout
        draw_parked_heading(
            layout,
            "Import",
            SECTION_ICONS["import"],
            leading_separator=False,
        )
        draw_import_parked(layout, context)
        draw_parked_heading(layout, "Studio", SECTION_ICONS["studio"])
        draw_studio_parked(layout, context)
        draw_parked_heading(layout, "Materials / BlenderKit", SECTION_ICONS["materials"])
        draw_materials_parked(layout, context)
        draw_parked_heading(layout, "Light Draw", SECTION_ICONS["lights"])
        draw_light_draw_parked(layout, context)
        draw_parked_heading(layout, "Shoot", SECTION_ICONS["shoot"])
        draw_shoot_parked(layout, context)


# Registration order is N-panel order: Import → Studio → Lights → Materials →
# Cameras → Shoot → Advanced (matches FLOW_STEPS with Lights/Cameras as inventory).
CLASSES = (
    BEHOLD_PT_main,
    BEHOLD_PT_import,
    BEHOLD_PT_studio,
    BEHOLD_PT_lights,
    BEHOLD_PT_materials,
    BEHOLD_PT_cameras,
    BEHOLD_PT_shoot,
    BEHOLD_PT_advanced,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
