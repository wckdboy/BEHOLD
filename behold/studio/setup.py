# SPDX-License-Identifier: GPL-3.0-or-later
"""Studio construction helpers for Build Studio."""

from __future__ import annotations

import bpy
from bpy.types import Context, Object
from mathutils import Vector

from . import lights as light_lib
from .tones import backdrop_tone_rgba, kelvin_to_rgb

PREFIX = light_lib.PREFIX


def selected_meshes(context: Context) -> list[Object]:
    return light_lib.selected_meshes(context)


def bounds_world(objects) -> tuple[Vector, Vector]:
    return light_lib.bounds_world(objects)


def ensure_collection(context: Context) -> bpy.types.Collection:
    return light_lib.ensure_collection(context)


def clear_studio(coll: bpy.types.Collection) -> None:
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def link_exclusive(obj: Object, coll: bpy.types.Collection) -> None:
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    if obj.name not in coll.objects:
        coll.objects.link(obj)


def make_cyclorama(
    coll: bpy.types.Collection,
    center: Vector,
    radius: float,
    color: tuple[float, float, float, float] = (0.85, 0.85, 0.87, 1.0),
) -> Object:
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
        bsdf.inputs["Base Color"].default_value = color
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


def _activate_key_light(context: Context) -> None:
    key = bpy.data.objects.get(f"{PREFIX}_Key")
    if key is not None and key.type == "LIGHT":
        light_lib.set_active_behold_light(context, key)
        return
    light_lib.sync_active_light_name(context)


def build_studio(context: Context) -> str:
    settings = context.scene.behold
    targets = selected_meshes(context)
    if not targets:
        return "Select at least one mesh object"

    mins, maxs = bounds_world(targets)
    floor_center = Vector(((mins.x + maxs.x) * 0.5, (mins.y + maxs.y) * 0.5, mins.z))
    extents = maxs - mins
    size = max(extents.x, extents.y, extents.z, 0.1)
    product_center = Vector((floor_center.x, floor_center.y, mins.z + extents.z * 0.5))

    coll = ensure_collection(context)
    clear_studio(coll)

    color = kelvin_to_rgb(settings.light_temperature)
    key_energy = 250.0 * size * settings.key_power
    tone = backdrop_tone_rgba(settings)

    if settings.studio_backdrop == "CYCLORAMA":
        make_cyclorama(coll, floor_center, size, color=tone)
        setup_world(context.scene)
    elif settings.studio_backdrop == "SOLID":
        setup_world(context.scene, color=tone, strength=0.35)
    else:
        setup_world(context.scene, color=(0.01, 0.01, 0.01, 1.0), strength=0.05)

    if settings.include_shadow_catcher and settings.studio_backdrop != "CYCLORAMA":
        make_shadow_catcher(coll, floor_center, size * 4.0)

    key_loc = product_center + Vector((-size * 1.4, -size * 1.6, size * 1.8))
    fill_loc = product_center + Vector((size * 1.6, -size * 1.1, size * 1.0))
    rim_loc = product_center + Vector((size * 0.2, size * 1.8, size * 1.4))

    if settings.studio_light_rig == "SOFTBOX":
        light_lib.make_area_light(
            f"{PREFIX}_Key", coll, key_loc, product_center, size * 1.8, key_energy, color
        )
        light_lib.make_area_light(
            f"{PREFIX}_Fill",
            coll,
            fill_loc,
            product_center,
            size * 1.4,
            key_energy * settings.fill_ratio,
            color,
        )
    else:
        light_lib.make_area_light(
            f"{PREFIX}_Key", coll, key_loc, product_center, size * 1.1, key_energy, color
        )
        light_lib.make_area_light(
            f"{PREFIX}_Fill",
            coll,
            fill_loc,
            product_center,
            size * 0.9,
            key_energy * settings.fill_ratio,
            color,
        )
        light_lib.make_area_light(
            f"{PREFIX}_Rim",
            coll,
            rim_loc,
            product_center,
            size * 0.7,
            key_energy * settings.rim_ratio,
            color,
        )

    cam = frame_camera(coll, product_center, size)
    context.scene.camera = cam
    context.scene.behold.main_camera_name = cam.name
    _activate_key_light(context)

    context.scene.render.engine = "CYCLES"
    context.scene.cycles.samples = 128
    context.scene.cycles.use_denoising = True
    try:
        context.scene.view_settings.view_transform = "AgX"
    except TypeError:
        pass

    return f"Studio built for {len(targets)} object(s)"


def refresh_light_mixer(context: Context) -> int:
    settings = context.scene.behold
    color = kelvin_to_rgb(settings.light_temperature)
    targets = selected_meshes(context)
    size = 1.0
    if targets:
        mins, maxs = bounds_world(targets)
        size = max(maxs.x - mins.x, maxs.y - mins.y, maxs.z - mins.z, 0.1)
    key_energy = 250.0 * size * settings.key_power
    mapping = {
        f"{PREFIX}_Key": key_energy,
        f"{PREFIX}_Fill": key_energy * settings.fill_ratio,
        f"{PREFIX}_Rim": key_energy * settings.rim_ratio,
    }
    updated = 0
    for name, energy in mapping.items():
        obj = bpy.data.objects.get(name)
        if obj is not None and obj.type == "LIGHT":
            obj.data.energy = energy
            obj.data.color = color
            updated += 1
    updated += light_lib.apply_temperature_to_extras(context)
    return updated
