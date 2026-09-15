# SPDX-License-Identifier: GPL-3.0-or-later
"""Suggest looks from CAD part names and apply a local rack material."""

from __future__ import annotations

from typing import Any

import bpy
from bpy.types import Context, Object

from ..materials import blenderkit_bridge, local_rack
from ..materials.presets import EMPTY_NO_MESH, assist_summary, plan_assist
from .auto_dress import (
    AUTO_DRESS_FAILED,
    BodyHint,
    auto_dress_summary,
    plan_bodies,
    rgb_from_any,
    usable_color,
)
from .hints import suggest_query_from_parts, suggest_query_from_parts_or_none


def suggest_query_for_objects(objects: list[Object], filepath: str = "") -> str:
    """Return a BlenderKit-friendly search string from selection metadata."""
    custom_hints: list[str] = []
    names: list[str] = []
    material_names: list[str] = []
    for obj in objects:
        for prop in ("STEP_material", "STEP_material_name", "BEHOLD_material_hint"):
            value = obj.get(prop)
            if isinstance(value, str) and value.strip():
                custom_hints.append(value)
        names.append(obj.name)
        for slot in obj.material_slots:
            mat = slot.material
            if mat is not None:
                material_names.append(mat.name)
    return suggest_query_from_parts(
        custom_hints=custom_hints,
        names=names,
        material_names=material_names,
        filepath=filepath,
    )


def _slot_material_names(obj: Object) -> list[str]:
    names: list[str] = []
    for slot in obj.material_slots:
        mat = slot.material
        if mat is not None and mat.name:
            names.append(mat.name)
    return names


def _color_from_material(mat) -> tuple[float, float, float] | None:
    parsed = rgb_from_any(getattr(mat, "diffuse_color", None))
    hit = usable_color(parsed)
    if hit is not None:
        return hit
    tree = getattr(mat, "node_tree", None)
    if tree is None:
        return None
    nodes = getattr(tree, "nodes", None)
    if nodes is None:
        return None
    principled = nodes.get("Principled BSDF") if hasattr(nodes, "get") else None
    if principled is None:
        for candidate in nodes:
            if getattr(candidate, "type", "") == "BSDF_PRINCIPLED":
                principled = candidate
                break
    if principled is None:
        return None
    try:
        socket = principled.inputs.get("Base Color")
    except Exception:  # noqa: BLE001 — bpy RNA collections vary
        socket = None
    if socket is None:
        return None
    return usable_color(rgb_from_any(getattr(socket, "default_value", None)))


def body_hint_from_object(obj: Object) -> BodyHint:
    """Collect STEP name / color clues from one imported mesh."""
    custom_hints: list[str] = []
    for prop in ("STEP_material", "STEP_material_name", "BEHOLD_material_hint"):
        value = obj.get(prop)
        if isinstance(value, str) and value.strip():
            custom_hints.append(value)
    color = None
    for prop in ("STEP_color", "BEHOLD_step_color"):
        value = obj.get(prop)
        parsed = usable_color(rgb_from_any(value))
        if parsed is not None:
            color = parsed
            break
    if color is None:
        for slot in obj.material_slots:
            mat = slot.material
            if mat is None:
                continue
            parsed = _color_from_material(mat)
            if parsed is not None:
                color = parsed
                break
    if color is None:
        color = usable_color(rgb_from_any(getattr(obj, "color", None)))
    return BodyHint(
        name=obj.name,
        custom_hints=tuple(custom_hints),
        material_names=tuple(_slot_material_names(obj)),
        color=color,
    )


def tag_selection_for_assist(context: Context) -> None:
    """Mark selected meshes so Studio / Assist can find them later."""
    for obj in context.selected_objects:
        if obj.type != "MESH":
            continue
        obj["BEHOLD_material_assist"] = True
        if "BEHOLD_material_hint" in obj:
            continue
        hinted = suggest_query_from_parts_or_none(
            names=[obj.name],
            material_names=_slot_material_names(obj),
        )
        if hinted:
            obj["BEHOLD_material_hint"] = hinted


def is_behold_product(obj: Object) -> bool:
    return bool(obj.get("BEHOLD_product_source") or obj.get("BEHOLD_cad_source"))


def run_material_assist(
    context: Context,
    meshes: list[Object],
    filepath: str = "",
) -> dict[str, Any]:
    """Apply a matching local look. Search BlenderKit only when signed in."""
    targets = local_rack.dressable_meshes(meshes)
    if not targets:
        return {
            "ok": False,
            "applied": 0,
            "searched": False,
            "query": "",
            "preset_id": "",
            "message": EMPTY_NO_MESH,
        }

    source = filepath
    if not source:
        for obj in targets:
            value = obj.get("BEHOLD_product_source") or obj.get("BEHOLD_cad_source")
            if isinstance(value, str) and value:
                source = value
                break

    query = suggest_query_for_objects(targets, source)
    context.scene.behold.blenderkit_query = query
    tag_selection_for_assist(context)

    try:
        status = blenderkit_bridge.blenderkit_status()
    except Exception:  # noqa: BLE001 — local apply must not depend on BlenderKit
        status = {"installed": False, "logged_in": False}

    plan = plan_assist(query, status)
    applied = 0
    if plan.apply_local:
        applied = local_rack.apply_to_objects(targets, plan.preset_id)

    searched = False
    if plan.search_blenderkit:
        try:
            result = bpy.ops.behold.blenderkit_search()
            searched = "FINISHED" in result or "RUNNING_MODAL" in result
        except Exception:  # noqa: BLE001 — search is optional; local look already applied
            searched = False

    return {
        "ok": True,
        "applied": applied,
        "searched": searched,
        "query": plan.query,
        "preset_id": plan.preset_id,
        "message": assist_summary(plan, applied=applied, searched=searched),
    }


def run_auto_dress(
    context: Context,
    meshes: list[Object],
) -> dict[str, Any]:
    """Assign a local look per body. Does not replace single-look Assist."""
    targets = local_rack.dressable_meshes(meshes)
    if not targets:
        return {
            "ok": False,
            "applied": 0,
            "skipped": 0,
            "plans": [],
            "message": EMPTY_NO_MESH,
        }

    plans = plan_bodies([body_hint_from_object(obj) for obj in targets])
    applied = 0
    try:
        for obj, plan in zip(targets, plans):
            if plan.source == "skip":
                continue
            applied += local_rack.apply_look_to_objects(
                [obj],
                plan.preset_id,
                material_name=plan.material_name,
                base_color=plan.base_color,
            )
    except Exception:  # noqa: BLE001 — keep the report actionable
        return {
            "ok": False,
            "applied": applied,
            "skipped": sum(1 for plan in plans if plan.source == "skip"),
            "plans": list(plans),
            "message": AUTO_DRESS_FAILED,
        }

    if context is not None and getattr(context, "selected_objects", None) is not None:
        tag_selection_for_assist(context)

    skipped = sum(1 for plan in plans if plan.source == "skip")
    return {
        "ok": applied > 0,
        "applied": applied,
        "skipped": skipped,
        "plans": list(plans),
        "message": auto_dress_summary(plans, applied=applied),
    }
