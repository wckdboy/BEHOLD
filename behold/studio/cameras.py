# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD camera inventory, creation, and product framing."""

from __future__ import annotations

from typing import Optional

import bpy
from bpy.types import Camera, Context, Object
from mathutils import Vector

from . import camera_ids
from . import lights as light_lib


def is_behold_camera(obj: Object) -> bool:
    return obj.type == "CAMERA" and camera_ids.is_behold_camera_name(obj.name)


def iter_behold_cameras(context: Optional[Context] = None) -> list[Object]:
    scene = context.scene if context is not None else bpy.context.scene
    cameras = [obj for obj in scene.objects if is_behold_camera(obj)]
    cameras.sort(key=lambda obj: obj.name)
    return cameras


def display_camera_name(obj: Object) -> str:
    return camera_ids.display_camera_name(obj.name)


def _existing_camera_names() -> list[str]:
    return [obj.name for obj in bpy.data.objects if obj.type == "CAMERA"]


def product_targets(context: Context) -> list[Object]:
    selected = [
        obj
        for obj in context.selected_objects
        if obj.type == "MESH" and not camera_ids.is_studio_mesh_name(obj.name)
    ]
    if selected:
        return selected

    tagged = [
        obj
        for obj in context.scene.objects
        if obj.type == "MESH"
        and (obj.get("BEHOLD_product_source") or obj.get("BEHOLD_cad_source"))
    ]
    if tagged:
        return tagged

    return [
        obj
        for obj in context.scene.objects
        if obj.type == "MESH" and not camera_ids.is_studio_mesh_name(obj.name)
    ]


def product_frame(context: Context) -> tuple[Vector, float]:
    targets = product_targets(context)
    if not targets:
        return Vector((0.0, 0.0, 1.0)), 1.0
    mins, maxs = light_lib.bounds_world(targets)
    center, size = camera_ids.bounds_center_size(
        (mins.x, mins.y, mins.z),
        (maxs.x, maxs.y, maxs.z),
    )
    return Vector(center), size


def apply_product_lens(cam_data: Camera, lens_mm: float) -> None:
    cam_data.lens = max(float(lens_mm), 1.0)
    cam_data.sensor_width = camera_ids.DEFAULT_SENSOR_WIDTH_MM
    cam_data.sensor_height = camera_ids.DEFAULT_SENSOR_HEIGHT_MM
    if hasattr(cam_data, "sensor_fit"):
        cam_data.sensor_fit = "HORIZONTAL"
    if hasattr(cam_data, "lens_unit"):
        cam_data.lens_unit = "MILLIMETERS"
    if hasattr(cam_data, "dof"):
        cam_data.dof.use_dof = False


def place_product_camera(cam: Object, center: Vector, size: float) -> None:
    data = cam.data
    lens_mm = float(data.lens) if data is not None else camera_ids.DEFAULT_LENS_MM
    offset = camera_ids.product_camera_offset(size, lens_mm=lens_mm)
    cam.location = center + Vector(offset)
    direction = center - cam.location
    if direction.length > 1e-6:
        cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    if data is not None:
        start, end = camera_ids.clip_range(size, direction.length)
        data.clip_start = start
        data.clip_end = end
        data.display_size = max(size * 0.15, 0.2)


def create_product_camera(
    coll: bpy.types.Collection,
    center: Vector,
    size: float,
    *,
    name: str,
    lens_mm: float = camera_ids.DEFAULT_LENS_MM,
) -> Object:
    data = bpy.data.cameras.new(name=name)
    apply_product_lens(data, lens_mm)
    cam = bpy.data.objects.new(name, data)
    place_product_camera(cam, center, size)
    coll.objects.link(cam)
    return cam


def get_active_behold_camera(context: Context) -> Optional[Object]:
    settings = context.scene.behold
    name = (settings.active_camera_name or "").strip()
    if name:
        obj = bpy.data.objects.get(name)
        if obj is not None and is_behold_camera(obj):
            return obj

    bookmarked = (settings.main_camera_name or "").strip()
    if bookmarked:
        obj = bpy.data.objects.get(bookmarked)
        if obj is not None and is_behold_camera(obj):
            return obj

    scene_cam = context.scene.camera
    if scene_cam is not None and is_behold_camera(scene_cam):
        return scene_cam

    cameras = iter_behold_cameras(context)
    return cameras[0] if cameras else None


def _look_through_camera(context: Context, cam: Object) -> None:
    try:
        context.view_layer.objects.active = cam
        cam.select_set(True)
    except RuntimeError:
        pass
    space = getattr(context, "space_data", None)
    if space is not None and getattr(space, "type", "") == "VIEW_3D":
        region = getattr(space, "region_3d", None)
        if region is not None:
            region.view_perspective = "CAMERA"


def set_active_behold_camera(context: Context, cam: Object) -> None:
    if not is_behold_camera(cam):
        return
    settings = context.scene.behold
    settings.active_camera_name = cam.name
    settings.main_camera_name = cam.name
    context.scene.camera = cam
    _look_through_camera(context, cam)


def resolve_shoot_camera(context: Context) -> Optional[Object]:
    """Camera Shoot still / batch / turntable should use."""
    active = get_active_behold_camera(context)
    if active is not None:
        return active

    settings = context.scene.behold
    bookmarked = (settings.main_camera_name or "").strip()
    if bookmarked:
        obj = bpy.data.objects.get(bookmarked)
        if obj is not None and obj.type == "CAMERA":
            return obj

    if context.scene.camera is not None:
        return context.scene.camera

    cameras = iter_behold_cameras(context)
    return cameras[0] if cameras else None


def add_product_camera(context: Context, *, lens_mm: Optional[float] = None) -> Object:
    settings = context.scene.behold
    coll = light_lib.ensure_collection(context)
    center, size = product_frame(context)
    name = camera_ids.next_camera_name(_existing_camera_names())
    lens = lens_mm if lens_mm is not None else settings.new_camera_lens
    cam = create_product_camera(coll, center, size, name=name, lens_mm=lens)
    set_active_behold_camera(context, cam)
    return cam


def frame_behold_camera(context: Context, cam: Object) -> None:
    if not is_behold_camera(cam):
        return
    center, size = product_frame(context)
    place_product_camera(cam, center, size)
    set_active_behold_camera(context, cam)


def remove_behold_camera(context: Context, cam: Object) -> None:
    settings = context.scene.behold
    was_active = settings.active_camera_name == cam.name
    was_main = settings.main_camera_name == cam.name
    was_scene = context.scene.camera == cam
    bpy.data.objects.remove(cam, do_unlink=True)
    remaining = iter_behold_cameras(context)
    if remaining and (was_active or was_main or was_scene):
        set_active_behold_camera(context, remaining[0])
        return
    if was_active:
        settings.active_camera_name = ""
    if was_main:
        settings.main_camera_name = ""
    if was_scene:
        context.scene.camera = None


def clear_behold_cameras(context: Context) -> int:
    settings = context.scene.behold
    cameras = list(iter_behold_cameras(context))
    removed_names = {cam.name for cam in cameras}
    scene_cam = context.scene.camera
    scene_cam_name = scene_cam.name if scene_cam is not None else ""
    for cam in cameras:
        bpy.data.objects.remove(cam, do_unlink=True)
    if settings.active_camera_name in removed_names:
        settings.active_camera_name = ""
    if settings.main_camera_name in removed_names:
        settings.main_camera_name = ""
    if scene_cam_name in removed_names:
        context.scene.camera = None
    return len(cameras)
