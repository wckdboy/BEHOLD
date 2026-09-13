# SPDX-License-Identifier: GPL-3.0-or-later
"""Suggest BlenderKit material queries from CAD part names and colors."""

from __future__ import annotations

from bpy.types import Context, Object

from .hints import DEFAULT_QUERY, suggest_query_for_path, suggest_query_for_text


def suggest_query_for_objects(objects: list[Object], filepath: str = "") -> str:
    """Return a BlenderKit-friendly search string from selection metadata."""
    for obj in objects:
        for prop in ("STEP_material", "STEP_material_name", "BEHOLD_material_hint"):
            value = obj.get(prop)
            if isinstance(value, str) and value.strip():
                hinted = suggest_query_for_text(value) or value.strip()
                return hinted

        hit = suggest_query_for_text(obj.name)
        if hit:
            return hit

        for slot in obj.material_slots:
            mat = slot.material
            if mat is None:
                continue
            hit = suggest_query_for_text(mat.name)
            if hit:
                return hit
            clean = mat.name.replace("_", " ").strip()
            if clean and clean.lower() not in {"material", "material.001"}:
                return clean

    if filepath:
        return suggest_query_for_path(filepath)
    return DEFAULT_QUERY


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
