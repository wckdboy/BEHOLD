# SPDX-License-Identifier: GPL-3.0-or-later
"""Light Draw helpers (aim math + multi-light target resolution)."""

from __future__ import annotations

from typing import Optional

import bpy
from bpy.types import Context, Event, Object
from bpy_extras import view3d_utils
from mathutils import Vector

from ..studio import lights as light_lib

MODES = ("REFLECT", "DIRECT", "ORBIT")


def ray_cast(context: Context, event: Event) -> tuple[Optional[Vector], Optional[Vector]]:
    region = context.region
    rv3d = context.region_data
    if region is None or rv3d is None:
        return None, None

    coord = (event.mouse_region_x, event.mouse_region_y)
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    depsgraph = context.evaluated_depsgraph_get()
    result, location, normal, _index, _obj, _matrix = context.scene.ray_cast(
        depsgraph, ray_origin, view_vector
    )
    if not result:
        return None, None
    return location.copy(), normal.normalized()


def ensure_draw_light(context: Context) -> Object:
    settings = context.scene.behold
    target = settings.light_draw_target
    if target == "NEW":
        return light_lib.add_draw_light(context)
    if target != "ACTIVE":
        raise ValueError(f"Unknown Light Draw target: {target}")
    light = light_lib.get_active_behold_light(context)
    if light is not None:
        light_lib.set_active_behold_light(context, light)
        return light
    return light_lib.add_draw_light(context)


def aim_light(light: Object, location: Vector, target: Vector) -> None:
    direction = target - location
    if direction.length < 1e-6:
        return
    light.location = location
    light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def reflect_position(hit: Vector, normal: Vector, view_dir: Vector, distance: float) -> Vector:
    to_camera = (-view_dir).normalized()
    reflected = (2.0 * normal.dot(to_camera) * normal - to_camera).normalized()
    return hit + reflected * distance


def direct_position(hit: Vector, normal: Vector, distance: float) -> Vector:
    return hit + normal.normalized() * distance


def set_solo(light: Object, enabled: bool, cache: dict) -> None:
    if enabled:
        if "hide" not in cache:
            cache["hide"] = {}
            for obj in bpy.data.objects:
                if obj.type == "LIGHT" and obj != light:
                    cache["hide"][obj.name] = (obj.hide_viewport, obj.hide_render)
                    obj.hide_viewport = True
                    obj.hide_render = True
    else:
        for name, (hide_v, hide_r) in cache.pop("hide", {}).items():
            obj = bpy.data.objects.get(name)
            if obj is not None:
                obj.hide_viewport = hide_v
                obj.hide_render = hide_r


def adjust_energy(light: Object, factor: float) -> None:
    light.data.energy = max(0.01, light.data.energy * factor)


def adjust_size(light: Object, factor: float) -> None:
    data = light.data
    if hasattr(data, "size"):
        data.size = max(0.05, data.size * factor)
    if hasattr(data, "size_y"):
        data.size_y = max(0.05, data.size_y * factor)
