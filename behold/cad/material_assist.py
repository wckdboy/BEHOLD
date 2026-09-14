# SPDX-License-Identifier: GPL-3.0-or-later
"""Suggest looks from CAD part names and apply a local rack material."""

from __future__ import annotations

from typing import Any

import bpy
from bpy.types import Context, Object

from ..materials import blenderkit_bridge, local_rack
from ..materials.presets import EMPTY_NO_MESH, assist_summary, plan_assist
from .hints import suggest_query_from_parts


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


def tag_selection_for_assist(context: Context) -> None:
    """Mark selected meshes so Studio / Assist can find them later."""
    for obj in context.selected_objects:
        if obj.type != "MESH":
            continue
        obj["BEHOLD_material_assist"] = True
        if "BEHOLD_material_hint" not in obj:
            obj["BEHOLD_material_hint"] = suggest_query_for_objects([obj])


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
