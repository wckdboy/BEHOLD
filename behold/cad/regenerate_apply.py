# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply live tessellation regenerate in the current Blender scene."""

from __future__ import annotations

from typing import Any, Sequence

import bpy
from bpy.types import Context, Object
from mathutils import Matrix

from . import ocp_core
from . import ocp_import
from . import regenerate as spec


def _result(ok: bool, message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "message": message}
    payload.update(extra)
    return payload


def tagged_cad_meshes(context: Context, filepath: str = "") -> list[Object]:
    want = (filepath or "").strip()
    found: list[Object] = []
    for obj in context.scene.objects:
        if obj.type != "MESH":
            continue
        source = obj.get(spec.CAD_SOURCE_KEY) or obj.get("BEHOLD_product_source")
        if not isinstance(source, str) or not source.strip():
            continue
        if want and source.strip() != want:
            continue
        found.append(obj)
    return found


def object_source_pairs(context: Context) -> tuple[tuple[str, str], ...]:
    pairs: list[tuple[str, str]] = []
    for obj in context.scene.objects:
        if obj.type != "MESH":
            continue
        source = obj.get(spec.CAD_SOURCE_KEY) or obj.get("BEHOLD_product_source")
        if not isinstance(source, str) or not source.strip():
            continue
        backend = obj.get(spec.CAD_BACKEND_KEY) or obj.get("BEHOLD_product_backend") or ""
        pairs.append((source.strip(), str(backend)))
    return tuple(pairs)


def write_scene_cache(
    context: Context,
    cache: spec.CadCache,
    *,
    touch_quality: bool = True,
) -> None:
    settings = context.scene.behold
    settings.cad_source_filepath = cache.filepath
    settings.cad_source_backend = cache.backend
    settings.cad_deflection = cache.deflection
    if touch_quality and spec.is_quality(cache.quality):
        settings.cad_quality = cache.quality


def scene_cache_from_settings(context: Context) -> spec.CadCache | None:
    settings = context.scene.behold
    return spec.resolve_cad_cache(
        scene_filepath=settings.cad_source_filepath,
        scene_backend=settings.cad_source_backend,
        scene_quality=settings.cad_quality,
        scene_deflection=settings.cad_deflection,
        object_sources=object_source_pairs(context),
    )


def tag_cad_meshes(
    meshes: Sequence[Object],
    cache: spec.CadCache,
) -> None:
    for obj in meshes:
        obj[spec.CAD_SOURCE_KEY] = cache.filepath
        obj[spec.CAD_BACKEND_KEY] = cache.backend
        obj[spec.CAD_QUALITY_KEY] = cache.quality
        obj[spec.CAD_DEFLECTION_KEY] = cache.deflection
        obj["BEHOLD_product_source"] = cache.filepath
        obj["BEHOLD_product_backend"] = cache.backend


def snapshot_objects(objects: Sequence[Object]) -> tuple[spec.ObjectSnapshot, ...]:
    snaps: list[spec.ObjectSnapshot] = []
    for obj in objects:
        matrix = tuple(float(v) for row in obj.matrix_world for v in row)
        names = tuple(slot.material.name if slot.material else "" for slot in obj.material_slots)
        snaps.append(
            spec.ObjectSnapshot(
                name=obj.name,
                matrix=matrix,
                material_names=names,
            )
        )
    return tuple(snaps)


def restore_snapshot(obj: Object, snap: spec.ObjectSnapshot) -> None:
    if len(snap.matrix) == 16:
        obj.matrix_world = Matrix(
            (
                snap.matrix[0:4],
                snap.matrix[4:8],
                snap.matrix[8:12],
                snap.matrix[12:16],
            )
        )
    materials = obj.data.materials
    materials.clear()
    for name in snap.material_names:
        if not name:
            materials.append(None)
            continue
        mat = bpy.data.materials.get(name)
        materials.append(mat)


def replace_mesh_geometry(
    obj: Object,
    verts: Sequence[tuple[float, float, float]],
    faces: Sequence[tuple[int, int, int]],
) -> None:
    mats = [slot.material for slot in obj.material_slots]
    old = obj.data
    mesh = bpy.data.meshes.new(old.name)
    mesh.from_pydata(list(verts), [], list(faces))
    mesh.validate(clean_customdata=False)
    mesh.update()
    obj.data = mesh
    for mat in mats:
        mesh.materials.append(mat)
    if old.users == 0:
        bpy.data.meshes.remove(old)


def tessellate_ocp(
    filepath: str,
    plan: spec.TessellationPlan,
) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]] | str:
    try:
        ocp_core.ensure_ocp()
    except ImportError as exc:
        return f"OCP not available ({exc})"
    shape, error = ocp_core.read_cad_shape(filepath)
    if error or shape is None:
        return error or "No shape"
    verts, faces = ocp_core.tessellate_shape(
        shape,
        deflection=plan.deflection,
        angular_deflection=plan.angular,
    )
    if not verts or not faces:
        return spec.REGENERATE_EMPTY
    return verts, faces


def regenerate_ocp(
    context: Context,
    cache: spec.CadCache,
    plan: spec.TessellationPlan,
) -> dict[str, Any]:
    existing = tagged_cad_meshes(context, cache.filepath)
    tess = tessellate_ocp(cache.filepath, plan)
    if isinstance(tess, str):
        return _result(False, tess, backend="OCP", objects=[])
    verts, faces = tess
    updated = spec.cache_record(
        cache.filepath,
        "OCP",
        quality=plan.quality,
        deflection=plan.deflection,
    )
    if existing:
        snaps = snapshot_objects(existing)
        primary = existing[0]
        replace_mesh_geometry(primary, verts, faces)
        if snaps:
            restore_snapshot(primary, snaps[0])
        extras = existing[1:]
        tag_cad_meshes([primary], updated)
        write_scene_cache(context, updated)
        bpy.ops.object.select_all(action="DESELECT")
        primary.select_set(True)
        context.view_layer.objects.active = primary
        return _result(
            True,
            spec.regenerated_message(
                cache.filepath,
                backend="OCP",
                quality=plan.quality,
                object_count=1,
            ),
            backend="OCP",
            objects=[primary],
            extras=extras,
        )

    result = ocp_import.import_cad_with_ocp(
        cache.filepath,
        deflection=plan.deflection,
    )
    if not result.get("ok"):
        return _result(
            False,
            result.get("message") or spec.REGENERATE_FAILED,
            backend="OCP",
            objects=[],
        )
    imported = list(result.get("objects") or [])
    tag_cad_meshes(imported, updated)
    write_scene_cache(context, updated)
    return _result(
        True,
        spec.regenerated_message(
            cache.filepath,
            backend="OCP",
            quality=plan.quality,
            object_count=len(imported),
        ),
        backend="OCP",
        objects=imported,
    )
