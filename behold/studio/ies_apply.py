# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply / tear down an IES profile on the active BEHOLD light."""

from __future__ import annotations

import os
from typing import Any, Iterable

import bpy
from bpy.types import Context, Node, NodeSocket, NodeTree, Object

from . import gobos as gobos_lib
from . import ies as spec
from . import light_presets
from . import light_shape
from . import lights as light_lib
from ..ui.messages import NO_LIGHTS

_SocketKey = str | int

GEOM_INCOMING_ALIASES = (spec.GEOM_INCOMING, "Incoming", 1)
IES_FAC_ALIASES = ("Fac", "Factor", "Color", 0)

SOCKET_ALIASES: dict[str, tuple[_SocketKey, ...]] = {
    "Vector": ("Vector", 0),
    "Fac": IES_FAC_ALIASES,
    "Strength": ("Strength", 0),
    "Scale": ("Scale", 1),
    "Surface": ("Surface", 0),
    "Emission": ("Emission", 0),
    "Color": ("Color", 0),
    spec.GEOM_INCOMING: GEOM_INCOMING_ALIASES,
}

SNAPSHOT_KEYS = (
    spec.PRIOR_TYPE_KEY,
    spec.PRIOR_SHAPE_KEY,
    spec.PRIOR_SIZE_KEY,
    spec.PRIOR_SIZE_Y_KEY,
    spec.PRIOR_SPREAD_KEY,
    spec.PRIOR_SOFT_KEY,
    spec.PRIOR_SPOT_SIZE_KEY,
    spec.PRIOR_SPOT_BLEND_KEY,
)


def apply_ies_in_scene(context: Context) -> dict[str, Any]:
    """Apply the scene IES path to the active BEHOLD light."""
    light = light_lib.get_active_behold_light(context)
    if light is None:
        return _result(False, NO_LIGHTS)
    settings = getattr(context.scene, "behold", None)
    strength = spec.DEFAULT_STRENGTH
    scale = spec.DEFAULT_SCALE
    path = ""
    if settings is not None:
        path = str(getattr(settings, "light_ies_filepath", "") or "")
        strength = float(getattr(settings, "light_ies_strength", strength))
        scale = float(getattr(settings, "light_ies_scale", scale))
    if not spec.normalize_filepath(path):
        return teardown_ies(context, light)
    return apply_ies_to_object(
        context,
        light,
        path,
        strength=strength,
        scale=scale,
    )


def apply_ies_to_object(
    context: Context,
    obj: Object,
    filepath: str,
    *,
    strength: float,
    scale: float,
) -> dict[str, Any]:
    data = getattr(obj, "data", None)
    if data is None:
        return _result(False, NO_LIGHTS)
    resolved = _resolve_filepath(filepath)
    problem = spec.classify_ies_filepath(filepath, resolved=resolved or None)
    if problem is not None:
        return _result(False, spec.path_problem_message(problem))

    light_type = str(getattr(data, "type", "") or "")
    plan = spec.plan_light_type(light_type)
    if plan.action == "reject":
        return _result(
            False,
            spec.NO_IES_TYPE,
            light=obj.name,
            light_type=light_type,
        )

    _snapshot_prior(obj, data, light_type)
    if plan.action == "convert":
        _convert_to_spot(data)

    graph = spec.node_graph_for(resolved, strength=strength, scale=scale)
    tree = _ensure_tree(data)
    if tree is None:
        return _result(False, spec.IES_NODES_FAILED, light=obj.name)

    tree.nodes.clear()
    created = _wire_plan(tree, graph)
    if created is None:
        tree.nodes.clear()
        if hasattr(data, "use_nodes"):
            data.use_nodes = False
        return _result(False, spec.IES_NODES_FAILED, light=obj.name)

    if not _write_values(created, graph):
        tree.nodes.clear()
        if hasattr(data, "use_nodes"):
            data.use_nodes = False
        return _result(False, spec.IES_NODES_FAILED, light=obj.name)

    _store(obj, spec.ACTIVE_KEY, True)
    _store(obj, spec.FILE_KEY, resolved)
    _clear_gobo_marker(context, obj)
    light_lib.set_active_behold_light(context, obj)
    return _result(
        True,
        spec.applied_message(resolved, obj.name),
        light=obj,
        filepath=resolved,
        strength=spec.clamp_strength(strength),
        scale=spec.clamp_scale(scale),
        converted=plan.action == "convert",
        graph=graph,
    )


