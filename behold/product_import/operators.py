# SPDX-License-Identifier: GPL-3.0-or-later
"""Unified Import Product operator."""

from __future__ import annotations

import os
from typing import Any, Never

import bpy
from bpy.props import BoolProperty, FloatProperty, StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ImportHelper

from ..cad import material_assist
from ..cad import operators as cad_ops
from ..ui.messages import (
    NO_FILE_SELECTED,
    report_set,
    unsupported_file_message,
)
from . import formats
from . import native


def apply_post_import(
    context: Context,
    filepath: str,
    *,
    auto_studio: bool,
    auto_material_assist: bool,
) -> list[str]:
    """Tag selection, optionally assist materials and build studio."""
    notes: list[str] = []
    material_assist.tag_selection_for_assist(context)
    meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]

    if auto_material_assist and meshes:
        try:
            kind = formats.product_import_dispatch(filepath)
            if kind == "cad":
                assist = material_assist.run_auto_dress(context, meshes)
            else:
                assist = material_assist.run_material_assist(context, meshes, filepath)
            if assist.get("ok"):
                notes.append(assist["message"])
            else:
                notes.append(assist.get("message") or "Material Assist skipped")
        except Exception:  # noqa: BLE001 — import must still finish
            notes.append("Material Assist failed")

    if auto_studio and meshes:
        try:
            result = bpy.ops.behold.build_studio()
            if "FINISHED" in result:
                notes.append("Studio built")
            else:
                notes.append("Studio skipped")
        except Exception:  # noqa: BLE001
            notes.append("Studio failed")

    return notes


def run_product_import(
    context: Context,
    filepath: str,
    *,
    deflection: float = 0.001,
    auto_studio: bool = True,
    auto_material_assist: bool = True,
) -> dict[str, Any]:
    """Same Import Product path as the file-browser operator (no GUI)."""
    kind = formats.product_import_dispatch(filepath)
    if kind == "unknown":
        ext = os.path.splitext(filepath)[1] or filepath
        return {
            "ok": False,
            "objects": [],
            "route": kind,
            "message": unsupported_file_message(ext),
        }
    if kind == "cad":
        result = cad_ops.import_cad_file(context, filepath, deflection=deflection)
    elif kind == "mesh":
        result = native.import_mesh_file(context, filepath)
    else:
        unreachable: Never = kind
        raise RuntimeError(f"unhandled import kind: {unreachable}")

    result = dict(result)
    result["route"] = kind
    if not result.get("ok"):
        return result

    notes = apply_post_import(
        context,
        filepath,
        auto_studio=auto_studio,
        auto_material_assist=auto_material_assist,
    )
    result["notes"] = notes
    return result


class BEHOLD_OT_import_product(Operator, ImportHelper):
    bl_idname = "behold.import_product"
    bl_label = "Import Product"
    bl_description = (
        "Import a product file (OBJ, FBX, STL, GLB/GLTF, 3MF, or STEP/IGES/BREP)"
    )
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ""
    filter_glob: StringProperty(
        default=formats.import_filter_glob(),
        options={"HIDDEN"},
    )
    auto_studio: BoolProperty(
        name="Build Studio",
        description="Run Build Studio on the imported mesh(es)",
        default=True,
    )
    auto_material_assist: BoolProperty(
        name="Material Assist",
        description=(
            "After CAD import, auto-dress each body from STEP color / name. "
            "Mesh files still get one Assist look. "
            "Searches BlenderKit only when signed in"
        ),
        default=True,
    )
    deflection: FloatProperty(
        name="CAD Deflection",
        description=(
            "OCP tessellation deflection for STEP/IGES/BREP (ignored for mesh). "
            "Passed to STEPper as lin_deflection_len only when that RNA prop exists"
        ),
        default=0.001,
        min=0.00001,
        soft_max=0.05,
    )

    def invoke(self, context: Context, event):
        settings = context.scene.behold
        self.auto_studio = settings.import_auto_studio
        self.auto_material_assist = settings.import_auto_material_assist
        return super().invoke(context, event)

    def draw(self, context: Context):
        layout = self.layout
        layout.prop(self, "auto_studio")
        layout.prop(self, "auto_material_assist")
        kind = formats.product_import_dispatch(self.filepath or "")
        if kind == "cad" or not self.filepath:
            layout.prop(self, "deflection")

    def execute(self, context: Context):
        filepath = self.filepath
        if not filepath:
            self.report(report_set(NO_FILE_SELECTED), NO_FILE_SELECTED)
            return {"CANCELLED"}

        settings = context.scene.behold
        settings.import_auto_studio = self.auto_studio
        settings.import_auto_material_assist = self.auto_material_assist

        result = run_product_import(
            context,
            filepath,
            deflection=self.deflection,
            auto_studio=self.auto_studio,
            auto_material_assist=self.auto_material_assist,
        )
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        notes = result.get("notes") or []
        suffix = f" — {'; '.join(notes)}" if notes else ""
        self.report({"INFO"}, result["message"] + suffix)
        return {"FINISHED"}


def _menu_import(self, _context: Context) -> None:
    self.layout.operator(
        BEHOLD_OT_import_product.bl_idname,
        text="BEHOLD Product (.obj/.fbx/.stl/.glb/.3mf/STEP…)",
    )


CLASSES = (BEHOLD_OT_import_product,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(_menu_import)


def unregister() -> None:
    bpy.types.TOPBAR_MT_file_import.remove(_menu_import)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
