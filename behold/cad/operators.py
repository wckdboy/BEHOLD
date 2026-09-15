# SPDX-License-Identifier: GPL-3.0-or-later
"""CAD operators: hybrid STEP import + Material Assist handoff."""

from __future__ import annotations

import os
from typing import Any, Never

import bpy
from bpy.props import FloatProperty, StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ImportHelper

from . import detect
from . import defeaturing as df_spec
from . import material_assist
from . import ocp_core
from . import ocp_defeature
from . import ocp_import
from . import regenerate as regen_spec
from . import regenerate_apply
from . import stepper_api
from ..ui.messages import (
    NO_CAD_SOURCE,
    NO_FILE_SELECTED,
    NO_MESH_SELECTED,
    file_not_found_message,
    report_set,
)


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


def _tag_imported_meshes(
    meshes: list,
    abs_path: str,
    backend: str,
    *,
    deflection: float = regen_spec.DEFAULT_DEFLECTION,
    quality: str = "CUSTOM",
) -> None:
    cache = regen_spec.cache_record(
        abs_path,
        backend,
        quality=quality,
        deflection=deflection,
    )
    regenerate_apply.tag_cad_meshes(meshes, cache)


def _remember_import(
    context: Context,
    abs_path: str,
    backend: str,
    deflection: float,
) -> None:
    cache = regen_spec.cache_record(
        abs_path,
        backend,
        quality="CUSTOM",
        deflection=deflection,
    )
    regenerate_apply.write_scene_cache(context, cache, touch_quality=False)


