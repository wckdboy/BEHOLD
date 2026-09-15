# SPDX-License-Identifier: GPL-3.0-or-later
"""IES practical lite — BYO photometric profile on a spot / point (no Blender).

Cycles only honors IES on point and spot lights. Area lights become spots
while a profile is on; Clear restores the prior type plus Shape / Gobo.
Not a streamed manufacturer catalog.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Literal, Never

PathProblemKind = Literal["empty", "unsupported", "missing"]

IES_EXTENSIONS = frozenset({".ies"})
IES_FILTER_GLOB = "*.ies"

DEFAULT_STRENGTH = 1.0
DEFAULT_SCALE = 1.0
MIN_STRENGTH = 0.0
MAX_STRENGTH = 16.0
MIN_SCALE = 0.1
MAX_SCALE = 8.0

NATIVE_TYPES = frozenset({"SPOT", "POINT"})
CONVERTIBLE_TYPES = frozenset({"AREA"})
REJECTED_TYPES = frozenset({"SUN"})

ACTIVE_KEY = "behold_ies_active"
FILE_KEY = "behold_ies_filepath"
PRIOR_TYPE_KEY = "behold_ies_prior_type"
PRIOR_SHAPE_KEY = "behold_ies_prior_shape"
PRIOR_SIZE_KEY = "behold_ies_prior_size"
PRIOR_SIZE_Y_KEY = "behold_ies_prior_size_y"
PRIOR_SPREAD_KEY = "behold_ies_prior_spread"
PRIOR_SOFT_KEY = "behold_ies_prior_shadow_soft_size"
PRIOR_SPOT_SIZE_KEY = "behold_ies_prior_spot_size"
PRIOR_SPOT_BLEND_KEY = "behold_ies_prior_spot_blend"

OWNED_PREFIX = "BEHOLD_IES"
NODE_GEOM = "BEHOLD_IESGeom"
NODE_MAP = "BEHOLD_IESMapping"
NODE_IES = "BEHOLD_IESTex"
NODE_EMISSION = "BEHOLD_IESEmission"
NODE_OUTPUT = "BEHOLD_IESOutput"

TYPE_GEOM = "ShaderNodeNewGeometry"
TYPE_MAP = "ShaderNodeMapping"
TYPE_IES = "ShaderNodeTexIES"
TYPE_EMISSION = "ShaderNodeEmission"
TYPE_OUTPUT = "ShaderNodeOutputLight"

IES_MODE_EXTERNAL = "EXTERNAL"
GEOM_INCOMING = "Incoming"

DEFAULT_SPOT_SIZE_DEG = 45.0
DEFAULT_SPOT_BLEND = 0.2
DEFAULT_SHADOW_SOFT_SIZE = 0.05

SAMPLE_FILENAME = "sample_spot.ies"
SAMPLE_RELPATH = os.path.join("ies", SAMPLE_FILENAME)

NO_IES_FILE = "No IES selected — pick a .ies from disk, or Sample"
NO_IES_TYPE = (
    "IES needs a spot or point light — this light is a sun. "
    "Add Light, then Load IES"
)
IES_NODES_FAILED = (
    "Could not build that IES graph — this Blender build is missing a light "
    "node. Try Clear, or update Blender"
)
IES_CLEARED = "IES off — the light is back to its prior Shape / Gobo"
IES_LOAD_FAILED = "Could not load that IES — pick another .ies and try Load"


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


@dataclass(frozen=True)
class NodeGraph:
    nodes: tuple[NodeSpec, ...]
    links: tuple[LinkSpec, ...]
    filepath: str
    strength: float
    scale: tuple[float, float, float]
    ies_mode: str = IES_MODE_EXTERNAL
    geom_socket: str = GEOM_INCOMING
    emission_color: tuple[float, float, float, float] = (1.0, 1.0, 1.0, 1.0)
    emission_strength: float = 1.0


@dataclass(frozen=True)
class PathProblem:
    kind: PathProblemKind
    detail: str = ""


@dataclass(frozen=True)
class TypePlan:
    """How to get a Cycles-legal IES host from the current light type."""

    action: Literal["keep", "convert", "reject"]
    target_type: str = ""
    prior_type: str = ""


def normalize_filepath(filepath: str) -> str:
    return (filepath or "").strip()


def ies_extension(filepath: str) -> str:
    return os.path.splitext(normalize_filepath(filepath))[1].lower()


def is_ies_extension(filepath: str) -> bool:
    return ies_extension(filepath) in IES_EXTENSIONS


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


def classify_ies_filepath(
    filepath: str,
    *,
    resolved: str | None = None,
) -> PathProblem | None:
    """Return a path problem when the IES cannot be used, else None."""
    raw = normalize_filepath(filepath)
    if not raw:
        return PathProblem("empty")
    if not is_ies_extension(raw):
        return PathProblem("unsupported", ies_extension(raw) or raw)
    check = resolved if resolved is not None else existing_filepath(raw)
    if not check:
        return PathProblem("missing", os.path.basename(raw) or raw)
    if not os.path.isfile(check):
        return PathProblem("missing", os.path.basename(check) or check)
    return None


def bundled_sample_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", SAMPLE_RELPATH))


def clamp_strength(value: float) -> float:
    return max(MIN_STRENGTH, min(MAX_STRENGTH, float(value)))


def clamp_scale(value: float) -> float:
    return max(MIN_SCALE, min(MAX_SCALE, float(value)))


def mapping_scale(scale: float) -> tuple[float, float, float]:
    amount = clamp_scale(scale)
    return (amount, amount, amount)


def default_spot_size_radians() -> float:
    return math.radians(DEFAULT_SPOT_SIZE_DEG)


def plan_light_type(light_type: str) -> TypePlan:
    current = (light_type or "").strip().upper()
    if current in NATIVE_TYPES:
        return TypePlan("keep", target_type=current, prior_type=current)
    if current in CONVERTIBLE_TYPES:
        return TypePlan("convert", target_type="SPOT", prior_type=current)
    if current in REJECTED_TYPES or current:
        return TypePlan("reject", prior_type=current)
    return TypePlan("reject", prior_type=current)


def owned_node_name(name: str) -> bool:
    return str(name or "").startswith(OWNED_PREFIX)


def node_graph_for(
    filepath: str,
    *,
    strength: float = DEFAULT_STRENGTH,
    scale: float = DEFAULT_SCALE,
) -> NodeGraph:
    amount = clamp_scale(scale)
    return NodeGraph(
        nodes=(
            NodeSpec("geom", NODE_GEOM, TYPE_GEOM),
            NodeSpec("mapping", NODE_MAP, TYPE_MAP),
            NodeSpec("ies", NODE_IES, TYPE_IES),
            NodeSpec("emission", NODE_EMISSION, TYPE_EMISSION),
            NodeSpec("output", NODE_OUTPUT, TYPE_OUTPUT),
        ),
        links=(
            LinkSpec("geom", GEOM_INCOMING, "mapping", "Vector"),
            LinkSpec("mapping", "Vector", "ies", "Vector"),
            LinkSpec("ies", "Fac", "emission", "Strength"),
            LinkSpec("emission", "Emission", "output", "Surface"),
        ),
        filepath=filepath,
        strength=clamp_strength(strength),
        scale=(amount, amount, amount),
    )


def applied_message(filepath: str, light_name: str) -> str:
    shown = light_name
    if shown.startswith("BEHOLD_"):
        shown = shown[len("BEHOLD_") :]
    name = os.path.basename(filepath) or filepath or "IES"
    return f"IES loaded: {name} on {shown}"


def cleared_message() -> str:
    return IES_CLEARED


def ies_file_not_found(filepath: str) -> str:
    name = os.path.basename(filepath) or filepath or "that IES"
    return f"IES file not found: {name} — choose an existing .ies"


def unsupported_ies_message(ext: str) -> str:
    shown = (ext or "").strip() or "this file"
    return f"Unsupported IES: {shown} — use a .ies photometric file"


def path_problem_message(problem: PathProblem) -> str:
    if problem.kind == "empty":
        return NO_IES_FILE
    if problem.kind == "unsupported":
        return unsupported_ies_message(problem.detail)
    if problem.kind == "missing":
        return ies_file_not_found(problem.detail)
    unreachable: Never = problem.kind
    raise RuntimeError(f"unhandled IES path problem: {unreachable}")
