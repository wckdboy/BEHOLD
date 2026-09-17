# SPDX-License-Identifier: GPL-3.0-or-later
"""HDRI world graph spec and path checks — no Blender import."""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Literal

PathProblemKind = Literal["empty", "unsupported", "missing"]

HDRI_EXTENSIONS = frozenset(
    {".hdr", ".exr", ".hdri", ".jpg", ".jpeg", ".png", ".tif", ".tiff"}
)
HDRI_FILTER_GLOB = "*.hdr;*.exr;*.hdri;*.jpg;*.jpeg;*.png;*.tif;*.tiff"

DEFAULT_STRENGTH = 1.0
DEFAULT_ROTATION_DEG = 0.0
DEFAULT_BACKGROUND_STRENGTH = 0.0
SOLID_STRENGTH = 0.2
SOLID_COLOR = (0.02, 0.02, 0.025, 1.0)

WORLD_MODE_KEY = "behold_world_mode"
WORLD_MODE_HDRI = "hdri"
WORLD_MODE_SOLID = "solid"

NODE_TEX_COORD = "BEHOLD_TexCoord"
NODE_MAPPING = "BEHOLD_Mapping"
NODE_ENV = "BEHOLD_EnvTex"
NODE_BG = "BEHOLD_Background"
NODE_BG_CAMERA = "BEHOLD_BackgroundCamera"
NODE_LIGHT_PATH = "BEHOLD_LightPath"
NODE_MIX = "BEHOLD_MixShader"
NODE_OUTPUT = "BEHOLD_Output"

TYPE_TEX_COORD = "ShaderNodeTexCoord"
TYPE_MAPPING = "ShaderNodeMapping"
TYPE_ENV = "ShaderNodeTexEnvironment"
TYPE_BACKGROUND = "ShaderNodeBackground"
TYPE_LIGHT_PATH = "ShaderNodeLightPath"
TYPE_MIX = "ShaderNodeMixShader"
TYPE_OUTPUT = "ShaderNodeOutputWorld"


@dataclass(frozen=True)
class NodeSpec:
    key: str
    name: str
    bl_idname: str


@dataclass(frozen=True)
class LinkSpec:
    from_key: str
    from_socket: str | int
    to_key: str
    to_socket: str | int


def normalize_filepath(filepath: str) -> str:
    return (filepath or "").strip()


def hdri_extension(filepath: str) -> str:
    return os.path.splitext(normalize_filepath(filepath))[1].lower()


def is_hdri_extension(filepath: str) -> bool:
    return hdri_extension(filepath) in HDRI_EXTENSIONS


def is_blender_relative(filepath: str) -> bool:
    return normalize_filepath(filepath).startswith("//")


def existing_filepath(filepath: str) -> str | None:
    """Absolute path when the file exists. Does not expand Blender ``//`` paths."""
    path = os.path.expanduser(normalize_filepath(filepath))
    if not path or is_blender_relative(path):
        return None
    if os.path.isfile(path):
        return os.path.abspath(path)
    return None


@dataclass(frozen=True)
class PathProblem:
    kind: PathProblemKind
    detail: str = ""


def classify_hdri_filepath(
    filepath: str,
    *,
    resolved: str | None = None,
) -> PathProblem | None:
    """Return a path problem when the HDRI cannot be used, else None."""
    raw = normalize_filepath(filepath)
    if not raw:
        return PathProblem("empty")
    if not is_hdri_extension(raw):
        return PathProblem("unsupported", hdri_extension(raw) or raw)
    check = resolved if resolved is not None else existing_filepath(raw)
    if not check:
        return PathProblem("missing", os.path.basename(raw) or raw)
    if not os.path.isfile(check):
        return PathProblem("missing", os.path.basename(check) or check)
    return None


def degrees_to_radians(degrees: float) -> float:
    return math.radians(float(degrees))


def rotation_radians_z(degrees: float) -> tuple[float, float, float]:
    """Mapping-node Euler: rotate the environment around world Z."""
    return (0.0, 0.0, degrees_to_radians(degrees))


def hdri_nodes(*, reflections_only: bool) -> tuple[NodeSpec, ...]:
    nodes = (
        NodeSpec("tex_coord", NODE_TEX_COORD, TYPE_TEX_COORD),
        NodeSpec("mapping", NODE_MAPPING, TYPE_MAPPING),
        NodeSpec("env", NODE_ENV, TYPE_ENV),
        NodeSpec("bg", NODE_BG, TYPE_BACKGROUND),
        NodeSpec("output", NODE_OUTPUT, TYPE_OUTPUT),
    )
    if not reflections_only:
        return nodes
    extra = (
        NodeSpec("bg_camera", NODE_BG_CAMERA, TYPE_BACKGROUND),
        NodeSpec("light_path", NODE_LIGHT_PATH, TYPE_LIGHT_PATH),
        NodeSpec("mix", NODE_MIX, TYPE_MIX),
    )
    return nodes + extra


def hdri_links(*, reflections_only: bool) -> tuple[LinkSpec, ...]:
    base = (
        LinkSpec("tex_coord", "Generated", "mapping", "Vector"),
        LinkSpec("mapping", "Vector", "env", "Vector"),
        LinkSpec("env", "Color", "bg", "Color"),
    )
    if not reflections_only:
        return base + (LinkSpec("bg", "Background", "output", "Surface"),)
    # Mix Shader inputs: 0 Fac, 1 lighting, 2 camera (both sockets named Shader).
    return base + (
        LinkSpec("env", "Color", "bg_camera", "Color"),
        LinkSpec("light_path", "Is Camera Ray", "mix", 0),
        LinkSpec("bg", "Background", "mix", 1),
        LinkSpec("bg_camera", "Background", "mix", 2),
        LinkSpec("mix", "Shader", "output", "Surface"),
    )


def solid_world_nodes() -> tuple[NodeSpec, ...]:
    return (
        NodeSpec("bg", NODE_BG, TYPE_BACKGROUND),
        NodeSpec("output", NODE_OUTPUT, TYPE_OUTPUT),
    )


def solid_world_links() -> tuple[LinkSpec, ...]:
    return (LinkSpec("bg", "Background", "output", "Surface"),)
