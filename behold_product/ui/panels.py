# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD Product N-panel: Import, Materials, Cameras, Shoot, Advanced.

Studio and Lights live in the Studio / Lighting add-ons. Product keeps the
hero, flow strip, and Import → Materials → Cameras → Shoot path.
"""

from __future__ import annotations

from typing import Never

import bpy
from bpy.types import Context, Panel, UILayout

from ..cad import detect as cad_detect
from ..cad.regenerate import cached_label
from ..cad.defeaturing import DEFAULT_BLEND_MM, DEFAULT_HOLE_MM
from ..cad.stepper_api import import_panel_copy
from ..materials import blenderkit_bridge, local_rack
from ..materials.presets import EMPTY_NO_MESH, empty_state
from ..common.previews import mark_icon_kwargs
from ..product_import import formats
from ..shoot.batch import TOKEN_HINT as BATCH_TOKEN_HINT
from ..shoot.quality import SHOOT_ENGINE_HINT
from ..shoot import resolution as resolution_lib
from ..shoot import turntable as turntable_lib
from .. import cameras as camera_lib
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
    EMPTY_MATERIALS,
    EMPTY_SHOTS,
    SECTION_ICONS,
)
from ..common.messages import BATCH_NO_MESH, NO_MESH_SELECTED, NO_PRODUCT


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
    """Import Product picker plus CAD backend status, tessellation, cleanup."""
    card = layout.box()
    card.operator("behold.import_product", icon="IMPORT")
    draw_cad_status_line(layout, cad_detect.cad_status_for_draw())
    draw_import_tessellation(layout, context)
    draw_import_cleanup(layout, context)


def draw_import_tessellation(layout: UILayout, context: Context) -> None:
    """Retessellate the last CAD import without re-picking the file."""
    settings = context.scene.behold_product
    card = layout.box()
    card.label(text="Tessellation", icon="MOD_TRIANGULATE")
    card.label(text=cached_label(settings.cad_source_filepath))
    card.prop(settings, "cad_quality", text="Quality", expand=True)
    if settings.cad_quality == "CUSTOM":
        card.prop(settings, "cad_deflection", text="Deflection")
    card.label(text="Tessellate only — Cleanup is the next card")
    card.operator("behold.regenerate_cad", icon="FILE_REFRESH")


def draw_import_cleanup(layout: UILayout, context: Context) -> None:
    """Fillet / chamfer / hole suppress in millimetres, then retessellate."""
    settings = context.scene.behold_product
    card = layout.box()
    card.label(text="Cleanup", icon="MOD_BEVEL")
    row = card.row(align=True)
    row.prop(settings, "cad_cleanup_fillets", text="Fillets", toggle=True)
    row.prop(settings, "cad_cleanup_chamfers", text="Chamfers", toggle=True)
    row.prop(settings, "cad_cleanup_holes", text="Holes", toggle=True)
    sizes = card.column(align=True)
    sizes.active = (
        settings.cad_cleanup_fillets
        or settings.cad_cleanup_chamfers
        or settings.cad_cleanup_holes
    )
    if settings.cad_cleanup_fillets or settings.cad_cleanup_chamfers:
        sizes.prop(settings, "cad_blend_mm", text="Blend mm")
    if settings.cad_cleanup_holes:
        sizes.prop(settings, "cad_hole_mm", text="Hole Ø mm")
    if not (
        settings.cad_cleanup_fillets
        or settings.cad_cleanup_chamfers
        or settings.cad_cleanup_holes
    ):
        card.label(text=f"Off — default blend {DEFAULT_BLEND_MM:g} mm, holes Ø {DEFAULT_HOLE_MM:g} mm")
    else:
        card.label(text="OCP before tessellate — STEPper has no cleanup RNA")
    card.operator("behold.cleanup_cad", text="Apply cleanup", icon="MOD_BEVEL")








def draw_shoot_first_ship(layout: UILayout, context: Context) -> None:
    """Draft / Final, Size, Still, Exposure, Look, Shots, Batch export, Turntable."""
    settings = context.scene.behold_product
    card = layout.box()
    row = card.row(align=True)
    row.prop_enum(settings, "render_quality", "DRAFT")
    row.prop_enum(settings, "render_quality", "FINAL")
    card.label(text=SHOOT_ENGINE_HINT)
    card.operator("behold.render_still", text="Still", icon="RENDER_STILL")
    layout.separator()
    draw_resolution_compact(layout, context)
    layout.separator()
    draw_exposure_compact(layout, context)
    layout.separator()
    draw_look_compact(layout, context)
    layout.separator()
    draw_shots_compact(layout, context)
    layout.separator()
    draw_batch_compact(layout, context)
    layout.separator()
    draw_turntable_compact(layout, context)


def draw_resolution_compact(layout: UILayout, context: Context) -> None:
    """Aspect + pixel-size presets writing scene.render resolution."""
    settings = context.scene.behold_product
    card = layout.box()
    card.label(text="Size", icon="OUTPUT")
    row = card.row(align=True)
    row.prop(settings, "resolution_aspect", text="", expand=True)
    row = card.row(align=True)
    row.prop(settings, "resolution_size", text="", expand=True)
    card.label(
        text=resolution_lib.summary_label(
            settings.resolution_aspect,
            settings.resolution_size,
        )
    )


def draw_exposure_compact(layout: UILayout, context: Context) -> None:
    """EV, WB, False Color — Color Management, not compositor looks."""
    settings = context.scene.behold_product
    card = layout.box()
    card.label(text="Exposure", icon="COLOR")
    row = card.row(align=True)
    row.prop(settings, "exposure_ev", text="EV")
    row.prop(settings, "white_balance_kelvin", text="WB")
    card.prop(settings, "false_color", text="False Color", toggle=True)


def draw_look_compact(layout: UILayout, context: Context) -> None:
    """Clean / Catalog / Dramatic compositor presets."""
    settings = context.scene.behold_product
    card = layout.box()
    card.label(text="Look", icon="NODE_COMPOSITING")
    row = card.row(align=True)
    row.prop(settings, "look_preset", text="", expand=True)
    card.prop(settings, "look_enabled", text="Compositor", toggle=True)


def draw_shots_compact(layout: UILayout, context: Context) -> None:
    """Named shots: list, Add from current, Apply, inline rename, Delete."""
    settings = context.scene.behold_product
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


def draw_batch_compact(layout: UILayout, context: Context) -> None:
    """One-click catalog stills: standard angles and/or saved shots."""
    settings = context.scene.behold_product
    card = layout.box()
    card.label(text="Batch export", icon="CAMERA_DATA")
    row = card.row(align=True)
    row.prop(settings, "batch_include_angles", text="Front / ¾ / Top")
    row.prop(settings, "batch_include_shots", text="Saved shots")
    card.label(text=BATCH_TOKEN_HINT)
    card.operator("behold.batch_angles", text="Batch export", icon="RENDER_STILL")


def draw_turntable_compact(layout: UILayout, context: Context) -> None:
    """One row: seconds + Setup + Play. Empty-state if no camera or product."""
    settings = context.scene.behold_product
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












def draw_materials_section(layout: UILayout, context: Context) -> None:
    """Local PBR rack + Assist + Auto-dress. Empty-state if nothing dressable is selected."""
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
    row = card.row(align=True)
    row.operator("behold.cad_material_assist", text="Assist", icon="MATERIAL")
    row.operator("behold.cad_auto_dress", text="Auto-dress", icon="NODE_MATERIAL")

    status = blenderkit_bridge.blenderkit_status()
    if status["installed"] and status["logged_in"]:
        card.label(text="BlenderKit signed in — Assist also searches")
    else:
        card.label(text="Local looks — no BlenderKit account needed")


def draw_cameras_section(layout: UILayout, context: Context) -> None:
    """Product camera inventory: add / active / frame / delete."""
    settings = context.scene.behold_product
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
    draw_cameras_dof(layout, context)
    row = layout.row(align=True)
    row.prop(settings, "new_camera_lens", text="mm")
    row.operator("behold.add_camera", text="Add", icon="ADD")
    row.operator("behold.frame_camera", text="Frame", icon="ZOOM_SELECTED")
    row.operator("behold.clear_cameras", text="Clear", icon="TRASH")


def draw_cameras_dof(layout: UILayout, context: Context) -> None:
    """DoF on/off, product f-stop, Focus on product / Focus on selected."""
    settings = context.scene.behold_product
    card = layout.box()
    card.label(text="DoF", icon="CAMERA_DATA")
    row = card.row(align=True)
    row.prop(settings, "dof_enabled", text="DoF", toggle=True)
    row.prop(settings, "dof_fstop", text="f-stop")
    row = card.row(align=True)
    row.operator("behold.focus_product", text="Focus on product")
    row.operator("behold.focus_selected", text="Focus on selected")


def draw_import_parked(layout: UILayout, context: Context) -> None:
    """Auto-studio / Material Assist toggles and CAD backend (parked)."""
    settings = context.scene.behold_product
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
    row.operator("behold.cad_auto_dress", text="Auto-dress", icon="NODE_MATERIAL")
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

    tess = layout.box()
    tess.label(text="Tessellation", icon="MOD_TRIANGULATE")
    tess.prop(settings, "cad_quality", text="Quality")
    tess.prop(settings, "cad_deflection", text="Deflection")
    tess.operator("behold.regenerate_cad", text="Apply tessellation", icon="FILE_REFRESH")

    clean = layout.box()
    clean.label(text="Cleanup", icon="MOD_BEVEL")
    clean.prop(settings, "cad_cleanup_fillets")
    clean.prop(settings, "cad_cleanup_chamfers")
    clean.prop(settings, "cad_cleanup_holes")
    clean.prop(settings, "cad_blend_mm", text="Blend mm")
    clean.prop(settings, "cad_hole_mm", text="Hole Ø mm")
    clean.operator("behold.cleanup_cad", text="Apply cleanup", icon="MOD_BEVEL")




def draw_materials_parked(layout: UILayout, context: Context) -> None:
    """BlenderKit chrome (parked). Local rack buttons stay for Advanced users."""
    settings = context.scene.behold_product

    layout.label(text="Local PBR rack")
    grid = layout.grid_flow(columns=3, align=True)
    for key, data in local_rack.PRESETS.items():
        op = grid.operator("behold.apply_local_material", text=data["label"])
        op.preset = key
    layout.operator("behold.cad_material_assist", text="Assist", icon="MATERIAL")
    layout.operator("behold.cad_auto_dress", text="Auto-dress", icon="NODE_MATERIAL")

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




def draw_shoot_parked(layout: UILayout, context: Context) -> None:
    """Tokens / bookmark / batch duplicate / turntable extras (Look lives on Shoot)."""
    settings = context.scene.behold_product
    has_camera = context.scene.camera is not None or bool(settings.main_camera_name)
    snap = scene_snap_from_context(context)
    has_product = snap.has_product or snap.has_selected_mesh

    if not has_camera:
        box = layout.box()
        box.label(text=turntable_lib.EMPTY_NO_CAMERA, icon="INFO")
        box.operator("behold.build_studio", text="Build Studio", icon="OUTLINER_OB_LIGHT")

    col = layout.column(align=True)
    col.label(text="Exposure")
    col.prop(settings, "exposure_ev")
    col.prop(settings, "white_balance_kelvin")
    col.prop(settings, "false_color", toggle=True)
    col.operator("behold.apply_exposure", icon="COLOR")

    layout.separator()
    col = layout.column(align=True)
    col.label(text="Look")
    col.prop(settings, "look_preset", text="", expand=True)
    col.prop(settings, "look_enabled", text="Compositor", toggle=True)
    col.operator("behold.apply_look", icon="NODE_COMPOSITING")

    layout.separator()
    col = layout.column(align=True)
    col.label(text="Quality")
    col.label(text=SHOOT_ENGINE_HINT)
    col.prop(settings, "render_quality", text="")
    col.operator("behold.apply_quality", icon="SETTINGS")

    layout.separator()
    col = layout.column(align=True)
    col.label(text="Size")
    col.prop(settings, "resolution_aspect", text="", expand=True)
    col.prop(settings, "resolution_size", text="", expand=True)
    col.label(
        text=resolution_lib.summary_label(
            settings.resolution_aspect,
            settings.resolution_size,
        )
    )
    col.operator("behold.apply_resolution", icon="OUTPUT")

    layout.separator()
    col = layout.column(align=True)
    col.label(text="Camera")
    row = col.row(align=True)
    row.operator("behold.bookmark_camera", text="Bookmark")
    row.operator("behold.use_main_camera", text="Use Main")
    if settings.main_camera_name:
        col.label(text=f"Main: {settings.main_camera_name}", icon="CAMERA_DATA")
    col.prop(settings, "dof_enabled", text="DoF", toggle=True)
    col.prop(settings, "dof_fstop", text="f-stop")
    row = col.row(align=True)
    row.operator("behold.focus_product", text="Focus on product")
    row.operator("behold.focus_selected", text="Focus on selected")
    col.operator("behold.apply_camera_dof", icon="CAMERA_DATA")

    layout.separator()
    col = layout.column(align=True)
    col.label(text="Output")
    col.prop(settings, "output_directory", text="")
    col.label(text=BATCH_TOKEN_HINT)

    layout.separator()
    col = layout.column(align=True)
    col.label(text="Batch export")
    row = col.row(align=True)
    row.prop(settings, "batch_include_angles", text="Front / ¾ / Top")
    row.prop(settings, "batch_include_shots", text="Saved shots")
    if not has_product:
        box = layout.box()
        box.label(text=BATCH_NO_MESH, icon="INFO")
        if not _has_imported_product(context):
            box.operator("behold.import_product", icon="IMPORT")
    layout.operator("behold.batch_angles", text="Batch export", icon="CAMERA_DATA")

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
        draw_parked_heading(layout, "Materials / BlenderKit", SECTION_ICONS["materials"])
        draw_materials_parked(layout, context)
        draw_parked_heading(layout, "Shoot", SECTION_ICONS["shoot"])
        draw_shoot_parked(layout, context)


# Registration order is N-panel order: Import → Studio → Lights → Materials →
# Cameras → Shoot → Advanced (matches FLOW_STEPS with Lights/Cameras as inventory).
CLASSES = (
    BEHOLD_PT_main,
    BEHOLD_PT_import,
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
