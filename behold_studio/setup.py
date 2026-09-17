# SPDX-License-Identifier: GPL-3.0-or-later
"""Studio construction helpers for Build Studio (cyclorama / world / catcher)."""

from __future__ import annotations

import bpy
from bpy.types import Context, Object
from mathutils import Vector

from . import catcher_apply
from .common import camera_ids
from .common import geom as geom_lib
from .common.deps import (
    APPLY_QUALITY_OP,
    APPLY_RESOLUTION_OP,
    SEED_CAMERA_OP,
    SEED_LIGHTS_OP,
    try_operator,
)
from .common.messages import EMPTY_NO_MESH
from .common.tones import backdrop_tone_rgba
from .common.fit import fit_from_aabb
from .world_apply import reapply_hdri_if_loaded, setup_solid_world

PREFIX = geom_lib.PREFIX
BUILD_NEEDS_MESH = EMPTY_NO_MESH


def selected_meshes(context: Context) -> list[Object]:
    return geom_lib.selected_meshes(context)


def bounds_world(objects) -> tuple[Vector, Vector]:
    return geom_lib.bounds_world(objects)


def ensure_collection(context: Context) -> bpy.types.Collection:
    return geom_lib.ensure_collection(context)


def clear_studio_backdrops(coll: bpy.types.Collection) -> None:
    for obj in list(coll.objects):
        if camera_ids.is_studio_mesh_name(obj.name):
            bpy.data.objects.remove(obj, do_unlink=True)


def remove_studio_backdrops() -> None:
    """Drop leftover cyclorama / catcher meshes, including ones outside the kit collection."""
    for obj in list(bpy.data.objects):
        if camera_ids.is_studio_mesh_name(obj.name):
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
    *,
    floor_size: float | None = None,
    wall_height: float | None = None,
    bevel_width: float | None = None,
) -> Object:
    plane_size = radius * 2.5 if floor_size is None else floor_size
    wall = radius * 1.8 if wall_height is None else wall_height
    cove = radius * 0.35 if bevel_width is None else bevel_width
    y_pull = -max(plane_size * 0.02, 0.02)

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(center.x, center.y, center.z))
    floor = bpy.context.active_object
    assert floor is not None
    floor.name = f"{PREFIX}_Cyclorama"
    floor.scale = (plane_size, plane_size, 1.0)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0.0, y_pull, wall)}
    )
    bpy.ops.object.mode_set(mode="OBJECT")

    bevel = floor.modifiers.new(name="Bevel", type="BEVEL")
    bevel.width = max(cove, 0.001)
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


def setup_world(
    scene: bpy.types.Scene,
    color: tuple[float, float, float, float] = (0.02, 0.02, 0.025, 1.0),
    strength: float = 0.2,
) -> None:
    setup_solid_world(scene, color=color, strength=strength)


def build_studio(context: Context) -> str:
    settings = context.scene.behold_studio
    targets = selected_meshes(context)
    if not targets:
        return BUILD_NEEDS_MESH

    mins, maxs = bounds_world(targets)
    floor_center = Vector(((mins.x + maxs.x) * 0.5, (mins.y + maxs.y) * 0.5, mins.z))
    fit = fit_from_aabb(
        (mins.x, mins.y, mins.z),
        (maxs.x, maxs.y, maxs.z),
        margin=settings.studio_margin,
    )

    coll = ensure_collection(context)
    remove_studio_backdrops()
    clear_studio_backdrops(coll)

    tone = backdrop_tone_rgba(settings)

    if settings.studio_backdrop == "CYCLORAMA":
        make_cyclorama(
            coll,
            floor_center,
            fit.radius,
            color=tone,
            floor_size=fit.floor_size,
            wall_height=fit.wall_height,
            bevel_width=fit.bevel_width,
        )
        setup_world(context.scene)
    elif settings.studio_backdrop == "SOLID":
        setup_world(context.scene, color=tone, strength=0.35)
    else:
        setup_world(context.scene, color=(0.01, 0.01, 0.01, 1.0), strength=0.05)

    catcher_apply.apply_ground_contact(
        context,
        coll=coll,
        floor_center=floor_center,
        fit=fit,
    )
    reapply_hdri_if_loaded(context)
    try_operator(SEED_LIGHTS_OP)
    try_operator(SEED_CAMERA_OP)
    try_operator(APPLY_QUALITY_OP)
    try_operator(APPLY_RESOLUTION_OP)
    try:
        context.scene.view_settings.view_transform = "AgX"
    except TypeError:
        pass
    return f"Studio built for {len(targets)} object(s)"