def teardown_ies(context: Context, obj: Object) -> dict[str, Any]:
    """Drop IES nodes and restore the prior type / Shape. Does not restore Gobo."""
    data = getattr(obj, "data", None)
    if data is not None:
        tree = getattr(data, "node_tree", None)
        if tree is not None:
            tree.nodes.clear()
        if hasattr(data, "use_nodes"):
            data.use_nodes = False
    restored_type = _restore_prior_type(obj, data)
    _clear_ies_keys(obj)
    restored_shape = _restore_shape(context, obj)
    _sync_scene_path(context, "")
    return _result(
        True,
        spec.cleared_message(),
        light=obj,
        restored_type=restored_type,
        restored_shape=restored_shape,
    )


def teardown_ies_in_scene(context: Context) -> dict[str, Any]:
    light = light_lib.get_active_behold_light(context)
    if light is None:
        _sync_scene_path(context, "")
        return _result(False, NO_LIGHTS)
    return teardown_ies(context, light)


def release_ies_if_active(context: Context, obj: Object) -> bool:
    """Restore prior type when Gobo / Shape takes the node tree back.

    Circular with gobo apply: gobos need the area type back before they
    rebuild falloff. Does not re-apply gobo (the caller owns that).
    """
    if not _is_ies_active(obj):
        return False
    data = getattr(obj, "data", None)
    if data is not None:
        tree = getattr(data, "node_tree", None)
        if tree is not None:
            tree.nodes.clear()
        if hasattr(data, "use_nodes"):
            data.use_nodes = False
    _restore_prior_type(obj, data)
    _clear_ies_keys(obj)
    _sync_scene_path(context, "")
    return True


def on_ies_filepath_update(settings, context: Context) -> None:
    if context is None or getattr(context, "scene", None) is None:
        return
    if light_lib.get_active_behold_light(context) is None:
        return
    path = spec.normalize_filepath(getattr(settings, "light_ies_filepath", "") or "")
    if not path:
        light = light_lib.get_active_behold_light(context)
        if light is not None and _is_ies_active(light):
            teardown_ies(context, light)
        return
    apply_ies_in_scene(context)


def on_ies_values_update(settings, context: Context) -> None:
    del settings
    if context is None or getattr(context, "scene", None) is None:
        return
    light = light_lib.get_active_behold_light(context)
    if light is None:
        return
    path = ""
    scene_settings = getattr(context.scene, "behold", None)
    if scene_settings is not None:
        path = spec.normalize_filepath(
            getattr(scene_settings, "light_ies_filepath", "") or ""
        )
    if not path:
        return
    apply_ies_in_scene(context)


def _is_ies_active(obj: Object) -> bool:
    try:
        return bool(obj.get(spec.ACTIVE_KEY, False))
    except (TypeError, AttributeError):
        return False


def _snapshot_prior(obj: Object, data: object, light_type: str) -> None:
    if _is_ies_active(obj):
        return
    _store(obj, spec.PRIOR_TYPE_KEY, light_type)
    _store(obj, spec.PRIOR_SHAPE_KEY, str(getattr(data, "shape", "") or ""))
    _store(obj, spec.PRIOR_SIZE_KEY, float(getattr(data, "size", 0.0) or 0.0))
    _store(obj, spec.PRIOR_SIZE_Y_KEY, float(getattr(data, "size_y", 0.0) or 0.0))
    _store(obj, spec.PRIOR_SPREAD_KEY, float(getattr(data, "spread", 0.0) or 0.0))
    _store(
        obj,
        spec.PRIOR_SOFT_KEY,
        float(getattr(data, "shadow_soft_size", 0.0) or 0.0),
    )
    _store(
        obj,
        spec.PRIOR_SPOT_SIZE_KEY,
        float(getattr(data, "spot_size", 0.0) or 0.0),
    )
    _store(
        obj,
        spec.PRIOR_SPOT_BLEND_KEY,
        float(getattr(data, "spot_blend", 0.0) or 0.0),
    )


def _convert_to_spot(data: object) -> None:
    if hasattr(data, "type"):
        try:
            data.type = "SPOT"
        except (TypeError, ValueError, AttributeError):
            return
    if hasattr(data, "spot_size"):
        try:
            data.spot_size = spec.default_spot_size_radians()
        except (TypeError, ValueError, AttributeError):
            pass
    if hasattr(data, "spot_blend"):
        try:
            data.spot_blend = spec.DEFAULT_SPOT_BLEND
        except (TypeError, ValueError, AttributeError):
            pass
    if hasattr(data, "shadow_soft_size"):
        try:
            data.shadow_soft_size = spec.DEFAULT_SHADOW_SOFT_SIZE
        except (TypeError, ValueError, AttributeError):
            pass


