# SPDX-License-Identifier: GPL-3.0-or-later
"""Native BEHOLD N-panel chrome: hero, flow strip, cards, empty states."""

from __future__ import annotations

from bpy.types import Context, UILayout

from ..brand import PRODUCT_CREDIT, PRODUCT_NAME
from ..cad import material_assist
from ..draw_cache import SCENE_SNAP_KEY, draw_get
from ..materials.presets import is_dressable_mesh_name
from ..preferences import get_prefs
from ..previews import draw_mark_label
from ..studio import cameras as camera_lib
from ..studio import lights as light_lib
from ..updates.core import (
    available_from_cache,
    failure_copy,
    installed_version,
)
from ..updates.runtime import notice_is_dismissed
from .flow import (
    FLOW_STEPS,
    EmptyState,
    FlowStepId,
    cta_for_step,
    flow_completed,
    is_look_material_name,
    next_step,
)
from .scene_scan import ObjectDrawRow, SceneDrawSnap, snap_from_rows


def draw_hero(layout: UILayout) -> None:
    box = layout.box()
    draw_mark_label(box, PRODUCT_NAME)
    box.label(text=PRODUCT_CREDIT)


def draw_update_notice(layout: UILayout, context: Context) -> None:
    """Session-dismissible notice: newer zip, or a failed check/install."""
    if notice_is_dismissed():
        return
    prefs = get_prefs(context)
    if prefs is None:
        return
    update = available_from_cache(
        getattr(prefs, "update_latest_tag", "") or "",
        installed=installed_version(),
        html_url=getattr(prefs, "update_latest_url", "") or "",
        zip_url=getattr(prefs, "update_latest_zip_url", "") or "",
    )
    error = getattr(prefs, "update_last_error", "") or ""
    busy = bool(getattr(prefs, "update_checking", False)) or bool(
        getattr(prefs, "update_installing", False)
    )
    if busy:
        error = ""
    if update is None and not error:
        return
    box = layout.box()
    if error:
        copy = failure_copy(
            kind=getattr(prefs, "update_error_kind", "") or "",
            error=error,
        )
        box.label(text=copy["line"], icon="ERROR")
        box.label(text=copy["detail"])
    elif update is not None:
        box.label(text=f"Update available: {update['version']}", icon="INFO")
    row = box.row(align=True)
    if error and update is None:
        row.operator("behold.check_updates", text="Check again", icon="FILE_REFRESH")
    elif update is not None and update.get("zip_url"):
        row.operator("behold.install_update", text="Install", icon="IMPORT")
    row.operator("behold.open_release", text="Open release", icon="URL")
    row.operator("behold.dismiss_update", text="", icon="X")


def draw_section_icon(layout: UILayout, icon: str) -> None:
    layout.label(text="", icon=icon)


def draw_parked_heading(
    layout: UILayout,
    text: str,
    icon: str,
    *,
    leading_separator: bool = True,
) -> None:
    if leading_separator:
        layout.separator()
    layout.label(text=text, icon=icon)


def draw_empty_card(
    layout: UILayout,
    spec: EmptyState,
) -> UILayout:
    """One primary CTA. Callers may add a quieter secondary control on the box."""
    box = layout.box()
    box.label(text=spec.title, icon="INFO")
    if spec.hint:
        box.label(text=spec.hint)
    box.operator(spec.operator, text=spec.operator_text, icon=spec.icon)
    return box


def _object_draw_rows(context: Context) -> list[ObjectDrawRow]:
    selected = {obj.name for obj in context.selected_objects}
    rows: list[ObjectDrawRow] = []
    for obj in context.scene.objects:
        ob_type = obj.type
        is_mesh = ob_type == "MESH"
        rows.append(
            ObjectDrawRow(
                name=obj.name,
                ob_type=ob_type,
                tagged_product=is_mesh and material_assist.is_behold_product(obj),
                has_look=(
                    is_mesh
                    and is_dressable_mesh_name(obj.name)
                    and _mesh_has_look(obj)
                ),
                selected=obj.name in selected,
                is_behold_light=ob_type == "LIGHT" and light_lib.is_behold_light(obj),
                is_behold_camera=ob_type == "CAMERA" and camera_lib.is_behold_camera(obj),
            )
        )
    return rows


def scene_snap_from_context(context: Context) -> SceneDrawSnap:
    """Product / studio / look / camera flags from one ``scene.objects`` walk."""

    def load() -> SceneDrawSnap:
        return snap_from_rows(
            _object_draw_rows(context),
            has_scene_camera=context.scene.camera is not None,
        )

    return draw_get(SCENE_SNAP_KEY, load)


def flow_state_from_context(context: Context) -> dict[FlowStepId, bool]:
    snap = scene_snap_from_context(context)
    return flow_completed(
        has_product=snap.has_product,
        has_studio=snap.has_studio,
        has_look=snap.has_look,
        has_camera=snap.has_camera,
    )


def draw_flow_strip(layout: UILayout, context: Context) -> None:
    prefs = get_prefs(context)
    if prefs is not None and not prefs.show_flow_strip:
        return

    completed = flow_state_from_context(context)
    nxt = next_step(completed)
    box = layout.box()
    row = box.row(align=True)
    last_index = len(FLOW_STEPS) - 1
    for index, step in enumerate(FLOW_STEPS):
        done = completed[step.id]
        is_next = step.id == nxt
        cell = row.column(align=True)
        cell.enabled = done or is_next
        icon = "CHECKMARK" if done else step.icon
        cell.label(text=step.label, icon=icon)
        if index < last_index:
            arrow = row.column(align=True)
            arrow.enabled = done
            arrow.label(text="", icon="TRIA_RIGHT")

    if nxt is None:
        box.operator("behold.render_still", text="Still", icon="RENDER_STILL")
        return
    cta = cta_for_step(nxt)
    box.operator(cta.operator, text=f"Next: {cta.label}", icon=cta.icon)


def _mesh_has_look(obj) -> bool:
    for slot in obj.material_slots:
        mat = slot.material
        if mat is not None and is_look_material_name(mat.name):
            return True
    return False
