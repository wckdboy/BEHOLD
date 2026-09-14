# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD light inventory, creation, and active-light helpers."""

from __future__ import annotations

import math
from typing import Iterable, Optional

import bpy
from bpy.types import Context, Object
from mathutils import Vector

from . import light_ids
from .tones import kelvin_to_rgb

PREFIX = light_ids.PREFIX
COLLECTION_NAME = light_ids.COLLECTION_NAME
RESERVED_RIG = light_ids.RESERVED_RIG


def is_behold_light(obj: Object) -> bool:
    return obj.type == "LIGHT" and light_ids.is_behold_light_name(obj.name)


def iter_behold_lights(context: Optional[Context] = None) -> list[Object]:
    scene = context.scene if context is not None else bpy.context.scene
    lights = [obj for obj in scene.objects if is_behold_light(obj)]
    lights.sort(key=lambda obj: obj.name)
    return lights


def display_light_name(obj: Object) -> str:
    return light_ids.display_light_name(obj.name)


def _existing_light_names() -> list[str]:
    return [obj.name for obj in bpy.data.objects if obj.type == "LIGHT"]


def next_extra_light_name() -> str:
    return light_ids.next_indexed_name(_existing_light_names(), "Light")


def next_draw_light_name() -> str:
    return light_ids.next_indexed_name(_existing_light_names(), "Draw")


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
    if coll.name not in {child.name for child in scene.collection.children}:
        scene.collection.children.link(coll)
    return coll


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
    settings = context.scene.behold
    color = kelvin_to_rgb(settings.light_temperature)
    count = 0
    for light in iter_behold_lights(context):
        if light.name in RESERVED_RIG:
            continue
        light.data.color = color
        count += 1
    return count
