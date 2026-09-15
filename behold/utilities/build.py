# SPDX-License-Identifier: GPL-3.0-or-later
"""Build Danish wall, balcony mount, and eave section meshes in the current scene."""

from __future__ import annotations

from typing import Optional

import bpy
from bpy.types import Context, Object
from mathutils import Vector

from . import ids
from .eaves import EavePart, EaveSpec, eave_parts, eave_spec_from_bounds, make_eave_spec
from .ids import (
    COLLECTION_NAME,
    CUSTOM_KIND,
    CUSTOM_PROP,
    EAVE_ROOT,
    EAVE_SNAP_EMPTY,
    MOUNT_BRACKET_ROOT,
    MOUNT_LEGS_ROOT,
    PRODUCT_SNAP_EMPTY,
    WALL_FACE_EMPTY,
    WALL_ROOT_NAME,
    is_utility_mesh_name,
    is_wall_name,
)
from .messages import (
    NO_PRODUCT,
    NO_WALL,
    UNKNOWN_EAVE,
    WALL_NEEDS_SIZE,
    eave_built_message,
    mount_built_message,
    wall_built_message,
)
from .mounts import MountPart, MountSpec, make_mount_spec, mount_parts, mount_spec_from_bounds
from .wall import WallSpec, make_wall_spec, wall_boxes
from ..cad.material_assist import is_behold_product
from ..materials.presets import is_dressable_mesh_name
from ..studio.camera_ids import is_studio_mesh_name

_LAYER_COLORS = {
    "exterior": ((0.45, 0.18, 0.12), 0.72, 0.0),
    "insulation": ((0.85, 0.70, 0.22), 0.90, 0.0),
    "interior": ((0.86, 0.84, 0.80), 0.85, 0.0),
    "steel": ((0.38, 0.40, 0.42), 0.35, 0.85),
    "roof": ((0.42, 0.24, 0.18), 0.88, 0.0),
    "gutter": ((0.50, 0.52, 0.54), 0.38, 0.72),
    "deck": ((0.58, 0.50, 0.42), 0.72, 0.0),
    "masonry": ((0.45, 0.18, 0.12), 0.72, 0.0),
}


def _ensure_collection(context: Context) -> bpy.types.Collection:
    scene = context.scene
    coll = bpy.data.collections.get(COLLECTION_NAME)
    if coll is None:
        coll = bpy.data.collections.new(COLLECTION_NAME)
    if COLLECTION_NAME not in scene.collection.children:
        scene.collection.children.link(coll)
    return coll


def _link_exclusive(obj: Object, coll: bpy.types.Collection) -> None:
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    if obj.name not in coll.objects:
        coll.objects.link(obj)


def _ensure_material(name: str, color: tuple[float, float, float], roughness: float, metallic: float):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
    mat.use_nodes = True
    tree = mat.node_tree
    if tree is None:
        return mat
    bsdf = tree.nodes.get("Principled BSDF")
    if bsdf is None:
        for node in tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                bsdf = node
                break
    if bsdf is not None:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        if "Roughness" in bsdf.inputs:
            bsdf.inputs["Roughness"].default_value = roughness
        if "Metallic" in bsdf.inputs:
            bsdf.inputs["Metallic"].default_value = metallic
    return mat


def _box_from_min(name: str, min_xyz: tuple[float, float, float], size_xyz: tuple[float, float, float]) -> Object:
    sx, sy, sz = size_xyz
    x, y, z = min_xyz
    verts = [
        (x, y, z),
        (x + sx, y, z),
        (x + sx, y + sy, z),
        (x, y + sy, z),
        (x, y, z + sz),
        (x + sx, y, z + sz),
        (x + sx, y + sy, z + sz),
        (x, y + sy, z + sz),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (0, 3, 7, 4),
    ]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    return obj


