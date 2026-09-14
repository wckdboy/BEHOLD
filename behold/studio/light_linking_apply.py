# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply light / shadow linking on the active BEHOLD light (Blender RNA)."""

from __future__ import annotations

from typing import Any, Literal, Never

import bpy
from bpy.types import Collection, Context, Object

from . import cameras as camera_lib
from . import light_linking as spec
from . import lights as light_lib
from .camera_ids import is_studio_mesh_name
from ..cad.material_assist import is_behold_product
from ..ui.messages import NO_LIGHTS

_SelectedAction = Literal["LINK", "EXCLUDE", "UNLINK", "CYCLE"]


def probe_api(obj: Object | None) -> dict[str, bool]:
    linking = getattr(obj, "light_linking", None) if obj is not None else None
    return {
        "has_light_linking": linking is not None,
        "has_receiver": linking is not None and hasattr(linking, "receiver_collection"),
        "has_blocker": linking is not None and hasattr(linking, "blocker_collection"),
    }


def render_engine(context: Context) -> str:
    render = getattr(context.scene, "render", None)
    return str(getattr(render, "engine", "") or "")


def _object_rows(context: Context) -> list[spec.ObjectRow]:
    selected = {obj.name for obj in context.selected_objects}
    rows: list[spec.ObjectRow] = []
    for obj in context.scene.objects:
        ob_type = str(getattr(obj, "type", "") or "")
        tagged = ob_type == "MESH" and is_behold_product(obj)
        rows.append(
            spec.ObjectRow(
                name=obj.name,
                ob_type=ob_type,
                tagged_product=tagged,
                selected=obj.name in selected,
            )
        )
    return rows


def _result(ok: bool, message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "message": message}
    payload.update(extra)
    return payload


def _resolve_kind(context: Context, kind: str) -> spec.KindId | dict[str, Any]:
    raw = (kind or "").strip()
    if not raw:
        settings = getattr(context.scene, "behold", None)
        raw = str(getattr(settings, "light_linking_kind", spec.DEFAULT_KIND) or "")
    if spec.is_kind(raw):
        if raw == "LIGHT":
            return "LIGHT"
        return "SHADOW"
    return _result(False, spec.UNKNOWN_KIND)


def _gate(context: Context, light: Object, kind: spec.KindId) -> str | None:
    probe = probe_api(light)
    return spec.capability_problem(
        engine=render_engine(context),
        has_light_linking=probe["has_light_linking"],
        has_receiver=probe["has_receiver"],
        has_blocker=probe["has_blocker"],
        kind=kind,
    )


def _collection_for(light: Object, kind: spec.KindId) -> Collection | None:
    linking = getattr(light, "light_linking", None)
    if linking is None:
        return None
    return getattr(linking, spec.collection_attr(kind), None)


def _set_collection(light: Object, kind: spec.KindId, collection: Collection | None) -> bool:
    linking = getattr(light, "light_linking", None)
    if linking is None:
        return False
    try:
        setattr(linking, spec.collection_attr(kind), collection)
    except (AttributeError, TypeError, RuntimeError):
        return False
    return True


def _discard_owned(collection: Collection | None) -> None:
    if collection is None:
        return
    if not spec.is_owned_collection_name(collection.name):
        return
    try:
        bpy.data.collections.remove(collection)
    except RuntimeError:
        pass


def _ensure_collection(light: Object, kind: spec.KindId) -> Collection | None:
    current = _collection_for(light, kind)
    if current is not None:
        return current
    name = spec.collection_name(light.name, kind)
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
        hide = getattr(coll, "hide_viewport", None)
        if hide is not None:
            try:
                coll.hide_viewport = True
            except (AttributeError, TypeError, RuntimeError):
                pass
    if not _set_collection(light, kind, coll):
        return None
    return coll


def _scene_object(name: str, context: Context) -> Object | None:
    obj = bpy.data.objects.get(name)
    if obj is None:
        return None
    if obj.name not in context.scene.objects:
        return None
    return obj


def _write_members(
    collection: Collection,
    desired: dict[str, str],
    context: Context,
) -> bool:
    current = spec.members_from_collection(collection)
    to_link, to_unlink, state_updates = spec.plan_collection_sync(current, desired)
    objects = collection.objects
    for name in to_unlink:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        try:
            if obj.name in objects:
                objects.unlink(obj)
        except RuntimeError:
            return False
    for name in to_link:
        obj = _scene_object(name, context)
        if obj is None:
            continue
        try:
            if obj.name not in objects:
                objects.link(obj)
        except RuntimeError:
            return False
    for name, state in state_updates.items():
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        entry = spec.lookup_collection_entry(collection, obj.name)
        if entry is None:
            continue
        if not spec.set_entry_state(entry, state if state == spec.EXCLUDE else spec.INCLUDE):
            if state == spec.EXCLUDE:
                return False
    return True


