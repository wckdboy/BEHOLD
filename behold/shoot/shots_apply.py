# SPDX-License-Identifier: GPL-3.0-or-later
"""Capture / apply named shots on a Blender scene."""

from __future__ import annotations

from typing import Any

import bpy
from bpy.types import Context

from ..studio import cameras as camera_lib
from ..studio import world_apply
from ..studio.tones import backdrop_tone_rgba
from ..ui.messages import (
    NO_SHOT_TO_APPLY,
    NO_SHOT_TO_REMOVE,
    NO_SHOT_TO_RENAME,
    SHOT_NAME_EMPTY,
    shot_camera_missing,
    shot_not_found,
)
from . import shots as shots_lib


def _settings(context: Context):
    return context.scene.behold


def _collection(context: Context):
    return _settings(context).shots


def iter_shot_names(context: Context) -> list[str]:
    return [item.name for item in _collection(context)]


def resolve_shot_item(context: Context, *, shot_name: str = "", shot_index: int = -1):
    collection = _collection(context)
    if 0 <= shot_index < len(collection):
        return collection[shot_index], shot_index
    needle = shots_lib.sanitize_shot_name(shot_name)
    if not needle:
        return None, -1
    for index, item in enumerate(collection):
        if shots_lib.sanitize_shot_name(item.name) == needle:
            return item, index
    return None, -1


def write_item(item, payload: dict[str, Any]) -> None:
    values = shots_lib.item_values(payload)
    for key, value in values.items():
        setattr(item, key, value)


def capture_from_scene(context: Context, *, name: str = "") -> dict[str, Any]:
    settings = _settings(context)
    cam = camera_lib.resolve_shoot_camera(context)
    camera_name = cam.name if cam is not None else (settings.active_camera_name or "")
    existing = iter_shot_names(context)
    payload = shots_lib.snapshot_from_mapping(
        settings,
        name=name,
        camera_name=camera_name,
    )
    desired = shots_lib.sanitize_shot_name(name) or shots_lib.default_shot_name(
        existing, camera_name=camera_name
    )
    payload["name"] = shots_lib.unique_shot_name(existing, desired)
    return payload


def add_shot_from_scene(context: Context, *, name: str = "") -> dict[str, Any]:
    payload = capture_from_scene(context, name=name)
    collection = _collection(context)
    item = collection.add()
    write_item(item, payload)
    index = len(collection) - 1
    _settings(context).active_shot_index = index
    return {"ok": True, "name": payload["name"], "index": index, "shot": payload}


def apply_shot_to_scene(
    context: Context,
    *,
    shot_name: str = "",
    shot_index: int = -1,
) -> dict[str, Any]:
    item, index = resolve_shot_item(
        context, shot_name=shot_name, shot_index=shot_index
    )
    if item is None:
        message = (
            shot_not_found(shot_name)
            if shots_lib.sanitize_shot_name(shot_name)
            else NO_SHOT_TO_APPLY
        )
        return {"ok": False, "message": message}

    payload = shots_lib.snapshot_from_mapping(item)
    result = apply_payload_to_scene(context, payload)
    _settings(context).active_shot_index = index
    warning = str(result.get("warning") or "")
    return {
        "ok": True,
        "name": payload["name"] or item.name,
        "index": index,
        "payload": payload,
        "written": result["written"],
        "warning": warning,
        "message": warning or shots_lib.shot_applied_message(payload["name"] or item.name),
    }


def apply_payload_to_scene(context: Context, payload: dict[str, Any]) -> dict[str, Any]:
    """Write a shot payload onto the scene. Does not touch the product mesh."""
    result = shots_lib.apply_shot_to_mapping(payload, _settings(context))
    data = result["payload"]
    camera_warning = _restore_camera(context, data)
    world_warning = _restore_world(context, data)
    _restore_backdrop_tone(context)
    warning = camera_warning or world_warning
    return {
        "ok": True,
        "payload": data,
        "written": result["written"],
        "warning": warning,
        "name": data.get("name") or "",
    }


def remove_shot_from_scene(
    context: Context,
    *,
    shot_name: str = "",
    shot_index: int = -1,
) -> dict[str, Any]:
    item, index = resolve_shot_item(
        context, shot_name=shot_name, shot_index=shot_index
    )
    if item is None:
        message = (
            shot_not_found(shot_name)
            if shots_lib.sanitize_shot_name(shot_name)
            else NO_SHOT_TO_REMOVE
        )
        return {"ok": False, "message": message}
    removed_name = item.name
    collection = _collection(context)
    collection.remove(index)
    settings = _settings(context)
    settings.active_shot_index = shots_lib.clamp_active_index(
        len(collection), settings.active_shot_index
    )
    return {"ok": True, "name": removed_name, "index": index}


def rename_shot_on_scene(
    context: Context,
    *,
    shot_name: str = "",
    shot_index: int = -1,
    new_name: str = "",
) -> dict[str, Any]:
    item, index = resolve_shot_item(
        context, shot_name=shot_name, shot_index=shot_index
    )
    if item is None:
        message = (
            shot_not_found(shot_name)
            if shots_lib.sanitize_shot_name(shot_name)
            else NO_SHOT_TO_RENAME
        )
        return {"ok": False, "message": message}
    desired = shots_lib.sanitize_shot_name(new_name)
    if not desired:
        return {"ok": False, "message": SHOT_NAME_EMPTY}
    others = [
        other.name
        for i, other in enumerate(_collection(context))
        if i != index
    ]
    if shots_lib.sanitize_shot_name(desired) in {
        shots_lib.sanitize_shot_name(name) for name in others
    }:
        return {"ok": False, "message": shots_lib.shot_name_taken(desired)}
    old = item.name
    item.name = desired
    _settings(context).active_shot_index = index
    return {"ok": True, "old_name": old, "name": desired, "index": index}


def _restore_camera(context: Context, payload: dict[str, Any]) -> str:
    """Switch the scene camera. Never touches product meshes."""
    name = (payload.get("camera_name") or payload.get("main_camera_name") or "").strip()
    if not name:
        return ""
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "CAMERA":
        return shot_camera_missing(name)
    settings = _settings(context)
    if camera_lib.is_behold_camera(obj):
        camera_lib.set_active_behold_camera(context, obj)
    else:
        context.scene.camera = obj
        settings.active_camera_name = obj.name
    main = (payload.get("main_camera_name") or obj.name).strip()
    if main:
        settings.main_camera_name = main
    return ""


def _restore_world(context: Context, payload: dict[str, Any]) -> str:
    """Reload HDRI from the shot, or drop back to a solid studio world."""
    if shots_lib.shot_has_hdri(payload):
        result = world_apply.apply_hdri_from_settings(context)
        if not result.get("ok"):
            return str(result.get("message") or "")
        return ""
    world_apply.setup_solid_world(context.scene)
    return ""


def _restore_backdrop_tone(context: Context) -> None:
    """Retint the cyclorama sweep from the shot tone. Never rebuilds or deletes meshes."""
    tone = backdrop_tone_rgba(_settings(context))
    mat = bpy.data.materials.get("BEHOLD_Sweep")
    if mat is None or not getattr(mat, "use_nodes", False) or mat.node_tree is None:
        return
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf is None:
        return
    if "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = tone
