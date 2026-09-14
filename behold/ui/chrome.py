# SPDX-License-Identifier: GPL-3.0-or-later
"""Native BEHOLD N-panel chrome: hero, flow strip, cards, empty states."""

from __future__ import annotations

from bpy.types import Context, UILayout

from ..cad import material_assist
from ..materials.presets import is_dressable_mesh_name
from ..preferences import get_prefs
from ..studio import cameras as camera_lib
from ..studio import lights as light_lib
from ..brand import HERO_ICON, PRODUCT_CREDIT, PRODUCT_NAME
from .flow import (
    FLOW_STEPS,
    EmptyState,
    FlowStepId,
    cta_for_step,
    flow_completed,
    is_look_material_name,
    next_step,
    product_present,
    studio_present,
)


def draw_hero(layout: UILayout) -> None:
    box = layout.box()
    box.label(text=PRODUCT_NAME, icon=HERO_ICON)
    box.label(text=PRODUCT_CREDIT)


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


def flow_state_from_context(context: Context) -> dict[FlowStepId, bool]:
    meshes = [obj.name for obj in context.scene.objects if obj.type == "MESH"]
    tagged = any(
        obj.type == "MESH" and material_assist.is_behold_product(obj)
        for obj in context.scene.objects
    )
    has_product = product_present(mesh_names=meshes, tagged_product=tagged)
    has_studio = studio_present(
        mesh_names=meshes,
        has_behold_light=bool(light_lib.iter_behold_lights(context)),
    )
    has_look = any(
        _mesh_has_look(obj)
        for obj in context.scene.objects
        if obj.type == "MESH" and is_dressable_mesh_name(obj.name)
    )
    has_camera = bool(camera_lib.iter_behold_cameras(context)) or (
        context.scene.camera is not None
    )
    return flow_completed(
        has_product=has_product,
        has_studio=has_studio,
        has_look=has_look,
        has_camera=has_camera,
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