def _box_centered(
    name: str,
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    rotation_euler: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> Object:
    sx, sy, sz = size
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    verts = [
        (-hx, -hy, -hz),
        (hx, -hy, -hz),
        (hx, hy, -hz),
        (-hx, hy, -hz),
        (-hx, -hy, hz),
        (hx, -hy, hz),
        (hx, hy, hz),
        (-hx, hy, hz),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (0, 3, 7, 4),
    ]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = center
    obj.rotation_euler = rotation_euler
    return obj


def _tag(obj: Object, kind: str) -> None:
    obj[CUSTOM_PROP] = True
    obj[CUSTOM_KIND] = kind


def _is_utility_object(obj: Object) -> bool:
    if obj.get(CUSTOM_PROP):
        return True
    return is_utility_mesh_name(obj.name)


def _is_wall_object(obj: Object) -> bool:
    kind = obj.get(CUSTOM_KIND)
    if kind and str(kind).startswith("wall"):
        return True
    return is_wall_name(obj.name)


def _remove_root(name: str) -> None:
    root = bpy.data.objects.get(name)
    if root is None:
        return
    children = getattr(root, "children_recursive", None)
    if children is None:
        children = root.children
    for obj in list(children):
        bpy.data.objects.remove(obj, do_unlink=True)
    if root.name in bpy.data.objects:
        bpy.data.objects.remove(root, do_unlink=True)


def _new_empty(name: str, location: tuple[float, float, float], coll: bpy.types.Collection) -> Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.25
    obj.location = location
    _link_exclusive(obj, coll)
    _tag(obj, "empty")
    return obj


def find_wall(context: Context) -> Optional[Object]:
    selected = [obj for obj in context.selected_objects if _is_wall_object(obj)]
    if selected:
        obj = selected[0]
        return obj if obj.parent is None else obj.parent
    root = bpy.data.objects.get(WALL_ROOT_NAME)
    if root is not None:
        return root
    for obj in context.scene.objects:
        if _is_wall_object(obj) and obj.parent is None:
            return obj
    return None


def find_product(context: Context) -> Optional[Object]:
    candidates: list[Object] = []
    for obj in context.selected_objects:
        if obj.type != "MESH":
            continue
        if is_studio_mesh_name(obj.name) or _is_utility_object(obj):
            continue
        if is_dressable_mesh_name(obj.name) or is_behold_product(obj):
            candidates.append(obj)
    if candidates:
        return candidates[0]
    for obj in context.scene.objects:
        if obj.type != "MESH":
            continue
        if is_behold_product(obj) and not _is_utility_object(obj):
            return obj
    return None


def _bounds_world(obj: Object) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    xs = [c.x for c in corners]
    ys = [c.y for c in corners]
    zs = [c.z for c in corners]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def spec_from_settings(settings) -> WallSpec:
    return make_wall_spec(
        settings.storey,
        width_m=settings.wall_width,
        height_m=settings.wall_height,
        foundation_mm=settings.foundation_mm,
        exterior_mm=settings.exterior_mm,
        interior_mm=settings.interior_mm,
        include_door=settings.include_door,
        door_width_m=settings.door_width,
        door_height_m=settings.door_height,
    )


def build_wall(context: Context, spec: WallSpec) -> dict:
    if spec.width_m <= 0.0 or spec.height_m <= 0.0:
        return {"ok": False, "message": WALL_NEEDS_SIZE}
    coll = _ensure_collection(context)
    _remove_root(WALL_ROOT_NAME)
    _remove_root(WALL_FACE_EMPTY)
    root = _new_empty(WALL_ROOT_NAME, (0.0, 0.0, 0.0), coll)
    _tag(root, "wall")
    root["BEHOLD_wall_width"] = spec.width_m
    root["BEHOLD_wall_height"] = spec.height_m
    face = _new_empty(WALL_FACE_EMPTY, (0.0, 0.0, spec.height_m * 0.5), coll)
    face.parent = root
    _tag(face, "wall_face")
    for box in wall_boxes(spec):
        obj = _box_from_min(box.name, box.min_xyz, box.size_xyz)
        color, roughness, metallic = _LAYER_COLORS[box.layer]
        mat = _ensure_material(f"BEHOLD_Util_{box.layer.title()}", color, roughness, metallic)
        obj.data.materials.append(mat)
        obj.parent = root
        _link_exclusive(obj, coll)
        _tag(obj, f"wall_{box.layer}")
    try:
        context.view_layer.objects.active = root
        root.select_set(True)
    except RuntimeError:
        pass
    return {
        "ok": True,
        "message": wall_built_message(spec.storey_label, spec.layers.total_mm),
        "object": root,
    }


def _constrain_to_wall(mount_root: Object, wall: Object) -> None:
    for con in list(mount_root.constraints):
        if con.type == "CHILD_OF":
            mount_root.constraints.remove(con)
    con = mount_root.constraints.new("CHILD_OF")
    con.target = wall
    try:
        con.inverse_matrix = wall.matrix_world.inverted()
    except ValueError:
        pass


def build_mount(context: Context, method: str) -> dict:
    wall = find_wall(context)
    if wall is None:
        return {"ok": False, "message": NO_WALL}
    product = find_product(context)
    if product is None:
        return {"ok": False, "message": NO_PRODUCT}
    settings = context.scene.behold.utilities
    mins, maxs = _bounds_world(product)
    spec: MountSpec = mount_spec_from_bounds(
        method,
        mins,
        maxs,
        leg_height_m=settings.leg_height,
    )
    spec = make_mount_spec(
        spec.method,
        width_m=spec.width_m,
        depth_m=spec.depth_m,
        deck_z=spec.deck_z,
        ground_z=spec.ground_z,
        inset_m=settings.mount_inset,
    )
    coll = _ensure_collection(context)
    root_name = MOUNT_LEGS_ROOT if spec.method == "LEGS" else MOUNT_BRACKET_ROOT
    snap_name = PRODUCT_SNAP_EMPTY if spec.method == "LEGS" else f"{PRODUCT_SNAP_EMPTY}_Bracket"
    _remove_root(root_name)
    _remove_root(snap_name)
    root = _new_empty(root_name, (0.0, 0.0, 0.0), coll)
    _tag(root, f"mount_{spec.method.lower()}")
    snap_name = PRODUCT_SNAP_EMPTY if spec.method == "LEGS" else f"{PRODUCT_SNAP_EMPTY}_Bracket"
    snap = _new_empty(snap_name, (0.0, spec.depth_m * 0.5, spec.deck_z), coll)
    snap.parent = root
    _tag(snap, "snap")
    for part in mount_parts(spec):
        obj = _mesh_from_part(part)
        mat = _ensure_material("BEHOLD_Util_Steel", *_LAYER_COLORS["steel"])
        obj.data.materials.append(mat)
        obj.parent = root
        _link_exclusive(obj, coll)
        _tag(obj, f"mount_{spec.method.lower()}")
    _constrain_to_wall(root, wall)
    try:
        context.view_layer.objects.active = root
        root.select_set(True)
    except RuntimeError:
        pass
    return {
        "ok": True,
        "message": mount_built_message(spec.method_label),
        "object": root,
    }


def _mesh_from_part(part: MountPart) -> Object:
    obj = _box_centered(f"{ids.UTIL_PREFIX}{part.name}", part.center, part.size, part.rotation_euler)
    return obj


def _mesh_from_eave_part(part: EavePart) -> Object:
    return _box_centered(
        f"{ids.UTIL_PREFIX}{part.name}",
        part.center,
        part.size,
        part.rotation_euler,
    )


def _iter_descendants(root: Object) -> list[Object]:
    children = getattr(root, "children_recursive", None)
    if children is None:
        return list(root.children)
    return list(children)


def _mesh_union_bounds(root: Object) -> Optional[tuple[tuple[float, float, float], tuple[float, float, float]]]:
    mins = [float("inf"), float("inf"), float("inf")]
    maxs = [float("-inf"), float("-inf"), float("-inf")]
    found = False
    for obj in [root, *_iter_descendants(root)]:
        if obj.type != "MESH":
            continue
        (x0, y0, z0), (x1, y1, z1) = _bounds_world(obj)
        mins[0], mins[1], mins[2] = min(mins[0], x0), min(mins[1], y0), min(mins[2], z0)
        maxs[0], maxs[1], maxs[2] = max(maxs[0], x1), max(maxs[1], y1), max(maxs[2], z1)
        found = True
    if not found:
        return None
    return (mins[0], mins[1], mins[2]), (maxs[0], maxs[1], maxs[2])


def _wall_extent(wall: Object, settings) -> tuple[float, float]:
    stored_w = wall.get("BEHOLD_wall_width")
    stored_h = wall.get("BEHOLD_wall_height")
    if stored_w is not None and stored_h is not None:
        return max(float(stored_w), 0.5), max(float(stored_h), 0.5)
    bounds = _mesh_union_bounds(wall)
    if bounds is not None:
        (x0, _y0, z0), (x1, _y1, z1) = bounds
        width = max(x1 - x0, 0.5)
        height = max(z1 - min(z0, 0.0), 0.5)
        return width, height
    return float(settings.wall_width), float(settings.wall_height)


def _eave_spec_for_scene(context: Context, section: str, wall: Object) -> EaveSpec:
    settings = context.scene.behold.utilities
    width, height = _wall_extent(wall, settings)
    product = find_product(context)
    if product is not None:
        mins, maxs = _bounds_world(product)
        return eave_spec_from_bounds(
            section,
            mins,
            maxs,
            deck_z=height,
            pitch_deg=settings.eave_pitch,
        )
    return make_eave_spec(
        section,
        width_m=width,
        deck_z=height,
        pitch_deg=settings.eave_pitch,
    )


def build_eave(context: Context, section: str) -> dict:
    wall = find_wall(context)
    if wall is None:
        return {"ok": False, "message": NO_WALL}
    try:
        spec = _eave_spec_for_scene(context, section, wall)
    except ValueError:
        return {"ok": False, "message": UNKNOWN_EAVE}
    coll = _ensure_collection(context)
    _remove_root(EAVE_ROOT)
    _remove_root(EAVE_SNAP_EMPTY)
    root = _new_empty(EAVE_ROOT, (0.0, 0.0, 0.0), coll)
    _tag(root, "eave")
    snap = _new_empty(
        EAVE_SNAP_EMPTY,
        (0.0, spec.projection_m * 0.5, spec.deck_z),
        coll,
    )
    snap.parent = root
    _tag(snap, "snap")
    for part in eave_parts(spec):
        obj = _mesh_from_eave_part(part)
        color, roughness, metallic = _LAYER_COLORS[part.layer]
        mat = _ensure_material(f"BEHOLD_Util_{part.layer.title()}", color, roughness, metallic)
        obj.data.materials.append(mat)
        obj.parent = root
        _link_exclusive(obj, coll)
        _tag(obj, "eave")
    _constrain_to_wall(root, wall)
    try:
        context.view_layer.objects.active = root
        root.select_set(True)
    except RuntimeError:
        pass
    return {
        "ok": True,
        "message": eave_built_message(spec.section_label),
        "object": root,
    }
