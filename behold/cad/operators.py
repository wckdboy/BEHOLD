# SPDX-License-Identifier: GPL-3.0-or-later
"""CAD operators: hybrid STEP import + Material Assist handoff."""

from __future__ import annotations

import os

import bpy
from bpy.props import FloatProperty, StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ImportHelper

from . import detect
from . import material_assist
from . import ocp_import


class BEHOLD_OT_import_step(Operator, ImportHelper):
    bl_idname = "behold.import_step"
    bl_label = "Import STEP / IGES"
    bl_description = (
        "Hybrid CAD import: STEPper NEXT if installed, otherwise BEHOLD OCP"
    )
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".step"
    filter_glob: StringProperty(
        default="*.step;*.stp;*.iges;*.igs;*.brep;*.brp",
        options={"HIDDEN"},
    )
    deflection: FloatProperty(
        name="Deflection",
        description=(
            "OCP tessellation linear deflection (meters-ish); "
            "ignored when STEPper handles import"
        ),
        default=0.001,
        min=0.00001,
        soft_max=0.05,
    )

    def execute(self, context: Context):
        filepath = self.filepath
        if not filepath:
            self.report({"ERROR"}, "No file selected")
            return {"CANCELLED"}

        status = detect.cad_status()
        before = {obj.as_pointer() for obj in bpy.data.objects}

        if status["backend"] == "STEPPER":
            ok = _invoke_stepper_import(filepath, status.get("stepper_operator"))
            if not ok:
                self.report(
                    {"ERROR"},
                    "STEPper NEXT is present but its import operator failed — "
                    "try File → Import in STEPper, or install OCP for BEHOLD's fallback",
                )
                return {"CANCELLED"}
            imported = [
                obj
                for obj in bpy.data.objects
                if obj.as_pointer() not in before and obj.type == "MESH"
            ]
            for obj in imported:
                obj["BEHOLD_cad_source"] = filepath
                obj["BEHOLD_cad_backend"] = "STEPPER"
            if imported:
                bpy.ops.object.select_all(action="DESELECT")
                for obj in imported:
                    obj.select_set(True)
                context.view_layer.objects.active = imported[0]
            material_assist.tag_selection_for_assist(context)
            self.report(
                {"INFO"},
                f"STEPper import finished ({len(imported)} new mesh(es)) — "
                "Material Assist ready",
            )
            return {"FINISHED"}

        if status["backend"] == "OCP":
            result = ocp_import.import_step_with_ocp(
                filepath,
                deflection=self.deflection,
            )
            if not result["ok"]:
                self.report({"ERROR"}, result["message"])
                return {"CANCELLED"}
            material_assist.tag_selection_for_assist(context)
            self.report({"INFO"}, result["message"] + " — Material Assist ready")
            return {"FINISHED"}

        self.report({"ERROR"}, status["detail"])
        return {"CANCELLED"}


def _invoke_stepper_import(filepath: str, preferred_op: str | None) -> bool:
    """Call STEPper's import operator with a filepath when possible."""
    candidates: list[str] = []
    if preferred_op:
        candidates.append(preferred_op)
    candidates.extend(detect.STEPPER_IMPORT_OPS)

    abs_path = bpy.path.abspath(filepath)
    directory = os.path.dirname(abs_path)
    basename = os.path.basename(abs_path)

    for op_id in candidates:
        try:
            path, name = op_id.split(".", 1)
            op = getattr(getattr(bpy.ops, path), name)
        except AttributeError:
            continue

        attempts = (
            {"filepath": abs_path},
            {"filepath": abs_path, "override_file": basename},
            {
                "filepath": abs_path,
                "directory": directory,
                "files": [{"name": basename}],
            },
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
        try:
            result = op("INVOKE_DEFAULT")
            if "FINISHED" in result or "RUNNING_MODAL" in result:
                return True
        except Exception:  # noqa: BLE001
            continue
    return False


class BEHOLD_OT_cad_material_assist(Operator):
    bl_idname = "behold.cad_material_assist"
    bl_label = "Material Assist"
    bl_description = (
        "Suggest BlenderKit queries from imported CAD part names/colors and open search"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not meshes:
            self.report({"ERROR"}, "Select imported CAD mesh(es) first")
            return {"CANCELLED"}

        query = material_assist.suggest_query_for_objects(meshes)
        context.scene.behold.blenderkit_query = query
        material_assist.tag_selection_for_assist(context)

        try:
            bpy.ops.behold.blenderkit_search()
        except Exception:  # noqa: BLE001
            self.report(
                {"INFO"},
                f"Suggested “{query}” — enable BlenderKit or use Materials → Search",
            )
            return {"FINISHED"}

        self.report({"INFO"}, f"Material Assist → BlenderKit “{query}”")
        return {"FINISHED"}


class BEHOLD_OT_cad_build_studio(Operator):
    bl_idname = "behold.cad_build_studio"
    bl_label = "Studio from Import"
    bl_description = "Keep CAD selection and run Build Studio"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not meshes:
            meshes = [
                obj
                for obj in context.scene.objects
                if obj.type == "MESH" and obj.get("BEHOLD_cad_source")
            ]
            bpy.ops.object.select_all(action="DESELECT")
            for obj in meshes:
                obj.select_set(True)
            if meshes:
                context.view_layer.objects.active = meshes[0]

        if not meshes:
            self.report({"ERROR"}, "Select CAD mesh(es) or import a STEP first")
            return {"CANCELLED"}

        try:
            result = bpy.ops.behold.build_studio()
        except Exception as exc:  # noqa: BLE001
            self.report({"ERROR"}, f"Build Studio failed: {exc}")
            return {"CANCELLED"}

        if "FINISHED" not in result:
            self.report({"WARNING"}, "Build Studio did not finish")
            return {"CANCELLED"}

        self.report({"INFO"}, "Studio built around CAD import")
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_import_step,
    BEHOLD_OT_cad_material_assist,
    BEHOLD_OT_cad_build_studio,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
