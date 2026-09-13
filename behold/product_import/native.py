# SPDX-License-Identifier: GPL-3.0-or-later
"""Invoke Blender's built-in mesh importers."""

from __future__ import annotations

import os
from typing import Any

import bpy

from .formats import extension_of, mesh_operator_candidates


def operator_available(op_id: str) -> bool:
    try:
        path, name = op_id.split(".", 1)
        category = getattr(bpy.ops, path, None)
        if category is None:
            return False
        return getattr(category, name, None) is not None
    except Exception:  # noqa: BLE001
        return False


def first_available_operator(op_ids: tuple[str, ...]) -> str | None:
    for op_id in op_ids:
        if operator_available(op_id):
            return op_id
    return None


def invoke_import_operator(op_id: str, filepath: str) -> bool:
    """Call a Blender import operator with a filepath. Returns True on success."""
    try:
        path, name = op_id.split(".", 1)
        op = getattr(getattr(bpy.ops, path), name)
    except AttributeError:
        return False

    abs_path = bpy.path.abspath(filepath)
    directory = os.path.dirname(abs_path)
    basename = os.path.basename(abs_path)
    attempts = (
        {"filepath": abs_path},
        {
            "filepath": abs_path,
            "directory": directory,
            "files": [{"name": basename}],
        },
        {"directory": directory, "files": [{"name": basename}]},
    )
    for kwargs in attempts:
        try:
            result = op("EXEC_DEFAULT", **kwargs)
            if "FINISHED" in result or "RUNNING_MODAL" in result:
                return True
        except TypeError:
            continue
        except Exception:  # noqa: BLE001
            continue
    return False


def import_mesh_file(context, filepath: str) -> dict[str, Any]:
    """Import a mesh interchange file with native Blender operators."""
    abs_path = bpy.path.abspath(filepath)
    if not abs_path or not os.path.isfile(abs_path):
        return {"ok": False, "objects": [], "message": f"File not found: {filepath}"}

    ext = extension_of(abs_path)
    candidates = mesh_operator_candidates(abs_path)
    available = first_available_operator(candidates)
    if available is None:
        if ext == ".3mf":
            return {
                "ok": False,
                "objects": [],
                "message": (
                    "This Blender has no 3MF importer. Install a 3MF add-on "
                    "(File → Import) or export OBJ / STL / GLB instead."
                ),
            }
        return {
            "ok": False,
            "objects": [],
            "message": f"No native importer found for {ext or 'this file'}",
        }

    before = {obj.as_pointer() for obj in bpy.data.objects}
    if not invoke_import_operator(available, abs_path):
        return {
            "ok": False,
            "objects": [],
            "message": f"{available} failed to import {os.path.basename(abs_path)}",
        }

    imported = [
        obj
        for obj in bpy.data.objects
        if obj.as_pointer() not in before and obj.type == "MESH"
    ]
    if not imported:
        return {
            "ok": False,
            "objects": [],
            "message": f"Importer ran but produced no mesh objects ({available})",
        }

    bpy.ops.object.select_all(action="DESELECT")
    for obj in imported:
        obj.select_set(True)
        obj["BEHOLD_product_source"] = abs_path
        obj["BEHOLD_product_backend"] = f"NATIVE_{ext.lstrip('.').upper()}"
    context.view_layer.objects.active = imported[0]

    names = ", ".join(obj.name for obj in imported[:3])
    extra = f" +{len(imported) - 3}" if len(imported) > 3 else ""
    return {
        "ok": True,
        "objects": imported,
        "message": f"Imported {len(imported)} mesh(es) via {available} ({names}{extra})",
        "backend": f"NATIVE_{ext.lstrip('.').upper()}",
    }
