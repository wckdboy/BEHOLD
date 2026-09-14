# SPDX-License-Identifier: GPL-3.0-or-later
"""Invoke Blender's built-in mesh importers."""

from __future__ import annotations

import os
from typing import Any

import bpy

from .formats import extension_of, mesh_operator_candidates
from .invoke import (
    format_empty_mesh_import_message,
    format_mesh_import_failure,
    format_no_mesh_operator_message,
    mesh_import_kwarg_attempts,
)


def operator_available(op_id: str) -> bool:
    try:
        path, name = op_id.split(".", 1)
        category = getattr(bpy.ops, path, None)
        if category is None:
            return False
        return getattr(category, name, None) is not None
    except Exception:  # noqa: BLE001
        return False


def _operator_from_id(op_id: str):
    path, name = op_id.split(".", 1)
    return getattr(getattr(bpy.ops, path), name)


def invoke_import_operator(op_id: str, filepath: str) -> tuple[bool, str | None]:
    """Call a Blender import operator. Returns (ok, error)."""
    try:
        op = _operator_from_id(op_id)
    except AttributeError:
        return False, f"{op_id} is not registered"

    abs_path = bpy.path.abspath(filepath)
    errors: list[str] = []
    for kwargs in mesh_import_kwarg_attempts(abs_path):
        try:
            result = op("EXEC_DEFAULT", **kwargs)
        except TypeError as exc:
            errors.append(f"TypeError ({sorted(kwargs)}): {exc}")
            continue
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{type(exc).__name__}: {exc}")
            continue
        if "FINISHED" in result or "RUNNING_MODAL" in result:
            return True, None
        errors.append(f"returned {set(result)}")
    if not errors:
        return False, f"{op_id} did not accept any known filepath kwargs"
    return False, "; ".join(errors)


def import_mesh_file(context, filepath: str) -> dict[str, Any]:
    """Import a mesh interchange file with native Blender operators."""
    abs_path = bpy.path.abspath(filepath)
    if not abs_path or not os.path.isfile(abs_path):
        return {"ok": False, "objects": [], "message": f"File not found: {filepath}"}

    ext = extension_of(abs_path)
    candidates = mesh_operator_candidates(abs_path)
    available_ops = [op_id for op_id in candidates if operator_available(op_id)]
    if not available_ops:
        return {
            "ok": False,
            "objects": [],
            "message": format_no_mesh_operator_message(ext, candidates),
        }

    before = {obj.as_pointer() for obj in bpy.data.objects}
    errors: list[str] = []
    used_op: str | None = None
    for op_id in available_ops:
        ok, error = invoke_import_operator(op_id, abs_path)
        if ok:
            used_op = op_id
            break
        errors.append(f"{op_id}: {error}" if error else op_id)

    if used_op is None:
        return {
            "ok": False,
            "objects": [],
            "message": format_mesh_import_failure(
                abs_path,
                operator_id=", ".join(available_ops),
                errors=errors,
            ),
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
            "message": format_empty_mesh_import_message(used_op),
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
        "message": f"Imported {len(imported)} mesh(es) via {used_op} ({names}{extra})",
        "backend": f"NATIVE_{ext.lstrip('.').upper()}",
    }