def _apply_desired(
    light: Object,
    kind: spec.KindId,
    desired: dict[str, str],
    context: Context,
) -> bool:
    if not desired:
        old = _collection_for(light, kind)
        if not _set_collection(light, kind, None):
            return False
        _discard_owned(old)
        return True
    collection = _ensure_collection(light, kind)
    if collection is None:
        return False
    return _write_members(collection, desired, context)


def _kinds_for_solo(light: Object) -> tuple[spec.KindId, ...]:
    probe = probe_api(light)
    kinds: list[spec.KindId] = ["LIGHT"]
    if spec.shadow_api_ok(has_blocker=probe["has_blocker"]):
        kinds.append("SHADOW")
    return tuple(kinds)


def run_selected(
    context: Context,
    action: _SelectedAction,
    *,
    kind: str = "",
) -> dict[str, Any]:
    resolved = _resolve_kind(context, kind)
    if isinstance(resolved, dict):
        return resolved
    light = light_lib.get_active_behold_light(context)
    if light is None:
        return _result(False, NO_LIGHTS)
    problem = _gate(context, light, resolved)
    if problem:
        return _result(False, problem)

    rows = _object_rows(context)
    names = spec.selected_target_names(rows, emitter_name=light.name)
    if action != "UNLINK" and not names:
        return _result(False, spec.NO_SELECTION)

    current = spec.members_from_collection(_collection_for(light, resolved))
    if action == "UNLINK" and not names:
        desired: dict[str, str] = {}
        cleared = True
        count = len(current)
    else:
        desired = spec.apply_member_action(current, names, action)
        cleared = action == "UNLINK" and not desired
        count = len(names)

    if not _apply_desired(light, resolved, desired, context):
        return _result(False, spec.LINKING_FAILED)

    if action == "UNLINK":
        message = spec.unlinked_message(
            resolved, light.name, count, cleared=cleared or not desired
        )
    elif action == "CYCLE":
        message = spec.cycled_message(resolved, light.name, desired)
    elif action == "EXCLUDE":
        message = spec.linked_message(resolved, light.name, count, spec.EXCLUDE)
    elif action == "LINK":
        message = spec.linked_message(resolved, light.name, count, spec.INCLUDE)
    else:
        unreachable: Never = action
        raise RuntimeError(f"unhandled linking action: {unreachable}")
    return _result(True, message, light=light, kind=resolved, members=desired)


def link_selected(context: Context, *, kind: str = "") -> dict[str, Any]:
    return run_selected(context, "CYCLE", kind=kind)


def exclude_selected(context: Context, *, kind: str = "") -> dict[str, Any]:
    return run_selected(context, "EXCLUDE", kind=kind)


def unlink_selected(context: Context, *, kind: str = "") -> dict[str, Any]:
    return run_selected(context, "UNLINK", kind=kind)


def solo_product(context: Context) -> dict[str, Any]:
    light = light_lib.get_active_behold_light(context)
    if light is None:
        return _result(False, NO_LIGHTS)
    problem = _gate(context, light, "LIGHT")
    if problem:
        return _result(False, problem)

    rows = _object_rows(context)
    products = spec.product_target_names(rows)
    if not products:
        # Fall back to camera framing targets when the snap missed tags.
        products = tuple(
            obj.name
            for obj in camera_lib.product_targets(context)
            if obj.type == "MESH" and not is_studio_mesh_name(obj.name)
        )
    if not products:
        return _result(False, spec.NO_PRODUCT_TO_SOLO)

    desired = spec.solo_members(products)
    kinds = _kinds_for_solo(light)
    for kind in kinds:
        extra = _gate(context, light, kind)
        if extra:
            if kind == "SHADOW":
                continue
            return _result(False, extra)
        if not _apply_desired(light, kind, desired, context):
            return _result(False, spec.LINKING_FAILED)
    return _result(
        True,
        spec.solo_message(light.name, len(desired), kinds=kinds),
        light=light,
        members=desired,
        kinds=kinds,
    )

