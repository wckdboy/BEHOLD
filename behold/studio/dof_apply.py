# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply product DoF on the active BEHOLD camera (Blender 5.2 Camera.dof RNA)."""

from __future__ import annotations

from typing import Any, Sequence

from bpy.types import Context, Object

from . import cameras as camera_lib
from . import dof as spec
from . import lights as light_lib
from .camera_ids import is_studio_mesh_name
from ..cad.material_assist import is_behold_product
from ..ui.messages import NO_CAMERA


def probe_api(cam_data: object | None) -> dict[str, bool]:
    dof = getattr(cam_data, "dof", None) if cam_data is not None else None
    return {
        "has_dof": dof is not None,
        "has_use_dof": dof is not None and hasattr(dof, "use_dof"),
        "has_fstop": dof is not None and hasattr(dof, "aperture_fstop"),
        "has_focus_distance": dof is not None and hasattr(dof, "focus_distance"),
        "has_focus_object": dof is not None and hasattr(dof, "focus_object"),
    }


def _result(ok: bool, message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "message": message}
    payload.update(extra)
    return payload


def _world_location(obj: Object) -> tuple[float, float, float]:
    loc = obj.matrix_world.translation
    return (float(loc.x), float(loc.y), float(loc.z))


def _bounds_tuple(
    objects: Sequence[Object],
) -> tuple[tuple[float, float, float], tuple[float, float, float]] | None:
    if not objects:
        return None
    mins, maxs = light_lib.bounds_world(list(objects))
    return (float(mins.x), float(mins.y), float(mins.z)), (
        float(maxs.x),
        float(maxs.y),
        float(maxs.z),
    )


def product_focus_meshes(context: Context) -> list[Object]:
    """Tagged product first, else non-studio meshes — not the live selection."""
    tagged = [
        obj
        for obj in context.scene.objects
        if obj.type == "MESH" and is_behold_product(obj)
    ]
    if tagged:
        return tagged
    return [
        obj
        for obj in context.scene.objects
        if obj.type == "MESH" and not is_studio_mesh_name(obj.name)
    ]


def selected_focus_meshes(context: Context) -> list[Object]:
    return [
        obj
        for obj in context.selected_objects
        if obj.type == "MESH" and not is_studio_mesh_name(obj.name)
    ]


def _write_plan(cam_data: object, plan: spec.DofPlan) -> bool:
    dof = getattr(cam_data, "dof", None)
    if dof is None:
        return False
    try:
        dof.use_dof = plan.use_dof
        dof.aperture_fstop = plan.fstop
        if plan.use_dof:
            dof.focus_distance = plan.focus_distance
            if plan.clear_focus_object and hasattr(dof, "focus_object"):
                dof.focus_object = None
    except (AttributeError, TypeError, ValueError):
        return False
    return True


def apply_dof(
    context: Context,
    *,
    use_dof: bool | None = None,
    fstop: float | None = None,
    focus: str = "KEEP",
) -> dict[str, Any]:
    """Write DoF RNA on the active BEHOLD camera."""
    cam = camera_lib.get_active_behold_camera(context)
    if cam is None:
        cam = camera_lib.resolve_shoot_camera(context)
    if cam is None or getattr(cam, "type", "") != "CAMERA":
        return _result(False, NO_CAMERA)

    data = cam.data
    probe = probe_api(data)
    problem = spec.capability_problem(
        has_dof=probe["has_dof"],
        has_use_dof=probe["has_use_dof"],
        has_fstop=probe["has_fstop"],
        has_focus_distance=probe["has_focus_distance"],
    )
    if problem is not None:
        return _result(False, problem, camera=cam.name)

    settings = getattr(context.scene, "behold", None)
    dof = data.dof
    current_use = bool(getattr(dof, "use_dof", False))
    current_fstop = float(getattr(dof, "aperture_fstop", spec.BLENDER_DEFAULT_FSTOP))
    current_distance = float(
        getattr(dof, "focus_distance", spec.BLENDER_DEFAULT_FOCUS)
    )
    if use_dof is None:
        if settings is not None and hasattr(settings, "dof_enabled"):
            wanted_use = bool(settings.dof_enabled)
        else:
            wanted_use = current_use
    else:
        wanted_use = bool(use_dof)

    focus_id = spec.normalize_focus(focus)
    if focus_id in ("PRODUCT", "SELECTED"):
        wanted_use = True

    requested = fstop
    if requested is None and settings is not None and hasattr(settings, "dof_fstop"):
        requested = float(settings.dof_fstop)

    enabling = wanted_use and not current_use
    plan = spec.plan_dof(
        use_dof=wanted_use,
        fstop=requested,
        current_fstop=current_fstop,
        current_focus_distance=current_distance,
        camera=_world_location(cam),
        product_bounds=_bounds_tuple(product_focus_meshes(context)),
        selected_bounds=_bounds_tuple(selected_focus_meshes(context)),
        focus=focus_id,
        enabling=enabling,
    )
    if isinstance(plan, str):
        return _result(False, plan, camera=cam.name)

    if not _write_plan(data, plan):
        return _result(False, spec.DOF_FAILED, camera=cam.name, plan=plan)

    return _result(True, spec.apply_message(plan), camera=cam.name, plan=plan)


def on_dof_update(settings, context: Context) -> None:
    """RNA update: DoF toggle / f-stop write to the active camera live."""
    del settings
    if context is None or getattr(context, "scene", None) is None:
        return
    apply_dof(context, focus="KEEP")
