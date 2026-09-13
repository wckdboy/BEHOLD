# SPDX-License-Identifier: GPL-3.0-or-later
"""One-click product studio setup."""

from __future__ import annotations

import math
from typing import Iterable

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Object, Operator
from mathutils import Vector

from . import lights as light_lib


COLLECTION_NAME = light_lib.COLLECTION_NAME
PREFIX = light_lib.PREFIX


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


def ensure_collection(context: Context) -> bpy.types.Collection:
    scene = context.scene
    coll = bpy.data.collections.get(COLLECTION_NAME)
    if coll is None:
        coll = bpy.data.collections.new(COLLECTION_NAME)
    if coll.name not in scene.collection.children:
        scene.collection.children.link(coll)
    return coll


def clear_studio(coll: bpy.types.Collection) -> None:
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def link_exclusive(obj: Object, coll: bpy.types.Collection) -> None:
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    if obj.name not in coll.objects:
        coll.objects.link(obj)


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
    data.energy = power
    data.color = color
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    direction = target - location
    if direction.length > 1e-6:
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    coll.objects.link(obj)
    return obj


def make_cyclorama(coll: bpy.types.Collection, center: Vector, radius: float) -> Object:
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(center.x, center.y, center.z))
    floor = bpy.context.active_object
    assert floor is not None
    floor.name = f"{PREFIX}_Cyclorama"
    floor.scale = (radius * 2.5, radius * 2.5, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0.0, -radius * 0.05, radius * 1.8)}
    )
    bpy.ops.object.mode_set(mode="OBJECT")

    bevel = floor.modifiers.new(name="Bevel", type="BEVEL")
    bevel.width = radius * 0.35
    bevel.segments = 6

    mat = bpy.data.materials.get(f"{PREFIX}_Sweep") or bpy.data.materials.new(
        name=f"{PREFIX}_Sweep"
    )
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.85, 0.85, 0.87, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.55
    floor.data.materials.clear()
    floor.data.materials.append(mat)
    link_exclusive(floor, coll)
    return floor


def make_shadow_catcher(coll: bpy.types.Collection, center: Vector, size: float) -> Object:
    bpy.ops.mesh.primitive_plane_add(size=size, location=(center.x, center.y, center.z))
    plane = bpy.context.active_object
    assert plane is not None
    plane.name = f"{PREFIX}_ShadowCatcher"
    plane.is_shadow_catcher = True
    link_exclusive(plane, coll)
    return plane


def frame_camera(coll: bpy.types.Collection, center: Vector, size: float) -> Object:
    cam_data = bpy.data.cameras.new(f"{PREFIX}_Camera")
    cam_data.lens = 85.0
    cam = bpy.data.objects.new(f"{PREFIX}_Camera", cam_data)
    cam.location = center + Vector((size * 1.6, -size * 2.2, size * 0.85))
    direction = center - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    coll.objects.link(cam)
    return cam


def setup_world(
    scene: bpy.types.Scene,
    color: tuple[float, float, float, float] = (0.02, 0.02, 0.025, 1.0),
    strength: float = 0.2,
) -> None:
    world = scene.world or bpy.data.worlds.new(f"{PREFIX}_World")
    scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    nodes.clear()
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = color
    bg.inputs["Strength"].default_value = strength
    out = nodes.new("ShaderNodeOutputWorld")
    links.new(bg.outputs["Background"], out.inputs["Surface"])
