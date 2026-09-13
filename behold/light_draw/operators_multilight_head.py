# SPDX-License-Identifier: GPL-3.0-or-later
"""Modal light placement: Reflect, Direct, Orbit."""

from __future__ import annotations

from typing import Optional

import bpy
from bpy.types import Context, Event, Object, Operator, SpaceView3D
from bpy_extras import view3d_utils
from mathutils import Vector

from ..studio import lights as light_lib


PREFIX = "BEHOLD"
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


def studio_lights() -> list[Object]:
    lights = [
        obj
        for obj in bpy.data.objects
        if obj.type == "LIGHT" and obj.name.startswith(PREFIX)
    ]
    return lights or [obj for obj in bpy.data.objects if obj.type == "LIGHT"]


def active_light(context: Context) -> Optional[Object]:
    obj = context.active_object
    if obj is not None and obj.type == "LIGHT":
        return obj
    lights = studio_lights()
    return lights[0] if lights else None


def ensure_draw_light(context: Context) -> Object:
    settings = context.scene.behold
    if settings.light_draw_target == "NEW":
        return light_lib.add_draw_light(context)

    light = light_lib.get_active_behold_light(context)
    if light is not None:
        light_lib.set_active_behold_light(context, light)
        return light

    return light_lib.add_draw_light(context)
