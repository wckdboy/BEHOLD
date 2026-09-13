# SPDX-License-Identifier: GPL-3.0-or-later
"""Unified Import Product operator."""

from __future__ import annotations

import os

import bpy
from bpy.props import BoolProperty, FloatProperty, StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ImportHelper

from ..cad import material_assist
from ..cad import operators as cad_ops
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
        query = material_assist.suggest_query_for_objects(meshes, filepath)
        context.scene.behold.blenderkit_query = query
        try:
            bpy.ops.behold.blenderkit_search()
            notes.append(f"Material Assist “{query}”")
        except Exception:  # noqa: BLE001
            notes.append(f"Material Assist query “{query}”")

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
        description="Set a BlenderKit query from the filename and imported names",
        default=True,
    )
    deflection: FloatProperty(
        name="CAD Deflection",
        description="OCP tessellation deflection for STEP/IGES/BREP (ignored for mesh)",
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
        kind = formats.classify_product_file(self.filepath or "")
        if kind == "cad" or not self.filepath:
            layout.prop(self, "deflection")

    def execute(self, context: Context):
        filepath = self.filepath
        if not filepath:
            self.report({"ERROR"}, "No file selected")
            return {"CANCELLED"}

        settings = context.scene.behold
        settings.import_auto_studio = self.auto_studio
        settings.import_auto_material_assist = self.auto_material_assist

        kind = formats.classify_product_file(filepath)
        if kind == "unknown":
            self.report(
                {"ERROR"},
                f"Unsupported file type: {os.path.splitext(filepath)[1] or filepath}",
            )
            return {"CANCELLED"}

        if kind == "cad":
            result = cad_ops.import_cad_file(
                context,
                filepath,
                deflection=self.deflection,
            )
        else:
            result = native.import_mesh_file(context, filepath)

        if not result["ok"]:
            self.report({"ERROR"}, result["message"])
            return {"CANCELLED"}

        notes = apply_post_import(
            context,
            filepath,
            auto_studio=self.auto_studio,
            auto_material_assist=self.auto_material_assist,
        )
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