def invoke_stepper_occ_import(
    filepath: str,
    *,
    lin_deflection_len: float | None = None,
    quality_preset: str | None = stepper_api.DEFAULT_QUALITY_PRESET,
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
    quality = quality_preset
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


def scene_cleanup_plan(context: Context) -> df_spec.DefeaturingPlan:
    settings = context.scene.behold
    return df_spec.plan_defeaturing(
        fillets=bool(settings.cad_cleanup_fillets),
        chamfers=bool(settings.cad_cleanup_chamfers),
        holes=bool(settings.cad_cleanup_holes),
        blend_mm=float(settings.cad_blend_mm),
        hole_mm=float(settings.cad_hole_mm),
    )


def _cleanup_blockers(plan: df_spec.DefeaturingPlan) -> dict[str, Any] | None:
    if not plan.active:
        return None
    probe = ocp_defeature.probe_defeaturing_api()
    blocked = df_spec.cleanup_blockers(
        plan,
        ocp_available=probe["ocp"],
        has_defeaturing=probe["defeaturing"],
        has_remove_wires=probe["remove_wires"],
    )
    if blocked is None:
        return None
    return {
        "ok": False,
        "objects": [],
        "backend": "OCP" if probe["ocp"] else "NONE",
        "message": blocked,
    }


def import_cad_file(
    context: Context,
    filepath: str,
    *,
    deflection: float = 0.001,
) -> dict[str, Any]:
    """Hybrid CAD import: STEPper NEXT first, OCP only if STEPper is missing.

    Cleanup (fillets / chamfers / holes) is OCP-only — STEPper has no RNA
    for it. When cleanup is on, this path uses OCP before tessellate.
    """
    abs_path = bpy.path.abspath(filepath)
    if not abs_path or not os.path.isfile(abs_path):
        return {
            "ok": False,
            "objects": [],
            "backend": "NONE",
            "message": file_not_found_message(filepath),
        }
    cleanup = scene_cleanup_plan(context)
    blocked = _cleanup_blockers(cleanup)
    if blocked is not None:
        return blocked
    if not cleanup.active:
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
    if cleanup.active:
        backend = "OCP"
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
        _tag_imported_meshes(imported, abs_path, "STEPPER", deflection=deflection)
        _remember_import(context, abs_path, "STEPPER", deflection)
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
        result = ocp_import.import_cad_with_ocp(
            filepath,
            deflection=deflection,
            cleanup=cleanup,
        )
        result["backend"] = "OCP"
        if result.get("ok"):
            _tag_imported_meshes(
                list(result.get("objects") or []),
                abs_path,
                "OCP",
                deflection=deflection,
            )
            _remember_import(context, abs_path, "OCP", deflection)
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


def _ensure_stepper_or_error() -> dict[str, Any] | None:
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
    return None


def regenerate_cad_file(
    context: Context,
    *,
    quality: str | None = None,
    deflection: float | None = None,
) -> dict[str, Any]:
    """Retessellate the cached CAD product. Does not open a file picker."""
    settings = context.scene.behold
    cache = regenerate_apply.scene_cache_from_settings(context)
    if cache is None:
        return {
            "ok": False,
            "objects": [],
            "backend": "NONE",
            "message": NO_CAD_SOURCE,
        }

    problem = regen_spec.classify_cad_source(cache.filepath)
    if problem is not None:
        return {
            "ok": False,
            "objects": [],
            "backend": cache.backend or "NONE",
            "message": regen_spec.cad_source_problem_message(problem),
        }

    plan = regen_spec.plan_tessellation(
        quality if quality is not None else settings.cad_quality,
        deflection if deflection is not None else settings.cad_deflection,
    )
    if isinstance(plan, str):
        return {
            "ok": False,
            "objects": [],
            "backend": cache.backend or "NONE",
            "message": plan,
        }

    cleanup = scene_cleanup_plan(context)
    blocked = _cleanup_blockers(cleanup)
    if blocked is not None:
        return blocked

    if not cleanup.active:
        enable_error = _ensure_stepper_or_error()
        if enable_error is not None:
            return enable_error

    status = detect.cad_status()
    backend = regen_spec.pick_regenerate_backend(cache.backend, status["backend"])
    if cleanup.active:
        backend = "OCP"
    if backend == "NONE":
        return {
            "ok": False,
            "objects": [],
            "backend": "NONE",
            "message": stepper_api.missing_cad_backend_message(),
        }
    if backend == "OCP":
        if not ocp_core.ocp_available():
            return {
                "ok": False,
                "objects": [],
                "backend": "NONE",
                "message": stepper_api.missing_cad_backend_message(),
            }
        return regenerate_apply.regenerate_ocp(
            context,
            cache,
            plan,
            cleanup=cleanup,
        )
    if backend == "STEPPER":
        return _regenerate_stepper(context, cache, plan)

    unreachable: Never = backend
    raise RuntimeError(f"unhandled CAD backend: {unreachable}")


def _regenerate_stepper(
    context: Context,
    cache: regen_spec.CadCache,
    plan: regen_spec.TessellationPlan,
) -> dict[str, Any]:
    existing = regenerate_apply.tagged_cad_meshes(context, cache.filepath)
    snaps = regenerate_apply.snapshot_objects(existing)
    snap_by_name = {snap.name: snap for snap in snaps}
    before = {obj.as_pointer() for obj in bpy.data.objects}

    known = None
    try:
        known = _rna_property_ids(_operator_from_id(stepper_api.STEPPER_OCC_IMPORT_OP))
    except AttributeError:
        known = None
    quality, lin_len = regen_spec.stepper_kwargs_plan(plan, known)
    invoked = invoke_stepper_occ_import(
        cache.filepath,
        lin_deflection_len=lin_len,
        quality_preset=quality,
    )
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

    updated = regen_spec.cache_record(
        cache.filepath,
        "STEPPER",
        quality=plan.quality,
        deflection=plan.deflection,
    )
    paired = regen_spec.match_snapshots(
        tuple(snap_by_name),
        tuple(obj.name for obj in imported),
    )
    for obj in imported:
        old_name = paired.get(obj.name)
        snap = snap_by_name.get(old_name or "")
        if snap is not None:
            regenerate_apply.restore_snapshot(obj, snap)

    old_ptrs = {obj.as_pointer() for obj in existing}
    imported_ptrs = {obj.as_pointer() for obj in imported}
    for obj in list(existing):
        if obj.as_pointer() in imported_ptrs:
            continue
        if obj.as_pointer() not in old_ptrs:
            continue
        mesh = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh is not None and getattr(mesh, "users", 1) == 0:
            bpy.data.meshes.remove(mesh)

    regenerate_apply.tag_cad_meshes(imported, updated)
    regenerate_apply.write_scene_cache(context, updated)
    _select_meshes(context, imported)
    return {
        "ok": True,
        "objects": imported,
        "backend": "STEPPER",
        "message": regen_spec.regenerated_message(
            cache.filepath,
            backend="STEPPER",
            quality=plan.quality,
            object_count=len(imported),
        ),
    }


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
            self.report(report_set(NO_FILE_SELECTED), NO_FILE_SELECTED)
            return {"CANCELLED"}

        result = import_cad_file(context, filepath, deflection=self.deflection)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        imported = list(result.get("objects") or [])
        material_assist.tag_selection_for_assist(context)
        extra = "Material Assist ready"
        settings = context.scene.behold
        if imported and bool(settings.import_auto_material_assist):
            dress = material_assist.run_auto_dress(context, imported)
            extra = dress.get("message") or extra
        self.report({"INFO"}, result["message"] + " — " + extra)
        return {"FINISHED"}


class BEHOLD_OT_regenerate_cad(Operator):
    bl_idname = "behold.regenerate_cad"
    bl_label = "Regenerate"
    bl_description = (
        "Retessellate the last imported CAD product with the Import quality / "
        "deflection and Cleanup toggles. Keeps materials and transforms where possible"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        result = regenerate_cad_file(context)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
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
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


class BEHOLD_OT_cad_auto_dress(Operator):
    bl_idname = "behold.cad_auto_dress"
    bl_label = "Auto-dress"
    bl_description = (
        "Assign a local look per body from STEP color and part names. "
        "Assist still applies one look to the whole selection"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not meshes:
            meshes = scene_product_meshes(context)
            _select_meshes(context, meshes)
        result = material_assist.run_auto_dress(context, meshes)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}
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
            self.report(report_set(NO_MESH_SELECTED), NO_MESH_SELECTED)
            return {"CANCELLED"}

        try:
            result = bpy.ops.behold.build_studio()
        except Exception as exc:  # noqa: BLE001
            self.report({"ERROR"}, f"Build Studio failed: {exc}")
            return {"CANCELLED"}

        if "FINISHED" not in result:
            self.report(report_set(NO_MESH_SELECTED), NO_MESH_SELECTED)
            return {"CANCELLED"}

        self.report({"INFO"}, "Studio built around imported product")
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_open_stepper_install,
    BEHOLD_OT_import_step,
    BEHOLD_OT_regenerate_cad,
    BEHOLD_OT_cad_material_assist,
    BEHOLD_OT_cad_auto_dress,
    BEHOLD_OT_cad_build_studio,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
