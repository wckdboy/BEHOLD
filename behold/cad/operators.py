# SPDX-License-Identifier: GPL-3.0-or-later
"""CAD operators: hybrid STEP import + Material Assist handoff."""

from __future__ import annotations

from typing import Any, Never

import bpy
from bpy.props import FloatProperty, StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ImportHelper

from . import detect
from . import material_assist
from . import ocp_core
from . import ocp_import
from . import stepper_api


def _new_meshes_since(before: set[int]) -> list:
    return [
        obj
        for obj in bpy.data.objects
        if obj.as_pointer() not in before and obj.type == "MESH"
    ]


def _select_meshes(context: Context, meshes: list) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    if meshes:
        context.view_layer.objects.active = meshes[0]


def _operator_from_id(op_id: str):
    path, name = op_id.split(".", 1)
    return getattr(getattr(bpy.ops, path), name)


def _rna_property_ids(op) -> frozenset[str] | None:
    try:
        rna = op.get_rna_type()
        return frozenset(prop.identifier for prop in rna.properties)
    except Exception:  # noqa: BLE001
        return None


def _tag_imported_meshes(meshes: list, abs_path: str, backend: str) -> None:
    for obj in meshes:
        obj["BEHOLD_cad_source"] = abs_path
        obj["BEHOLD_cad_backend"] = backend
        obj["BEHOLD_product_source"] = abs_path
        obj["BEHOLD_product_backend"] = backend


def invoke_stepper_occ_import(
    filepath: str,
    *,
    lin_deflection_len: float | None = None,
) -> dict[str, Any]:
    """Call ``import_scene.occ_import_step`` with filepath + override_file.

    Does not INVOKE (no STEPper dialog) and does not use background_import.
    """
    abs_path = bpy.path.abspath(filepath)
    try:
        op = _operator_from_id(stepper_api.STEPPER_OCC_IMPORT_OP)
    except AttributeError:
        return {
            "ok": False,
            "message": stepper_api.stepper_operator_failed_message(
                f"{stepper_api.STEPPER_OCC_IMPORT_OP} is not registered"
            ),
        }

    known_props = _rna_property_ids(op)
    quality = stepper_api.DEFAULT_QUALITY_PRESET
    if known_props is not None and "quality_preset" not in known_props:
        quality = None

    errors: list[str] = []
    for kwargs in stepper_api.stepper_occ_import_attempts(
        abs_path,
        known_props=known_props,
        quality_preset=quality,
        lin_deflection_len=lin_deflection_len,
    ):
        try:
            result = op("EXEC_DEFAULT", **kwargs)
        except TypeError as exc:
            errors.append(f"TypeError ({sorted(kwargs)}): {exc}")
            continue
        except Exception as exc:  # noqa: BLE001
            return {
                "ok": False,
                "message": stepper_api.stepper_operator_failed_message(
                    f"{type(exc).__name__}: {exc}"
                ),
            }
        if "FINISHED" in result or "RUNNING_MODAL" in result:
            return {"ok": True, "message": None}
        errors.append(f"{stepper_api.STEPPER_OCC_IMPORT_OP} returned {set(result)}")

    detail = "; ".join(errors) if errors else "no kwargs pattern succeeded"
    return {
        "ok": False,
        "message": stepper_api.stepper_operator_failed_message(detail),
    }


