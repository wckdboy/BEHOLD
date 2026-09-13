# SPDX-License-Identifier: GPL-3.0-or-later
"""Suggest BlenderKit material queries from CAD part names and colors."""

from __future__ import annotations

import re

from bpy.types import Context, Object


_NAME_HINTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"alum|al[\s_-]?6061|al[\s_-]?7075", re.I), "brushed aluminum"),
    (re.compile(r"steel|ss[\s_-]?304|inox", re.I), "brushed steel"),
    (re.compile(r"brass|bronze", re.I), "brass metal"),
    (re.compile(r"copper", re.I), "copper metal"),
    (re.compile(r"plastic|abs|pla|nylon|pom|delrin|pc\b|polycarb", re.I), "abs plastic"),
    (re.compile(r"rubber|tpu|silicone|gasket", re.I), "matte rubber"),
    (re.compile(r"glass|lens|acrylic|pmma", re.I), "clear glass"),
    (re.compile(r"paint|coated|anodiz", re.I), "matte paint"),
    (re.compile(r"chrome|mirror|polish", re.I), "chrome metal"),
)


def suggest_query_for_objects(objects: list[Object]) -> str:
    """Return a BlenderKit-friendly search string from selection metadata."""
    for obj in objects:
        for prop in ("STEP_material", "STEP_material_name", "BEHOLD_material_hint"):
            value = obj.get(prop)
            if isinstance(value, str) and value.strip():
                return value.strip()

        for pattern, query in _NAME_HINTS:
            if pattern.search(obj.name):
                return query

        for slot in obj.material_slots:
            mat = slot.material
            if mat is None:
                continue
            for pattern, query in _NAME_HINTS:
                if pattern.search(mat.name):
                    return query
            clean = mat.name.replace("_", " ").strip()
            if clean and clean.lower() not in {"material", "material.001"}:
                return clean

    return "brushed metal"


def tag_selection_for_assist(context: Context) -> None:
    """Mark selected meshes so Studio / Assist can find them later."""
    for obj in context.selected_objects:
        if obj.type != "MESH":
            continue
        obj["BEHOLD_material_assist"] = True
        if "BEHOLD_material_hint" not in obj:
            obj["BEHOLD_material_hint"] = suggest_query_for_objects([obj])
