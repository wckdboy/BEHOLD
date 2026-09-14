# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply / reset the BEHOLD world shader (Blender nodes)."""

from __future__ import annotations

import os
from typing import Any, Never

import bpy
from bpy.types import Context, Node, NodeSocket, NodeTree, Scene

from ..ui.messages import (
    HDRI_LOAD_FAILED,
    NO_HDRI_FILE,
    NO_WORLD,
    WORLD_RESET,
    hdri_file_not_found,
    hdri_loaded_message,
    unsupported_hdri_message,
)
from . import world as world_lib
from .tones import backdrop_tone_rgba

_SocketKey = str | int


def resolve_filepath(filepath: str) -> str:
    raw = world_lib.normalize_filepath(filepath)
    if not raw:
        return ""
    try:
        expanded = bpy.path.abspath(raw)
    except Exception:  # noqa: BLE001 — keep raw path when Blender cannot expand
        expanded = os.path.expanduser(raw)
    else:
        expanded = os.path.expanduser(expanded)
    return os.path.abspath(expanded) if expanded else ""


def ensure_world(scene: Scene):
    world = scene.world
    if world is None:
        world = bpy.data.worlds.new("BEHOLD_World")
        scene.world = world
    world.use_nodes = True
    if world.node_tree is None:
        return None
    return world


def setup_solid_world(
    scene: Scene,
    color: tuple[float, float, float, float] = world_lib.SOLID_COLOR,
    strength: float = world_lib.SOLID_STRENGTH,
) -> None:
    world = ensure_world(scene)
    if world is None:
        return
    tree = world.node_tree
    created = _wire_plan(tree, world_lib.solid_world_nodes(), world_lib.solid_world_links())
    bg = created["bg"]
    bg.inputs["Color"].default_value = color
    bg.inputs["Strength"].default_value = strength
    world[world_lib.WORLD_MODE_KEY] = world_lib.WORLD_MODE_SOLID


def apply_hdri(
    scene: Scene,
    *,
    filepath: str,
    strength: float,
    rotation_deg: float,
    reflections_only: bool,
    background_strength: float,
) -> dict[str, Any]:
    resolved = resolve_filepath(filepath)
    problem = world_lib.classify_hdri_filepath(filepath, resolved=resolved or None)
    if problem is not None:
        return {"ok": False, "message": path_problem_message(problem)}

    world = ensure_world(scene)
    if world is None:
        return {"ok": False, "message": NO_WORLD}

    try:
        image = bpy.data.images.load(resolved, check_existing=True)
    except Exception as exc:  # noqa: BLE001 — surface Blender's load error
        return {"ok": False, "message": f"{HDRI_LOAD_FAILED}: {exc}"}

    tree = world.node_tree
    created = _wire_plan(
        tree,
        world_lib.hdri_nodes(reflections_only=reflections_only),
        world_lib.hdri_links(reflections_only=reflections_only),
    )
    env = created["env"]
    env.image = image
    _write_hdri_values(
        created,
        strength=strength,
        rotation_deg=rotation_deg,
        reflections_only=reflections_only,
        background_strength=background_strength,
    )
    world[world_lib.WORLD_MODE_KEY] = world_lib.WORLD_MODE_HDRI
    return {"ok": True, "message": hdri_loaded_message(resolved)}


def apply_hdri_from_settings(context: Context) -> dict[str, Any]:
    settings = context.scene.behold
    return apply_hdri(
        context.scene,
        filepath=getattr(settings, "hdri_filepath", "") or "",
        strength=float(getattr(settings, "hdri_strength", world_lib.DEFAULT_STRENGTH)),
        rotation_deg=float(
            getattr(settings, "hdri_rotation", world_lib.DEFAULT_ROTATION_DEG)
        ),
        reflections_only=bool(getattr(settings, "hdri_reflections_only", False)),
        background_strength=float(
            getattr(
                settings,
                "hdri_background_strength",
                world_lib.DEFAULT_BACKGROUND_STRENGTH,
            )
        ),
    )


