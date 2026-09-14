# SPDX-License-Identifier: GPL-3.0-or-later
"""Run catalog batch export on a Blender scene."""

from __future__ import annotations

import os
from typing import Any, Callable, Never

import bpy
from bpy.types import Context, Object
from mathutils import Vector

from ..studio import cameras as camera_lib
from ..ui.messages import NO_CAMERA
from . import batch as batch_lib
from . import shots as shots_lib
from . import shots_apply
from .exposure_apply import apply_exposure
from .looks_apply import apply_look

ReportFn = Callable[[str, str], None]


def _settings(context: Context):
    return context.scene.behold


def _ensure_camera(context: Context) -> Object | None:
    cam = camera_lib.resolve_shoot_camera(context)
    if cam is not None:
        context.scene.camera = cam
    return cam


def _product_center_extent(targets: list[Object]) -> tuple[Vector, float]:
    corners = [
        obj.matrix_world @ Vector(corner)
        for obj in targets
        for corner in obj.bound_box
    ]
    center = sum(corners, Vector()) / len(corners)
    mins = (
        min(c.x for c in corners),
        min(c.y for c in corners),
        min(c.z for c in corners),
    )
    maxs = (
        max(c.x for c in corners),
        max(c.y for c in corners),
        max(c.z for c in corners),
    )
    return center, batch_lib.product_extent(mins, maxs)


def _render_helpers():
    """Load still helpers after operators has finished loading.

    operators.execute imports this module; a module-level import of
    operators would cycle (operators → batch_apply → operators).
    """
    from .operators import apply_render_quality, resolve_output_dir

    return apply_render_quality, resolve_output_dir


def _render_still(context: Context, job: batch_lib.BatchJob) -> dict[str, Any]:
    apply_quality, resolve_dir = _render_helpers()
    apply_exposure(context)
    apply_look(context)
    result = apply_quality(context)
    if not result.get("ok"):
        return {
            "ok": False,
            "message": str(result.get("message") or batch_lib.BATCH_RENDER_FAILED),
        }
    scene = context.scene
    scene.render.image_settings.file_format = "PNG"
    out_dir = resolve_dir(context, angle=job.slug)
    scene.render.filepath = os.path.join(out_dir, job.filename)
    bpy.ops.render.render(write_still=True)
    return {"ok": True, "out_dir": out_dir}


def _place_angle_camera(
    cam: Object, center: Vector, extent: float, slug: str
) -> None:
    offset = Vector(batch_lib.angle_world_offset(slug, extent))
    cam.location = center + offset
    direction = center - cam.location
    if direction.length > 1e-6:
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def _run_job(
    context: Context,
    job: batch_lib.BatchJob,
    *,
    center: Vector,
    extent: float,
) -> dict[str, Any]:
    if job.kind == "angle":
        cam = _ensure_camera(context)
        if cam is None:
            return {"ok": False, "message": NO_CAMERA}
        _place_angle_camera(cam, center, extent, job.slug)
        return _render_still(context, job)
    if job.kind == "shot":
        applied = shots_apply.apply_shot_to_scene(
            context, shot_name=job.shot_name
        )
        if not applied["ok"]:
            return {
                "ok": False,
                "message": str(applied.get("message") or batch_lib.BATCH_RENDER_FAILED),
            }
        warning = str(applied.get("warning") or "")
        if warning:
            return {"ok": False, "message": warning}
        if _ensure_camera(context) is None:
            return {"ok": False, "message": NO_CAMERA}
        return _render_still(context, job)
    unreachable: Never = job.kind
    raise RuntimeError(f"unhandled batch job kind: {unreachable}")


def _progress_begin(context: Context, total: int) -> Any | None:
    wm = getattr(context, "window_manager", None)
    if wm is None or not hasattr(wm, "progress_begin"):
        return None
    try:
        wm.progress_begin(0, max(total, 1))
    except Exception:
        return None
    return wm


def _progress_update(wm: Any, index: int) -> None:
    if wm is None or not hasattr(wm, "progress_update"):
        return
    try:
        wm.progress_update(index)
    except Exception:
        return


def _progress_end(wm: Any) -> None:
    if wm is None or not hasattr(wm, "progress_end"):
        return
    try:
        wm.progress_end()
    except Exception:
        return


def run_batch_export(
    context: Context,
    *,
    report: ReportFn | None = None,
) -> dict[str, Any]:
    """Render planned stills. Restores camera pose and scene look afterwards."""
    settings = _settings(context)
    targets = camera_lib.product_targets(context)
    cam = camera_lib.resolve_shoot_camera(context)
    shot_names = [item.name for item in settings.shots]
    plan, error = batch_lib.plan_batch(
        include_angles=bool(getattr(settings, "batch_include_angles", True)),
        include_shots=bool(getattr(settings, "batch_include_shots", False)),
        shot_names=shot_names,
        has_product=bool(targets),
        has_camera=cam is not None,
    )
    if error or plan is None:
        return {"ok": False, "message": error or batch_lib.BATCH_NOTHING, "errors": ()}

    restore_payload = shots_lib.snapshot_from_mapping(
        settings,
        camera_name=cam.name if cam is not None else "",
    )
    original_cam_name = cam.name if cam is not None else ""
    original_matrix = cam.matrix_world.copy() if cam is not None else None
    center = Vector((0.0, 0.0, 0.0))
    extent = batch_lib.MIN_EXTENT
    if targets:
        center, extent = _product_center_extent(targets)

    last_dir = ""
    ok_count = 0
    errors: list[str] = []
    total = plan.total
    wm = _progress_begin(context, total)
    try:
        for index, job in enumerate(plan.jobs, start=1):
            _progress_update(wm, index)
            if report is not None:
                report("INFO", batch_lib.progress_message(index, total, job))
            try:
                result = _run_job(
                    context,
                    job,
                    center=center,
                    extent=extent,
                )
            except RuntimeError as exc:
                result = {
                    "ok": False,
                    "message": str(exc).strip() or batch_lib.BATCH_RENDER_FAILED,
                }
            if result.get("ok"):
                ok_count += 1
                last_dir = str(result.get("out_dir") or last_dir)
            else:
                errors.append(
                    str(result.get("message") or batch_lib.BATCH_RENDER_FAILED)
                )
    finally:
        _progress_end(wm)
        shots_apply.apply_payload_to_scene(context, restore_payload)
        if original_matrix is not None and original_cam_name:
            obj = bpy.data.objects.get(original_cam_name)
            if obj is not None and obj.type == "CAMERA":
                obj.matrix_world = original_matrix
                context.scene.camera = obj

    message = batch_lib.done_message(
        ok_count, total, last_dir=last_dir, errors=errors
    )
    if ok_count == 0:
        return {
            "ok": False,
            "message": errors[0] if errors else message,
            "errors": tuple(errors),
            "rendered": ok_count,
            "total": total,
        }
    return {
        "ok": True,
        "message": message,
        "errors": tuple(errors),
        "rendered": ok_count,
        "total": total,
        "out_dir": last_dir,
    }
