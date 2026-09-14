# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply BEHOLD area-light shape presets (RNA + optional emission nodes)."""

from __future__ import annotations

from typing import Any

import bpy
from bpy.types import Context, Node, NodeSocket, NodeTree, Object

from . import light_presets as presets
from . import lights as light_lib

_SocketKey = str | int


def apply_preset_to_object(
    obj: Object,
    preset_id: str,
    *,
    scale: float,
) -> dict[str, Any]:
    preset = presets.get_preset(preset_id)
    if preset is None:
        return {"ok": False, "message": presets.unknown_preset_message(preset_id)}
    data = obj.data
    written = presets.apply_shape_props(data, preset, scale=scale)
    graph = presets.node_graph_for(preset.nodes)
    if graph is None:
        if hasattr(data, "use_nodes"):
            data.use_nodes = False
        written["use_nodes"] = False
    else:
        _apply_node_graph(data, graph)
        written["use_nodes"] = True
    try:
        obj[presets.PRESET_ID_KEY] = preset.id
    except (TypeError, AttributeError):
        pass
    return {
        "ok": True,
        "message": presets.applied_message(preset.label, obj.name),
        "preset": preset,
        "written": written,
    }


def apply_preset_in_scene(
    context: Context,
    preset_id: str,
    *,
    create_if_missing: bool = True,
) -> dict[str, Any]:
    """Apply to the active BEHOLD light, or add one when the inventory is empty."""
    light = light_lib.get_active_behold_light(context)
    if light is None:
        if not create_if_missing or light_lib.iter_behold_lights(context):
            return {"ok": False, "message": "NO_LIGHTS"}
        light = light_lib.add_extra_light(context)
    _, product_size = light_lib.product_frame(context)
    current = float(getattr(light.data, "size", 1.0) or 1.0)
    scale = presets.resolve_shape_scale(
        product_size=product_size,
        current_size=current,
    )
    result = apply_preset_to_object(light, preset_id, scale=scale)
    if result["ok"]:
        light_lib.set_active_behold_light(context, light)
        result["light"] = light
        result["scale"] = scale
    return result


def _apply_node_graph(data, graph: presets.NodeGraph) -> None:
    data.use_nodes = True
    tree = data.node_tree
    if tree is None:
        return
    created = _wire_plan(tree, graph.nodes, graph.links)
    mapping = created.get("mapping")
    if mapping is not None:
        _set_vector_input(mapping, "Location", graph.mapping.location)
        _set_vector_input(mapping, "Scale", graph.mapping.scale)
    gradient = created.get("gradient")
    if gradient is not None and hasattr(gradient, "gradient_type"):
        try:
            gradient.gradient_type = graph.gradient_type
        except (TypeError, ValueError):
            pass
    ramp_node = created.get("ramp")
    if ramp_node is not None:
        ramp = getattr(ramp_node, "color_ramp", None)
        if ramp is not None:
            _write_ramp(ramp, graph.ramp)
    emission = created.get("emission")
    if emission is not None:
        try:
            emission.inputs["Strength"].default_value = graph.emission_strength
        except (KeyError, TypeError):
            pass


def _set_vector_input(node: Node, name: str, value: tuple[float, float, float]) -> None:
    try:
        node.inputs[name].default_value = value
    except (KeyError, TypeError):
        pass


def _write_ramp(ramp, stops: tuple[presets.RampStop, ...]) -> None:
    elements = ramp.elements
    while len(elements) < len(stops):
        nxt = stops[len(elements)]
        elements.new(nxt.position)
    for index, stop in enumerate(stops):
        element = elements[index]
        element.position = stop.position
        element.color = stop.color


def _socket(node: Node, side: str, key: _SocketKey) -> NodeSocket:
    sockets = node.outputs if side == "output" else node.inputs
    return sockets[key]


def _wire_plan(
    tree: NodeTree,
    nodes: tuple[presets.NodeSpec, ...],
    links: tuple[presets.LinkSpec, ...],
) -> dict[str, Node]:
    tree.nodes.clear()
    created: dict[str, Node] = {}
    for spec in nodes:
        node = tree.nodes.new(spec.bl_idname)
        node.name = spec.name
        node.label = spec.name
        created[spec.key] = node
    for link in links:
        src = created[link.from_key]
        dst = created[link.to_key]
        tree.links.new(
            _socket(src, "output", link.from_socket),
            _socket(dst, "input", link.to_socket),
        )
    return created
