# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply / tear down procedural gobos on the active BEHOLD light."""

from __future__ import annotations

from typing import Any, Iterable

from bpy.types import Context, Node, NodeSocket, NodeTree, Object

from . import gobos as spec
from . import ies as ies_spec
from . import ies_apply
from . import light_presets
from . import light_shape
from . import lights as light_lib
from ..ui.messages import NO_LIGHTS

_SocketKey = str | int

MIX_NODE_TYPES = (spec.TYPE_MIX, "ShaderNodeMix")
TEXCOORD_ALIASES = (spec.TEXCOORD_UV, "Generated", 0)

SOCKET_ALIASES: dict[str, tuple[_SocketKey, ...]] = {
    "Vector": ("Vector", 0),
    "Fac": ("Fac", "Factor", 0),
    "Color": ("Color", "Result", 0),
    "Color1": ("Color1", "A", 1),
    "Color2": ("Color2", "B", 2),
    "Surface": ("Surface", 0),
    "Emission": ("Emission", 0),
    "Scale": ("Scale", 1),
    "Strength": ("Strength", 0),
}


def apply_gobo_in_scene(context: Context) -> dict[str, Any]:
    """Apply the scene gobo preset to the active BEHOLD light."""
    light = light_lib.get_active_behold_light(context)
    if light is None:
        return _result(False, NO_LIGHTS)
    settings = getattr(context.scene, "behold", None)
    preset_id = spec.DEFAULT_PRESET
    scale = spec.DEFAULT_SCALE
    strength = spec.DEFAULT_STRENGTH
    if settings is not None:
        preset_id = str(getattr(settings, "light_gobo_preset", preset_id) or preset_id)
        scale = float(getattr(settings, "light_gobo_scale", scale))
        strength = float(getattr(settings, "light_gobo_strength", strength))
    return apply_gobo_to_object(
        context,
        light,
        preset_id,
        scale=scale,
        strength=strength,
    )


def apply_gobo_to_object(
    context: Context,
    obj: Object,
    preset_id: str,
    *,
    scale: float,
    strength: float,
) -> dict[str, Any]:
    preset = spec.get_preset(preset_id)
    if preset is None:
        return _result(False, spec.unknown_gobo_message(preset_id))
    data = getattr(obj, "data", None)
    if data is None:
        return _result(False, NO_LIGHTS)
    ies_apply.release_ies_if_active(context, obj)
    data = getattr(obj, "data", None)
    if data is None:
        return _result(False, NO_LIGHTS)
    light_type = str(getattr(data, "type", "") or "")
    if light_type not in spec.SUPPORTED_TYPES:
        return _result(False, spec.NO_GOBO_TYPE, light=obj.name, light_type=light_type)

    if preset.id == "NONE":
        return teardown_gobo(context, obj)

    graph = spec.node_graph_for(preset.id, scale=scale, strength=strength)
    if graph is None:
        return teardown_gobo(context, obj)

    tree = _ensure_tree(data)
    if tree is None:
        return _result(False, spec.GOBO_NODES_FAILED, light=obj.name)

    tree.nodes.clear()
    created = _wire_plan(tree, graph)
    if created is None:
        tree.nodes.clear()
        if hasattr(data, "use_nodes"):
            data.use_nodes = False
        return _result(False, spec.GOBO_NODES_FAILED, light=obj.name)

    _write_values(created, graph)
    _store_preset(obj, preset.id)
    light_lib.set_active_behold_light(context, obj)
    return _result(
        True,
        spec.applied_message(preset.label, obj.name),
        light=obj,
        preset=preset,
        graph=graph,
        scale=spec.clamp_scale(scale),
        strength=spec.clamp_strength(strength),
    )


def teardown_gobo(context: Context, obj: Object) -> dict[str, Any]:
    """Drop gobo nodes and restore Shape falloff when IES is not on."""
    _store_preset(obj, "NONE")
    try:
        ies_on = bool(obj.get(ies_spec.ACTIVE_KEY, False))
    except (TypeError, AttributeError):
        ies_on = False
    if ies_on:
        return _result(True, spec.cleared_message(), light=obj, restored_shape=False)
    data = getattr(obj, "data", None)
    if data is not None:
        tree = getattr(data, "node_tree", None)
        if tree is not None:
            tree.nodes.clear()
        if hasattr(data, "use_nodes"):
            data.use_nodes = False
    restored = _restore_shape(context, obj)
    return _result(
        True,
        spec.cleared_message(),
        light=obj,
        restored_shape=restored,
    )