def _restore_prior_type(obj: Object, data: object | None) -> str:
    prior = _read_str(obj, spec.PRIOR_TYPE_KEY)
    if not prior or data is None or not hasattr(data, "type"):
        return ""
    try:
        data.type = prior
    except (TypeError, ValueError, AttributeError):
        return ""
    _restore_float(data, "size", obj, spec.PRIOR_SIZE_KEY)
    _restore_float(data, "size_y", obj, spec.PRIOR_SIZE_Y_KEY)
    _restore_float(data, "spread", obj, spec.PRIOR_SPREAD_KEY)
    _restore_float(data, "shadow_soft_size", obj, spec.PRIOR_SOFT_KEY)
    _restore_float(data, "spot_size", obj, spec.PRIOR_SPOT_SIZE_KEY)
    _restore_float(data, "spot_blend", obj, spec.PRIOR_SPOT_BLEND_KEY)
    shape = _read_str(obj, spec.PRIOR_SHAPE_KEY)
    if shape and hasattr(data, "shape"):
        try:
            data.shape = shape
        except (TypeError, ValueError, AttributeError):
            pass
    return prior


def _restore_float(data: object, attr: str, obj: Object, key: str) -> None:
    if not hasattr(data, attr):
        return
    try:
        raw = obj.get(key, None)
    except (TypeError, AttributeError):
        return
    if raw is None:
        return
    try:
        setattr(data, attr, float(raw))
    except (TypeError, ValueError, AttributeError):
        return


def _restore_shape(context: Context, obj: Object) -> bool:
    shape_id = ""
    try:
        shape_id = str(obj.get(light_presets.PRESET_ID_KEY, "") or "")
    except (TypeError, AttributeError):
        shape_id = ""
    if not shape_id or light_presets.get_preset(shape_id) is None:
        return False
    _, product_size = light_lib.product_frame(context)
    current = float(getattr(obj.data, "size", 1.0) or 1.0)
    scale = light_presets.resolve_shape_scale(
        product_size=product_size,
        current_size=current,
    )
    result = light_shape.apply_preset_to_object(obj, shape_id, scale=scale)
    return bool(result.get("ok"))


def _clear_gobo_marker(context: Context, obj: Object) -> None:
    """IES owns the node tree — Gobo enum goes to None without RNA teardown."""
    _store(obj, gobos_lib.PRESET_ID_KEY, gobos_lib.DEFAULT_PRESET)
    settings = getattr(context.scene, "behold", None)
    if settings is None or not hasattr(settings, "light_gobo_preset"):
        return
    current = str(getattr(settings, "light_gobo_preset", "") or "")
    if current == gobos_lib.DEFAULT_PRESET:
        return
    try:
        settings["light_gobo_preset"] = gobos_lib.DEFAULT_PRESET
    except (TypeError, AttributeError, KeyError):
        try:
            settings.light_gobo_preset = gobos_lib.DEFAULT_PRESET
        except (TypeError, AttributeError):
            pass


def _ensure_tree(data: object) -> NodeTree | None:
    if hasattr(data, "use_nodes"):
        data.use_nodes = True
    return getattr(data, "node_tree", None)


def _store(obj: Object, key: str, value: Any) -> None:
    try:
        obj[key] = value
    except (TypeError, AttributeError):
        pass


def _read_str(obj: Object, key: str) -> str:
    try:
        return str(obj.get(key, "") or "")
    except (TypeError, AttributeError):
        return ""


def _clear_ies_keys(obj: Object) -> None:
    for key in (spec.ACTIVE_KEY, spec.FILE_KEY, *SNAPSHOT_KEYS):
        try:
            if key in obj:
                del obj[key]
        except (TypeError, AttributeError, KeyError):
            try:
                obj[key] = "" if key != spec.ACTIVE_KEY else False
            except (TypeError, AttributeError):
                pass


def _sync_scene_path(context: Context, filepath: str) -> None:
    settings = getattr(context.scene, "behold", None)
    if settings is None or not hasattr(settings, "light_ies_filepath"):
        return
    current = str(getattr(settings, "light_ies_filepath", "") or "")
    if current == filepath:
        return
    try:
        settings["light_ies_filepath"] = filepath
    except (TypeError, AttributeError, KeyError):
        try:
            settings.light_ies_filepath = filepath
        except (TypeError, AttributeError):
            pass


