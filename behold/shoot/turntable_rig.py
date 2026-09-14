# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD turntable pivot: setup, play helpers, bake, and clear."""

from __future__ import annotations

from typing import Iterator, Optional

import bpy
from bpy.types import Context, FCurve, Object
from mathutils import Matrix, Vector

from ..studio import cameras as camera_lib
from ..studio import lights as light_lib
from . import turntable as turntable_lib

try:
    from bpy_extras import anim_utils
except ImportError:
    anim_utils = None


def scene_fps(scene: bpy.types.Scene) -> float:
    fps = float(getattr(scene.render, "fps", turntable_lib.DEFAULT_FPS) or turntable_lib.DEFAULT_FPS)
    base = float(getattr(scene.render, "fps_base", 1.0) or 1.0)
    return turntable_lib.effective_fps(fps, base)


def get_pivot() -> Optional[Object]:
    obj = bpy.data.objects.get(turntable_lib.PIVOT_NAME)
    if obj is not None and obj.type == "EMPTY":
        return obj
    return None


def has_turntable() -> bool:
    return get_pivot() is not None


def resolve_product_center(context: Context) -> Optional[Vector]:
    targets = camera_lib.product_targets(context)
    if not targets:
        return None
    mins, maxs = light_lib.bounds_world(targets)
    return (mins + maxs) * 0.5


def _channelbag(obj: Object):
    ad = obj.animation_data
    if ad is None or ad.action is None:
        return None
    action = ad.action
    slot = getattr(ad, "action_slot", None)
    slots = getattr(action, "slots", None)
    if slot is None and slots:
        try:
            slot = slots[0]
        except (IndexError, TypeError):
            slot = None

    if (
        anim_utils is not None
        and hasattr(anim_utils, "action_get_channelbag_for_slot")
        and slot is not None
    ):
        try:
            bag = anim_utils.action_get_channelbag_for_slot(action, slot)
        except (TypeError, AttributeError):
            bag = None
        if bag is not None:
            return bag

    layers = getattr(action, "layers", None)
    if not layers:
        return None
    for layer in layers:
        for strip in getattr(layer, "strips", []):
            getter = getattr(strip, "channelbag", None)
            if callable(getter) and slot is not None:
                try:
                    found = getter(slot)
                except TypeError:
                    found = None
                if found is not None:
                    return found
            bags = getattr(strip, "channelbags", None)
            if bags:
                try:
                    return bags[0]
                except (IndexError, TypeError, KeyError):
                    continue
    return None


def iter_fcurves(obj: Object) -> Iterator[FCurve]:
    """Yield fcurves on 4.2 (action.fcurves) and 5.2 (action slots / channelbags)."""
    ad = obj.animation_data
    if ad is None or ad.action is None:
        return
    bag = _channelbag(obj)
    if bag is not None and getattr(bag, "fcurves", None) is not None:
        yield from bag.fcurves
        return
    fcurves = getattr(ad.action, "fcurves", None)
    if fcurves:
        yield from fcurves


def apply_key_interpolation(obj: Object, interpolation: str) -> None:
    handle = "AUTO_CLAMPED" if interpolation == "BEZIER" else "AUTO"
    for fcurve in iter_fcurves(obj):
        for kp in fcurve.keyframe_points:
            kp.interpolation = interpolation
            if interpolation == "BEZIER":
                kp.easing = "EASE_IN_OUT"
                kp.handle_left_type = handle
                kp.handle_right_type = handle
        fcurve.update()


def _unlink_from_pivot(cam: Object, pivot: Object) -> None:
    if cam.parent != pivot:
        return
    mw = cam.matrix_world.copy()
    cam.parent = None
    cam.matrix_world = mw


def _parent_keep_world(cam: Object, pivot: Object) -> None:
    mw = cam.matrix_world.copy()
    cam.parent = pivot
    cam.matrix_world = mw


def _restore_timeline(scene: bpy.types.Scene, holder: Object) -> None:
    if turntable_lib.PROP_FRAME_START in holder:
        scene.frame_start = int(holder[turntable_lib.PROP_FRAME_START])
    if turntable_lib.PROP_FRAME_END in holder:
        scene.frame_end = int(holder[turntable_lib.PROP_FRAME_END])


def _store_timeline(scene: bpy.types.Scene, holder: Object) -> None:
    holder[turntable_lib.PROP_FRAME_START] = int(scene.frame_start)
    holder[turntable_lib.PROP_FRAME_END] = int(scene.frame_end)


def _clear_loc_rot_keys(obj: Object) -> None:
    bag = _channelbag(obj)
    action = obj.animation_data.action if obj.animation_data else None
    for fcurve in list(iter_fcurves(obj)):
        if fcurve.data_path not in {"location", "rotation_euler"}:
            continue
        if bag is not None and hasattr(bag, "fcurves"):
            bag.fcurves.remove(fcurve)
        elif action is not None and hasattr(action, "fcurves"):
            action.fcurves.remove(fcurve)
    if turntable_lib.PROP_BAKED in obj:
        del obj[turntable_lib.PROP_BAKED]


def _delete_pivot(pivot: Object) -> None:
    bpy.data.objects.remove(pivot, do_unlink=True)