def import_cad_file(
    context: Context,
    filepath: str,
    *,
    deflection: float = 0.001,
) -> dict[str, Any]:
    """Hybrid CAD import: STEPper NEXT first, OCP only if STEPper is missing."""
    abs_path = bpy.path.abspath(filepath)
    enabled = detect.ensure_stepper_enabled()
    if enabled.get("installed") and not enabled.get("ok"):
        return {
            "ok": False,
            "objects": [],
            "backend": "STEPPER",
            "message": enabled.get("error")
            or stepper_api.stepper_enable_failed_message(
                enabled.get("module") or "stepper_next",
                "enable failed",
            ),
        }

    status = detect.cad_status()
    backend = status["backend"]
    before = {obj.as_pointer() for obj in bpy.data.objects}

    if backend == "STEPPER":
        lin_len = None
        known = None
        try:
            known = _rna_property_ids(
                _operator_from_id(stepper_api.STEPPER_OCC_IMPORT_OP)
            )
        except AttributeError:
            known = None
        if known is not None and "lin_deflection_len" in known:
            lin_len = deflection
        invoked = invoke_stepper_occ_import(abs_path, lin_deflection_len=lin_len)
        if not invoked["ok"]:
            return {
                "ok": False,
                "objects": [],
                "backend": "STEPPER",
                "message": invoked["message"],
            }
        imported = _new_meshes_since(before)
        if not imported:
            return {
                "ok": False,
                "objects": [],
                "backend": "STEPPER",
                "message": stepper_api.stepper_no_mesh_message(),
            }
        _tag_imported_meshes(imported, abs_path, "STEPPER")
        _select_meshes(context, imported)
        return {
            "ok": True,
            "objects": imported,
            "backend": "STEPPER",
            "message": f"STEPper NEXT imported {len(imported)} mesh(es)",
        }

    if backend == "OCP":
        if not ocp_core.ocp_available():
            return {
                "ok": False,
                "objects": [],
                "backend": "NONE",
                "message": stepper_api.missing_cad_backend_message(),
            }
        result = ocp_import.import_cad_with_ocp(filepath, deflection=deflection)
        result["backend"] = "OCP"
        return result

    if backend == "NONE":
        return {
            "ok": False,
            "objects": [],
            "backend": "NONE",
            "message": stepper_api.missing_cad_backend_message(),
        }

    unreachable: Never = backend
    raise RuntimeError(f"unhandled CAD backend: {unreachable}")


def scene_product_meshes(context: Context) -> list:
    return [
        obj
        for obj in context.scene.objects
        if obj.type == "MESH" and material_assist.is_behold_product(obj)
    ]


class BEHOLD_OT_open_stepper_install(Operator):
    bl_idname = "behold.open_stepper_install"
    bl_label = "Install STEPper NEXT"
    bl_description = (
        "Open STEPper NEXT GitHub Releases (Blender 5.1+/5.2 LTS extension zip)"
    )
    bl_options = {"REGISTER"}

    def execute(self, context: Context):
        del context
        bpy.ops.wm.url_open(url=stepper_api.STEPPER_INSTALL_URL)
        return {"FINISHED"}


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
            "passed as STEPper lin_deflection_len only when that RNA prop exists"
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

        result = import_cad_file(context, filepath, deflection=self.deflection)
        if not result["ok"]:
            self.report({"ERROR"}, result["message"])
            return {"CANCELLED"}
        material_assist.tag_selection_for_assist(context)
        self.report({"INFO"}, result["message"] + " — Material Assist ready")
        return {"FINISHED"}


class BEHOLD_OT_cad_material_assist(Operator):
    bl_idname = "behold.cad_material_assist"
    bl_label = "Material Assist"
    bl_description = (
        "Apply a local product look from the filename / STEP hint. "
        "Searches BlenderKit only when signed in — no account needed for the local path"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        result = material_assist.run_material_assist(context, meshes)
        if not result["ok"]:
            self.report({"ERROR"}, result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


class BEHOLD_OT_cad_build_studio(Operator):
    bl_idname = "behold.cad_build_studio"
    bl_label = "Studio from Import"
    bl_description = "Keep the imported product selection and run Build Studio"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not meshes:
            meshes = scene_product_meshes(context)
            _select_meshes(context, meshes)

        if not meshes:
            self.report({"ERROR"}, "Select a product mesh or import a file first")
            return {"CANCELLED"}

        try:
            result = bpy.ops.behold.build_studio()
        except Exception as exc:  # noqa: BLE001
            self.report({"ERROR"}, f"Build Studio failed: {exc}")
            return {"CANCELLED"}

        if "FINISHED" not in result:
            self.report({"WARNING"}, "Build Studio did not finish")
            return {"CANCELLED"}

        self.report({"INFO"}, "Studio built around imported product")
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_open_stepper_install,
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