def _resolve_filepath(filepath: str) -> str:
    raw = spec.normalize_filepath(filepath)
    if not raw:
        return ""
    try:
        expanded = bpy.path.abspath(raw)
    except Exception:  # noqa: BLE001 — keep raw path when Blender cannot expand
        expanded = os.path.expanduser(raw)
    else:
        expanded = os.path.expanduser(expanded)
    return os.path.abspath(expanded) if expanded else ""


def _result(ok: bool, message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "message": message}
    payload.update(extra)
    return payload


def _new_node(tree: NodeTree, types: Iterable[str], name: str) -> Node | None:
    for bl_idname in types:
        try:
            node = tree.nodes.new(bl_idname)
        except (RuntimeError, TypeError, ValueError):
            continue
        node.name = name
        node.label = name
        return node
    return None


def _wire_plan(tree: NodeTree, graph: spec.NodeGraph) -> dict[str, Node] | None:
    created: dict[str, Node] = {}
    for node_spec in graph.nodes:
        node = _new_node(tree, (node_spec.bl_idname,), node_spec.name)
        if node is None:
            if node_spec.key == "geom":
                continue
            return None
        created[node_spec.key] = node
    for link in graph.links:
        src = created.get(link.from_key)
        dst = created.get(link.to_key)
        if src is None or dst is None:
            if link.from_key == "geom":
                continue
            return None
        from_key: _SocketKey = (
            graph.geom_socket if link.from_key == "geom" else link.from_socket
        )
        out_sock = _socket(src, "output", from_key)
        if out_sock is None and link.from_key == "geom":
            for alias in GEOM_INCOMING_ALIASES:
                out_sock = _socket(src, "output", alias)
                if out_sock is not None:
                    break
        in_sock = _socket(dst, "input", link.to_socket)
        if out_sock is None or in_sock is None:
            if link.from_key == "geom":
                continue
            return None
        tree.links.new(out_sock, in_sock)
    if "ies" not in created or "emission" not in created or "output" not in created:
        return None
    return created


def _socket(node: Node, side: str, key: _SocketKey) -> NodeSocket | None:
    sockets = node.outputs if side == "output" else node.inputs
    aliases: tuple[_SocketKey, ...]
    if isinstance(key, str):
        aliases = SOCKET_ALIASES.get(key, (key,))
    else:
        aliases = (key,)
    for alias in aliases:
        try:
            return sockets[alias]
        except (KeyError, IndexError, TypeError):
            continue
    return None


def _set_vector_input(
    node: Node | None,
    name: str,
    value: tuple[float, float, float],
) -> None:
    if node is None:
        return
    sock = _socket(node, "input", name)
    if sock is None:
        return
    try:
        sock.default_value = value
    except (TypeError, ValueError):
        pass


def _set_float_input(node: Node | None, names: tuple[str, ...], value: float) -> None:
    if node is None:
        return
    for name in names:
        sock = _socket(node, "input", name)
        if sock is None:
            continue
        try:
            sock.default_value = value
            return
        except (TypeError, ValueError):
            continue


def _set_color_input(
    node: Node | None,
    names: tuple[str, ...],
    value: tuple[float, float, float, float],
) -> None:
    if node is None:
        return
    for name in names:
        sock = _socket(node, "input", name)
        if sock is None:
            continue
        try:
            sock.default_value = value
            return
        except (TypeError, ValueError):
            continue


def _write_values(created: dict[str, Node], graph: spec.NodeGraph) -> bool:
    mapping = created.get("mapping")
    _set_vector_input(mapping, "Scale", graph.scale)

    ies = created.get("ies")
    if ies is None:
        return False
    if hasattr(ies, "mode"):
        try:
            ies.mode = graph.ies_mode
        except (TypeError, ValueError, AttributeError):
            pass
    if hasattr(ies, "filepath"):
        try:
            ies.filepath = graph.filepath
        except (TypeError, ValueError, AttributeError):
            return False
    else:
        return False
    _set_float_input(ies, ("Strength",), graph.strength)

    emission = created.get("emission")
    _set_color_input(emission, ("Color",), graph.emission_color)
    _set_float_input(emission, ("Strength",), graph.emission_strength)
    return True