def _ensure_pivot(context: Context, center: Vector) -> Object:
    pivot = get_pivot()
    if pivot is None:
        pivot = bpy.data.objects.new(turntable_lib.PIVOT_NAME, None)
        coll = light_lib.ensure_collection(context)
        coll.objects.link(pivot)
    pivot.empty_display_type = "PLAIN_AXES"
    pivot.empty_display_size = 0.25
    pivot.location = center
    pivot.rotation_euler = (0.0, 0.0, 0.0)
    return pivot


def clear_baked_camera(context: Context, cam: Optional[Object] = None) -> bool:
    if cam is None:
        cam = camera_lib.resolve_shoot_camera(context)
    if cam is None or not cam.get(turntable_lib.PROP_BAKED):
        return False
    _restore_timeline(context.scene, cam)
    _clear_loc_rot_keys(cam)
    return True


def clear_turntable(context: Context) -> str:
    """Remove the pivot (or baked camera keys) without touching other animation."""
    scene = context.scene
    pivot = get_pivot()
    if pivot is None:
        cam = camera_lib.resolve_shoot_camera(context)
        if cam is not None and cam.get(turntable_lib.PROP_BAKED):
            clear_baked_camera(context, cam)
            return ""
        return "No turntable to clear"

    cam_name = str(pivot.get(turntable_lib.PROP_CAMERA, "") or "")
    cam = bpy.data.objects.get(cam_name) if cam_name else None
    if cam is None:
        cam = camera_lib.resolve_shoot_camera(context)
    scene.frame_set(int(scene.frame_start))
    if cam is not None:
        _unlink_from_pivot(cam, pivot)
    _restore_timeline(scene, pivot)
    _delete_pivot(pivot)
    return ""


def setup_turntable(context: Context) -> tuple[str, Optional[turntable_lib.TurntablePlan]]:
    settings = context.scene.behold
    cam = camera_lib.resolve_shoot_camera(context)
    if cam is None:
        return turntable_lib.EMPTY_NO_CAMERA, None
    center = resolve_product_center(context)
    if center is None:
        return turntable_lib.EMPTY_NO_PRODUCT, None

    scene = context.scene
    context.scene.camera = cam
    fps = scene_fps(scene)
    plan = turntable_lib.plan_turntable(
        seconds=float(settings.turntable_seconds),
        fps=fps,
        interpolation=settings.turntable_interpolation,
    )
    settings.turntable_frames = plan.frames

    existing = get_pivot()
    if existing is not None:
        old_name = str(existing.get(turntable_lib.PROP_CAMERA, "") or "")
        old = bpy.data.objects.get(old_name) if old_name else None
        if old is not None and old != cam:
            _unlink_from_pivot(old, existing)
        ad = existing.animation_data
        if ad is not None:
            existing.animation_data_clear()

    pivot = _ensure_pivot(context, center)
    if turntable_lib.PROP_FRAME_START not in pivot:
        _store_timeline(scene, pivot)
    pivot[turntable_lib.PROP_CAMERA] = cam.name
    _parent_keep_world(cam, pivot)

    scene.frame_start = plan.frame_start
    scene.frame_end = plan.frame_end
    scene.frame_set(plan.frame_start)

    pivot.rotation_euler = (0.0, 0.0, plan.angle_start)
    pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=plan.key_start)
    pivot.rotation_euler = (0.0, 0.0, plan.angle_end)
    pivot.keyframe_insert(data_path="rotation_euler", index=2, frame=plan.key_end)
    apply_key_interpolation(pivot, plan.interpolation)
    pivot.rotation_euler = (0.0, 0.0, plan.angle_start)
    return "", plan


def bake_turntable(context: Context) -> str:
    """Bake the camera's world loc/rot, then delete the pivot."""
    pivot = get_pivot()
    if pivot is None:
        return "Run Setup Turntable first"

    cam_name = str(pivot.get(turntable_lib.PROP_CAMERA, "") or "")
    cam = bpy.data.objects.get(cam_name) if cam_name else None
    if cam is None:
        cam = camera_lib.resolve_shoot_camera(context)
    if cam is None:
        return turntable_lib.EMPTY_NO_CAMERA

    scene = context.scene
    start = int(scene.frame_start)
    end = int(scene.frame_end)
    current = int(scene.frame_current)
    samples: list[tuple[int, Matrix]] = []
    for frame in range(start, end + 1):
        scene.frame_set(frame)
        context.view_layer.update()
        samples.append((frame, cam.matrix_world.copy()))

    prev_start = int(pivot.get(turntable_lib.PROP_FRAME_START, start))
    prev_end = int(pivot.get(turntable_lib.PROP_FRAME_END, end))
    _unlink_from_pivot(cam, pivot)
    _delete_pivot(pivot)

    for frame, matrix in samples:
        scene.frame_set(frame)
        cam.matrix_world = matrix
        cam.keyframe_insert(data_path="location", frame=frame)
        cam.keyframe_insert(data_path="rotation_euler", frame=frame)
    apply_key_interpolation(cam, "LINEAR")
    cam[turntable_lib.PROP_BAKED] = True
    cam[turntable_lib.PROP_FRAME_START] = prev_start
    cam[turntable_lib.PROP_FRAME_END] = prev_end
    scene.frame_set(current)
    return ""
