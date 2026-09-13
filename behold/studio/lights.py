# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD light inventory, creation, and active-light helpers."""

from __future__ import annotations

import math
import re
from typing import Iterable, Optional

import bpy
from bpy.types import Context, Object
from mathutils import Vector

PREFIX = "BEHOLD"
COLLECTION_NAME = "BEHOLD_Studio"
_EXTRA_RE = re.compile(rf"^{re.escape(PREFIX)}_Light_(\d+)$")
_DRAW_RE = re.compile(rf"^{re.escape(PREFIX)}_Draw_(\d+)$")


def is_behold_light(obj: Object) -> bool:
    return obj.type == "LIGHT" and obj.name.startswith(f"{PREFIX}_")


def iter_behold_lights(context: Optional[Context] = None) -> list[Object]:
    scene = context.scene if context is not None else bpy.context.scene
    lights = [obj for obj in scene.objects if is_behold_light(obj)]
    lights.sort(key=lambda obj: obj.name)
    return lights


def display_light_name(obj: Object) -> str:
    prefix = f"{PREFIX}_"
    if obj.name.startswith(prefix):
        return obj.name[len(prefix) :]
    return obj.name


def _next_indexed_name(pattern: re.Pattern[str], template: str) -> str:
    highest = 0
    for obj in bpy.data.objects:
        if obj.type != "LIGHT":
            continue
        match = pattern.match(obj.name)
        if match:
            highest = max(highest, int(match.group(1)))
    return template.format(highest + 1)


def next_extra_light_name() -> str:
    return _next_indexed_name(_EXTRA_RE, f"{PREFIX}_Light_{{:03d}}")


def next_draw_light_name() -> str:
    return _next_indexed_name(_DRAW_RE, f"{PREFIX}_Draw_{{:03d}}")


def get_active_behold_light(context: Context) -> Optional[Object]:
    settings = context.scene.behold
    name = (settings.active_light_name or "").strip()
    if name:
        obj = bpy.data.objects.get(name)
        if obj is not None and is_behold_light(obj):
            return obj

    active = context.active_object
    if active is not None and is_behold_light(active):
        return active

    lights = iter_behold_lights(context)
    return lights[0] if lights else None


def set_active_behold_light(context: Context, light: Object) -> None:
    if not is_behold_light(light):
        return
    context.scene.behold.active_light_name = light.name
    try:
        context.view_layer.objects.active = light
        light.select_set(True)
    except RuntimeError:
        pass


def sync_active_light_name(context: Context) -> None:
    current = get_active_behold_light(context)
    context.scene.behold.active_light_name = current.name if current is not None else ""


def ensure_collection(context: Context) -> bpy.types.Collection:
    scene = context.scene
    coll = bpy.data.collections.get(COLLECTION_NAME)
    if coll is None:
        coll = bpy.data.collections.new(COLLECTION_NAME)
    if coll.name not in {c.name for c in scene.collection.children}:
        scene.collection.children.link(coll)
    return coll


def kelvin_to_rgb(kelvin: float) -> tuple[float, float, float]:
    temp = max(1000.0, min(40000.0, kelvin)) / 100.0
    if temp <= 66.0:
        r = 1.0
        g = max(0.0, min(1.0, 0.3900815787690196 * math.log(temp) - 0.6318414437886275))
    else:
        r = max(0.0, min(1.0, 1.292936186062745 * ((temp - 60.0) ** -0.1332047592)))
        g = max(0.0, min(1.0, 1.129890860895294 * ((temp - 60.0) ** -0.0755148492)))
    if temp >= 66.0:
        b = 1.0
    elif temp <= 19.0:
        b = 0.0
    else:
        b = max(0.0, min(1.0, 0.543206789110196 * math.log(temp - 10.0) - 1.19625408914))
    return (r, g, b)


def make_area_light(
    name: str,
    coll: bpy.types.Collection,
    location: Vector,
    target: Vector,
    size: float,
    power: float,
    color: tuple[float, float, float],
) -> Object:
    data = bpy.data.lights.new(name=name, type="AREA")
    data.shape = "RECTANGLE"
    data.size = max(size, 0.05)
    data.size_y = max(size * 0.75, 0.05)
    data.energy = max(0.01, power)
    data.color = color
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    direction = target - location
    if direction.length > 1e-6:
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    coll.objects.link(obj)
    return obj


def selected_meshes(context: Context) -> list[Object]:
    return [obj for obj in context.selected_objects if obj.type == "MESH"]


def bounds_world(objects: Iterable[Object]) -> tuple[Vector, Vector]:
    mins = Vector((math.inf, math.inf, math.inf))
    maxs = Vector((-math.inf, -math.inf, -math.inf))
    for obj in objects:
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            mins = Vector((min(mins.x, world.x), min(mins.y, world.y), min(mins.z, world.z)))
            maxs = Vector((max(maxs.x, world.x), max(maxs.y, world.y), max(maxs.z, world.z)))
    return mins, maxs


def product_frame(context: Context) -> tuple[Vector, float]:
    targets = selected_meshes(context)
    if not targets:
        targets = [obj for obj in context.scene.objects if obj.type == "MESH"]
    if not targets:
        return Vector((0.0, 0.0, 1.0)), 1.0
    mins, maxs = bounds_world(targets)
    center = (mins + maxs) * 0.5
    size = max(maxs.x - mins.x, maxs.y - mins.y, maxs.z - mins.z, 0.1)
    return center, size


def add_extra_light(context: Context, energy: Optional[float] = None) -> Object:
    settings = context.scene.behold
    coll = ensure_collection(context)
    center, size = product_frame(context)
    color = kelvin_to_rgb(settings.light_temperature)
    power = energy if energy is not None else settings.new_light_energy
    name = next_extra_light_name()
    location = center + Vector((-size * 1.2, -size * 1.5, size * 1.6))
    light = make_area_light(
        name,
        coll,
        location,
        center,
        size * 0.9,
        max(0.01, power),
        color,
    )
    set_active_behold_light(context, light)
    return light


def add_draw_light(context: Context) -> Object:
    settings = context.scene.behold
    coll = ensure_collection(context)
    center, size = product_frame(context)
    color = kelvin_to_rgb(settings.light_temperature)
    name = next_draw_light_name()
    location = center + Vector((0.0, -size * 1.8, size * 1.2))
    light = make_area_light(
        name,
        coll,
        location,
        center,
        max(size * 0.7, 0.5),
        max(0.01, settings.new_light_energy),
        color,
    )
    set_active_behold_light(context, light)
    return light


def remove_behold_light(context: Context, light: Object) -> None:
    settings = context.scene.behold
    was_active = settings.active_light_name == light.name
    bpy.data.objects.remove(light, do_unlink=True)
    if was_active:
        remaining = iter_behold_lights(context)
        if remaining:
            set_active_behold_light(context, remaining[0])
        else:
            settings.active_light_name = ""


def apply_temperature_to_extras(context: Context) -> int:
    """Apply shared temperature to non key/fill/rim BEHOLD lights."""
    settings = context.scene.behold
    color = kelvin_to_rgb(settings.light_temperature)
    reserved = {f"{PREFIX}_Key", f"{PREFIX}_Fill", f"{PREFIX}_Rim"}
    count = 0
    for light in iter_behold_lights(context):
        if light.name in reserved:
            continue
        light.data.color = color
        count += 1
    return count
