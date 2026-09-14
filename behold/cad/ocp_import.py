# SPDX-License-Identifier: GPL-3.0-or-later
"""Thin OCP / OpenCASCADE STEP / IGES / BREP to Blender mesh importer."""

from __future__ import annotations

import os
from typing import Any

import bpy

from . import ocp_core
from ..product_import.invoke import format_file_not_found_message


def import_cad_with_ocp(
    filepath: str,
    *,
    deflection: float = 0.001,
    collection_name: str | None = None,
) -> dict[str, Any]:
    """Read a STEP / IGES / BREP file via OCP, tessellate, and create mesh objects."""
    path = bpy.path.abspath(filepath)
    if not path or not os.path.isfile(path):
        return {
            "ok": False,
            "objects": [],
            "message": format_file_not_found_message(filepath),
        }

    try:
        ocp_core.ensure_ocp()
    except ImportError as exc:
        return {"ok": False, "objects": [], "message": f"OCP not available ({exc})"}

    shape, error = ocp_core.read_cad_shape(path)
    if error or shape is None:
        return {"ok": False, "objects": [], "message": error or "No shape"}

    all_verts, all_faces = ocp_core.tessellate_shape(shape, deflection=deflection)
    if not all_verts or not all_faces:
        return {
            "ok": False,
            "objects": [],
            "message": "Tessellation produced no triangles — try a finer deflection",
        }

    stem = os.path.splitext(os.path.basename(path))[0] or "BEHOLD_CAD"
    mesh = bpy.data.meshes.new(f"{stem}_Mesh")
    mesh.from_pydata(list(all_verts), [], list(all_faces))
    mesh.validate(clean_customdata=False)
    mesh.update()

    obj = bpy.data.objects.new(stem, mesh)
    obj["BEHOLD_cad_source"] = path
    obj["BEHOLD_cad_backend"] = "OCP"
    obj["BEHOLD_product_source"] = path
    obj["BEHOLD_product_backend"] = "OCP"

    col_name = collection_name or f"BEHOLD_CAD_{stem}"
    collection = bpy.data.collections.get(col_name)
    if collection is None:
        collection = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(collection)
    collection.objects.link(obj)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    return {
        "ok": True,
        "objects": [obj],
        "message": f"Imported “{stem}” via OCP ({len(all_faces)} tris)",
    }


def import_step_with_ocp(
    filepath: str,
    *,
    deflection: float = 0.001,
    collection_name: str | None = None,
) -> dict[str, Any]:
    """Backward-compatible alias for STEP-oriented callers."""
    return import_cad_with_ocp(
        filepath,
        deflection=deflection,
        collection_name=collection_name,
    )
