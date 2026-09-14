# SPDX-License-Identifier: GPL-3.0-or-later
"""Build / tear down BEHOLD compositor look nodes on a scene."""

from __future__ import annotations

from typing import Any, Iterable

import bpy
from bpy.types import Context, Node, NodeSocket, NodeTree, Scene

from . import looks as looks_lib

_SocketKey = str | int

MIX_NODE_TYPES = (looks_lib.TYPE_MIX, "CompositorNodeMix")
GRAIN_NODE_TYPES = (looks_lib.TYPE_GRAIN, "CompositorNodeNoiseTexture")
GLARE_TYPES = (looks_lib.GLARE_FOG_GLOW, "BLOOM")

SOCKET_ALIASES: dict[str, tuple[_SocketKey, ...]] = {
    "Fac": ("Fac", "Factor", 0),
    "Color1": ("Color1", "A", "Image", 1),
    "Color2": ("Color2", "B", 2),
    "Image": ("Image", "Result", "Color", 0),
    "Mask": ("Mask", "Image", 0),
    "Color": ("Color", "Image", 0),
    "Value": ("Value", 0),
}

INFRA_TYPES = frozenset({looks_lib.TYPE_RLAYERS, looks_lib.TYPE_COMPOSITE})


def apply_look(context: Context) -> dict[str, Any]:
    """Enable the selected look, or tear the graph down when the toggle is off."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return {"ok": False, "message": looks_lib.NO_COMPOSITOR}
    settings = scene.behold
    if not bool(getattr(settings, "look_enabled", False)):
        return teardown_look(scene)
    preset_id = getattr(settings, "look_preset", looks_lib.DEFAULT_PRESET)
    return apply_look_preset(scene, str(preset_id or looks_lib.DEFAULT_PRESET))


def apply_look_preset(scene: Scene, preset_id: str) -> dict[str, Any]:
    preset = looks_lib.get_preset(preset_id)
    if preset is None:
        return {"ok": False, "message": looks_lib.unknown_look_message(preset_id)}
    graph = looks_lib.node_graph_for(preset.id)
    if graph is None:
        return {"ok": False, "message": looks_lib.unknown_look_message(preset_id)}

    tree = ensure_compositor(scene)
    if tree is None:
        return {"ok": False, "message": looks_lib.NO_COMPOSITOR}
    if tree_has_foreign_nodes(tree):
        return {"ok": False, "message": looks_lib.LOOK_COMPOSITOR_BUSY}

    tree.nodes.clear()
    created = _wire_plan(tree, graph)
    if created is None:
        tree.nodes.clear()
        return {"ok": False, "message": looks_lib.LOOK_NODES_FAILED}
    _write_values(created, graph)
    _mark_owned(scene, True)
    _set_compositing(scene, True)
    return {
        "ok": True,
        "message": looks_lib.applied_message(preset),
        "preset": preset,
        "graph": graph,
    }


def teardown_look(scene: Scene) -> dict[str, Any]:
    tree = compositor_tree(scene)
    if tree is None:
        _set_compositing(scene, False)
        _mark_owned(scene, False)
        return {"ok": True, "message": looks_lib.disabled_message()}
    if tree_has_foreign_nodes(tree):
        clear_owned_nodes(tree)
        _mark_owned(scene, False)
        return {"ok": True, "message": looks_lib.disabled_message()}
    tree.nodes.clear()
    _set_compositing(scene, False)
    if hasattr(scene, "use_nodes"):
        scene.use_nodes = False
    _mark_owned(scene, False)
    return {"ok": True, "message": looks_lib.disabled_message()}


def on_look_update(settings, context: Context) -> None:
    """RNA update: preset or Compositor toggle rebuilds the look graph."""
    del settings
    if context is None or getattr(context, "scene", None) is None:
        return
    apply_look(context)


def compositor_tree(scene: Scene) -> NodeTree | None:
    tree = getattr(scene, "node_tree", None)
    if tree is not None:
        return tree
    group = getattr(scene, "compositing_node_group", None)
    if group is not None:
        return group
    return None


def ensure_compositor(scene: Scene) -> NodeTree | None:
    if hasattr(scene, "use_nodes"):
        scene.use_nodes = True
    tree = compositor_tree(scene)
    if tree is not None:
        _set_compositing(scene, True)
        return tree
    groups = getattr(bpy.data, "node_groups", None)
    if groups is not None and hasattr(scene, "compositing_node_group"):
        try:
            group = groups.new("BEHOLD_LookTree", "CompositorNodeTree")
            scene.compositing_node_group = group
        except (TypeError, ValueError, AttributeError):
            return compositor_tree(scene)
        _set_compositing(scene, True)
        return compositor_tree(scene)
    return compositor_tree(scene)


def tree_has_foreign_nodes(tree: NodeTree) -> bool:
    for node in tree.nodes:
        if looks_lib.owned_node_name(node.name):
            continue
        bl_idname = getattr(node, "bl_idname", "") or ""
        if bl_idname in INFRA_TYPES:
            continue
        return True
    return False


def clear_owned_nodes(tree: NodeTree) -> list[str]:
    removed: list[str] = []
    for node in list(tree.nodes):
        if looks_lib.owned_node_name(node.name):
            removed.append(node.name)
            tree.nodes.remove(node)
    return removed


def _set_compositing(scene: Scene, enabled: bool) -> None:
    render = getattr(scene, "render", None)
    if render is None:
        return
    if hasattr(render, "use_compositing"):
        render.use_compositing = enabled


def _mark_owned(scene: Scene, owned: bool) -> None:
    try:
        scene[looks_lib.TREE_OWNED_KEY] = bool(owned)
    except (TypeError, AttributeError):
        pass


def _new_node(tree: NodeTree, types: Iterable[str], name: str) -> Node | None:
    last_error: Exception | None = None
    for bl_idname in types:
        try:
            node = tree.nodes.new(bl_idname)
        except (RuntimeError, TypeError, ValueError) as exc:
            last_error = exc
            continue
        node.name = name
        node.label = name
        del last_error
        return node
    return None


def _type_for_spec(spec: looks_lib.NodeSpec) -> tuple[str, ...]:
    if spec.bl_idname == looks_lib.TYPE_MIX:
        return MIX_NODE_TYPES
    if spec.bl_idname == looks_lib.TYPE_GRAIN:
        return GRAIN_NODE_TYPES
    return (spec.bl_idname,)


def _wire_plan(tree: NodeTree, graph: looks_lib.NodeGraph) -> dict[str, Node] | None:
    created: dict[str, Node] = {}
    for spec in graph.nodes:
        node = _new_node(tree, _type_for_spec(spec), spec.name)
        if node is None:
            return None
        created[spec.key] = node
    for link in graph.links:
        src = created.get(link.from_key)
        dst = created.get(link.to_key)
        if src is None or dst is None:
            return None
        out_sock = _socket(src, "output", link.from_socket)
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


def _set_input_default(node: Node | None, names: tuple[str, ...], value: float) -> None:
    if node is None:
        return
    for name in names:
        sock = _socket(node, "input", name)
        if sock is None:
            continue
        try:
            sock.default_value = value
            return
        except (TypeError, ValueError, AttributeError):
            continue


def _set_blend(node: Node | None, blend: str) -> None:
    if node is None or not hasattr(node, "blend_type"):
        return
    try:
        node.blend_type = blend
    except (TypeError, ValueError):
        pass
    if hasattr(node, "data_type"):
        try:
            node.data_type = "RGBA"
        except (TypeError, ValueError):
            pass


def _write_values(created: dict[str, Node], graph: looks_lib.NodeGraph) -> None:
    contrast = created.get("contrast")
    _set_input_default(contrast, ("Contrast",), graph.contrast)
    _set_input_default(contrast, ("Bright", "Brightness"), 0.0)

    mask = created.get("vignette_mask")
    if mask is not None:
        for attr, value in (
            ("width", graph.vignette_width),
            ("height", graph.vignette_height),
            ("x", 0.5),
            ("y", 0.5),
        ):
            if hasattr(mask, attr):
                try:
                    setattr(mask, attr, value)
                except (TypeError, ValueError):
                    pass

    blur = created.get("vignette_blur")
    if blur is not None:
        if hasattr(blur, "use_relative"):
            try:
                blur.use_relative = True
            except (TypeError, ValueError):
                pass
        if hasattr(blur, "factor_x"):
            try:
                blur.factor_x = graph.vignette_blur
                blur.factor_y = graph.vignette_blur
            except (TypeError, ValueError, AttributeError):
                pass
        if hasattr(blur, "size_x"):
            try:
                blur.size_x = graph.vignette_blur
                blur.size_y = graph.vignette_blur
            except (TypeError, ValueError, AttributeError):
                pass

    amount = created.get("vignette_amount")
    if amount is not None:
        if hasattr(amount, "operation"):
            try:
                amount.operation = graph.math_operation
            except (TypeError, ValueError):
                pass
        _set_input_default(amount, ("Value",), graph.vignette)
        try:
            amount.inputs[1].default_value = graph.vignette
        except (KeyError, IndexError, TypeError, AttributeError):
            pass

    color = created.get("vignette_color")
    if color is not None and hasattr(color, "outputs"):
        try:
            color.outputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
        except (KeyError, IndexError, TypeError, AttributeError):
            pass

    _set_blend(created.get("vignette_mix"), graph.vignette_blend)
    _set_blend(created.get("grain_mix"), graph.grain_blend)
    _set_input_default(created.get("grain_mix"), ("Fac", "Factor"), graph.grain)

    grain = created.get("grain")
    if grain is not None:
        _attach_grain_texture(grain)

    glare = created.get("glare")
    if glare is not None:
        if hasattr(glare, "glare_type"):
            for glare_type in GLARE_TYPES:
                try:
                    glare.glare_type = glare_type
                    break
                except (TypeError, ValueError):
                    continue
        for attr, value in (
            ("mix", graph.glare_mix),
            ("threshold", graph.glare_threshold),
            ("size", graph.glare_size),
        ):
            if hasattr(glare, attr):
                try:
                    setattr(glare, attr, value)
                except (TypeError, ValueError):
                    pass
        if hasattr(glare, "quality"):
            try:
                glare.quality = "MEDIUM"
            except (TypeError, ValueError):
                pass


def _attach_grain_texture(node: Node) -> None:
    if not hasattr(node, "texture"):
        return
    textures = getattr(bpy.data, "textures", None)
    if textures is None:
        return
    tex = textures.get(looks_lib.GRAIN_TEXTURE_NAME)
    if tex is None:
        try:
            tex = textures.new(looks_lib.GRAIN_TEXTURE_NAME, type="NOISE")
        except (TypeError, ValueError, RuntimeError):
            return
    try:
        node.texture = tex
    except (TypeError, AttributeError):
        pass