def sync_hdri_values(context: Context) -> None:
    """Push strength / rotation / mix without reloading the image."""
    settings = context.scene.behold
    world = context.scene.world
    if world is None or not world.use_nodes or world.node_tree is None:
        return
    nodes = world.node_tree.nodes
    env = nodes.get(world_lib.NODE_ENV)
    if env is None or getattr(env, "image", None) is None:
        return
    reflections_only = bool(getattr(settings, "hdri_reflections_only", False))
    has_mix = nodes.get(world_lib.NODE_MIX) is not None
    if reflections_only != has_mix:
        apply_hdri_from_settings(context)
        return
    created = {
        "env": env,
        "mapping": nodes.get(world_lib.NODE_MAPPING),
        "bg": nodes.get(world_lib.NODE_BG),
        "bg_camera": nodes.get(world_lib.NODE_BG_CAMERA),
    }
    _write_hdri_values(
        created,
        strength=float(getattr(settings, "hdri_strength", world_lib.DEFAULT_STRENGTH)),
        rotation_deg=float(
            getattr(settings, "hdri_rotation", world_lib.DEFAULT_ROTATION_DEG)
        ),
        reflections_only=reflections_only,
        background_strength=float(
            getattr(
                settings,
                "hdri_background_strength",
                world_lib.DEFAULT_BACKGROUND_STRENGTH,
            )
        ),
    )


def reapply_hdri_if_loaded(context: Context) -> None:
    """Keep a loaded HDRI after Build Studio overwrites the world."""
    settings = context.scene.behold
    filepath = getattr(settings, "hdri_filepath", "") or ""
    if not world_lib.normalize_filepath(filepath):
        return
    result = apply_hdri_from_settings(context)
    if not result["ok"]:
        setup_solid_world(context.scene)


def reset_world(context: Context) -> dict[str, Any]:
    settings = context.scene.behold
    settings.hdri_filepath = ""
    world = ensure_world(context.scene)
    if world is None:
        return {"ok": False, "message": NO_WORLD}
    tone = backdrop_tone_rgba(settings)
    if getattr(settings, "studio_backdrop", "CYCLORAMA") == "SOLID":
        setup_solid_world(context.scene, color=tone, strength=0.35)
    else:
        setup_solid_world(context.scene)
    return {"ok": True, "message": WORLD_RESET}


def path_problem_message(problem: world_lib.PathProblem) -> str:
    if problem.kind == "empty":
        return NO_HDRI_FILE
    if problem.kind == "unsupported":
        return unsupported_hdri_message(problem.detail)
    if problem.kind == "missing":
        return hdri_file_not_found(problem.detail)
    unreachable: Never = problem.kind
    raise RuntimeError(f"unhandled HDRI path problem: {unreachable}")


def on_hdri_filepath_update(settings, context: Context) -> None:
    if not world_lib.normalize_filepath(getattr(settings, "hdri_filepath", "") or ""):
        return
    apply_hdri_from_settings(context)


def on_hdri_values_update(settings, context: Context) -> None:
    del settings
    sync_hdri_values(context)


def _socket(node: Node, side: str, key: _SocketKey) -> NodeSocket:
    sockets = node.outputs if side == "output" else node.inputs
    return sockets[key]


def _wire_plan(
    tree: NodeTree,
    nodes: tuple[world_lib.NodeSpec, ...],
    links: tuple[world_lib.LinkSpec, ...],
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


def _write_hdri_values(
    created: dict[str, Node | None],
    *,
    strength: float,
    rotation_deg: float,
    reflections_only: bool,
    background_strength: float,
) -> None:
    mapping = created.get("mapping")
    if mapping is not None:
        mapping.inputs["Rotation"].default_value = world_lib.rotation_radians_z(
            rotation_deg
        )
    bg = created.get("bg")
    if bg is not None:
        bg.inputs["Strength"].default_value = strength
    if reflections_only:
        camera_bg = created.get("bg_camera")
        if camera_bg is not None:
            camera_bg.inputs["Strength"].default_value = background_strength
