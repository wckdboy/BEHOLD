# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared mesh / collection helpers used by studio, lighting, and product."""

from __future__ import annotations

import math
from typing import Iterable, Optional

import bpy
from bpy.types import Context, Object
from mathutils import Vector

from .camera_ids import is_studio_mesh_name
from .ids import is_behold_product
from .light_ids import COLLECTION_NAME, PREFIX, is_behold_light_name
from .utility_ids import is_utility_mesh_name


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


def ensure_collection(context: Context, name: str = COLLECTION_NAME) -> bpy.types.Collection:
    scene = context.scene
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    if coll.name not in {child.name for child in scene.collection.children}:
        scene.collection.children.link(coll)
    return coll


def iter_behold_lights(context: Optional[Context] = None) -> list[Object]:
    scene = context.scene if context is not None else bpy.context.scene
    lights = [
        obj
        for obj in scene.objects
        if obj.type == "LIGHT" and is_behold_light_name(obj.name)
    ]
    lights.sort(key=lambda obj: obj.name)
    return lights


def product_meshes(context: Context) -> list[Object]:
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
        if obj.type == "MESH"
        and not is_studio_mesh_name(obj.name)
        and not is_utility_mesh_name(obj.name)
    ]


def product_frame(context: Context) -> tuple[Vector, float]:
    targets = selected_meshes(context) or product_meshes(context)
    if not targets:
        return Vector((0.0, 0.0, 1.0)), 1.0
    mins, maxs = bounds_world(targets)
    center = (mins + maxs) * 0.5
    size = max(maxs.x - mins.x, maxs.y - mins.y, maxs.z - mins.z, 0.1)
    return center, size