def on_gobo_update(settings, context: Context) -> None:
    """RNA update: preset / scale / strength rewrite the active light live."""
    del settings
    if context is None or getattr(context, "scene", None) is None:
        return
    if light_lib.get_active_behold_light(context) is None:
        return
    apply_gobo_in_scene(context)


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


def _ensure_tree(data: object) -> NodeTree | None:
    if hasattr(data, "use_nodes"):
        data.use_nodes = True
    return getattr(data, "node_tree", None)


def _store_preset(obj: Object, preset_id: str) -> None:
    try:
        obj[spec.PRESET_ID_KEY] = preset_id
    except (TypeError, AttributeError):
        pass


def _result(ok: bool, message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "message": message}
    payload.update(extra)
    return payload


def _type_for_spec(node: spec.NodeSpec) -> tuple[str, ...]:
    if node.bl_idname == spec.TYPE_MIX:
        return MIX_NODE_TYPES
    return (node.bl_idname,)


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
        node = _new_node(tree, _type_for_spec(node_spec), node_spec.name)
        if node is None:
            return None
        created[node_spec.key] = node
    for link in graph.links:
        src = created.get(link.from_key)
        dst = created.get(link.to_key)
        if src is None or dst is None:
            return None
        from_key = graph.texcoord_socket if link.from_key == "tex_coord" else link.from_socket
        out_sock = _socket(src, "output", from_key)
        if out_sock is None and link.from_key == "tex_coord":
            for alias in TEXCOORD_ALIASES:
                out_sock = _socket(src, "output", alias)
                if out_sock is not None:
                    break
        in_sock = _socket(dst, "input", link.to_socket)
        if out_sock is None or in_sock is None:
            return None
        tree.links.new(out_sock, in_sock)
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


def _set_vector_input(node: Node | None, name: str, value: tuple[float, float, float]) -> None:
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


def _write_ramp(ramp_node: Node | None, stops: tuple[spec.RampStop, ...]) -> None:
    if ramp_node is None:
        return
    ramp = getattr(ramp_node, "color_ramp", None)
    if ramp is None:
        return
    elements = ramp.elements
    while len(elements) < len(stops):
        nxt = stops[len(elements)]
        elements.new(nxt.position)
    for index, stop in enumerate(stops):
        element = elements[index]
        element.position = stop.position
        element.color = stop.color


def _write_values(created: dict[str, Node], graph: spec.NodeGraph) -> None:
    mapping = created.get("mapping")
    _set_vector_input(mapping, "Location", graph.mapping.location)
    _set_vector_input(mapping, "Scale", graph.mapping.scale)

    wave = created.get("wave")
    if wave is not None:
        for attr, value in (
            ("wave_type", graph.wave_type),
            ("bands_direction", graph.bands_direction),
            ("wave_profile", graph.wave_profile),
        ):
            if hasattr(wave, attr):
                try:
                    setattr(wave, attr, value)
                except (TypeError, ValueError):
                    pass

    brick = created.get("brick")
    if brick is not None:
        if hasattr(brick, "offset"):
            try:
                brick.offset = graph.brick_offset
            except (TypeError, ValueError):
                pass
        _set_float_input(brick, ("Mortar Size", "MortarSize"), graph.brick_mortar)
        _set_float_input(
            brick,
            ("Mortar Smooth", "MortarSmooth"),
            graph.brick_mortar_smooth,
        )

    gradient = created.get("gradient")
    if gradient is not None and hasattr(gradient, "gradient_type"):
        try:
            gradient.gradient_type = graph.gradient_type
        except (TypeError, ValueError):
            pass

    _write_ramp(created.get("ramp"), graph.ramp)

    mix = created.get("mix")
    if mix is not None:
        if hasattr(mix, "blend_type"):
            try:
                mix.blend_type = graph.mix_blend
            except (TypeError, ValueError):
                pass
        if hasattr(mix, "data_type"):
            try:
                mix.data_type = "RGBA"
            except (TypeError, ValueError):
                pass
        _set_float_input(mix, ("Fac", "Factor"), graph.mix_fac)
        _set_color_input(mix, ("Color1", "A"), graph.mix_open)

    emission = created.get("emission")
    _set_float_input(emission, ("Strength",), graph.emission_strength)
