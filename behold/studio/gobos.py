# SPDX-License-Identifier: GPL-3.0-or-later
"""Procedural gobo / cookie lite — blinds, soft window, circle (no Blender).

Light Wrangler streams a gobo texture library onto area/spot lights. This cut
is three procedural patterns as nodes on the active BEHOLD light — IES
practical lite is 1.2.0 (BYO .ies). None tears the graph down and restores
the 0.16.0 shape falloff when that light still has a shape preset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Never

GoboId = Literal["NONE", "BLINDS", "WINDOW", "CIRCLE"]
PatternId = Literal["NONE", "WAVE", "BRICK", "SPHERE"]

DEFAULT_PRESET: GoboId = "NONE"
DEFAULT_SCALE = 1.0
DEFAULT_STRENGTH = 1.0
MIN_SCALE = 0.1
MAX_SCALE = 8.0
MIN_STRENGTH = 0.0
MAX_STRENGTH = 1.0

PRESET_ID_KEY = "behold_gobo_preset"
OWNED_PREFIX = "BEHOLD_Gobo"
SUPPORTED_TYPES = frozenset({"AREA", "SPOT"})

NODE_TEX = "BEHOLD_GoboTexCoord"
NODE_MAP = "BEHOLD_GoboMapping"
NODE_WAVE = "BEHOLD_GoboWave"
NODE_BRICK = "BEHOLD_GoboBrick"
NODE_GRAD = "BEHOLD_GoboGradient"
NODE_RAMP = "BEHOLD_GoboRamp"
NODE_MIX = "BEHOLD_GoboMix"
NODE_EMISSION = "BEHOLD_GoboEmission"
NODE_OUTPUT = "BEHOLD_GoboOutput"

TYPE_TEX = "ShaderNodeTexCoord"
TYPE_MAP = "ShaderNodeMapping"
TYPE_WAVE = "ShaderNodeTexWave"
TYPE_BRICK = "ShaderNodeTexBrick"
TYPE_GRAD = "ShaderNodeTexGradient"
TYPE_RAMP = "ShaderNodeValToRGB"
TYPE_MIX = "ShaderNodeMixRGB"
TYPE_EMISSION = "ShaderNodeEmission"
TYPE_OUTPUT = "ShaderNodeOutputLight"

WAVE_BANDS = "BANDS"
WAVE_DIR_Y = "Y"
WAVE_SAW = "SAW"
GRADIENT_SPHERE = "QUADRATIC_SPHERE"
MIX_BLEND_MIX = "MIX"
TEXCOORD_UV = "UV"

CENTER_MAPPING_LOCATION = (-0.5, -0.5, -0.5)
IDENTITY_MAPPING_LOCATION = (0.0, 0.0, 0.0)

WHITE = (1.0, 1.0, 1.0, 1.0)
BLACK = (0.0, 0.0, 0.0, 1.0)

NO_GOBO_TYPE = (
    "Gobos need an area or spot light — Apply a Softbox, or Add Light"
)
GOBO_NODES_FAILED = (
    "Could not build that gobo — this Blender build is missing a light node. "
    "Try None, or update Blender"
)
UNKNOWN_GOBO = "Unknown gobo — pick None, Blinds, Window, or Circle"
GOBO_CLEARED = "Gobo off — the light is uniform again"


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
class RampStop:
    position: float
    color: tuple[float, float, float, float]


@dataclass(frozen=True)
class MappingValues:
    location: tuple[float, float, float]
    scale: tuple[float, float, float]


@dataclass(frozen=True)
class GoboPreset:
    id: GoboId
    label: str
    description: str
    pattern: PatternId


@dataclass(frozen=True)
class NodeGraph:
    nodes: tuple[NodeSpec, ...]
    links: tuple[LinkSpec, ...]
    mapping: MappingValues
    ramp: tuple[RampStop, ...]
    pattern: PatternId
    mix_fac: float
    mix_open: tuple[float, float, float, float] = WHITE
    mix_blend: str = MIX_BLEND_MIX
    texcoord_socket: str = TEXCOORD_UV
    wave_type: str = WAVE_BANDS
    bands_direction: str = WAVE_DIR_Y
    wave_profile: str = WAVE_SAW
    gradient_type: str = GRADIENT_SPHERE
    brick_offset: float = 0.0
    brick_mortar: float = 0.08
    brick_mortar_smooth: float = 0.18
    emission_strength: float = 1.0


PRESETS: dict[str, GoboPreset] = {
    "NONE": GoboPreset(
        id="NONE",
        label="None",
        description="No gobo — uniform emission, or the Shape falloff if one is applied",
        pattern="NONE",
    ),
    "BLINDS": GoboPreset(
        id="BLINDS",
        label="Blinds",
        description="Horizontal window-blind bands on the light",
        pattern="WAVE",
    ),
    "WINDOW": GoboPreset(
        id="WINDOW",
        label="Window",
        description="Soft window panes (brick muntins, feathered mortar)",
        pattern="BRICK",
    ),
    "CIRCLE": GoboPreset(
        id="CIRCLE",
        label="Circle",
        description="Circular cookie — bright disc, dark surround",
        pattern="SPHERE",
    ),
}

# Sharp slats: dark → open.
BLINDS_RAMP = (
    RampStop(0.0, BLACK),
    RampStop(0.42, BLACK),
    RampStop(0.52, WHITE),
    RampStop(1.0, WHITE),
)

# Soft window: panes stay open (brick Fac 0), mortar/muntins stay darker (Fac 1).
WINDOW_RAMP = (
    RampStop(0.0, WHITE),
    RampStop(0.45, (0.88, 0.88, 0.88, 1.0)),
    RampStop(0.78, (0.18, 0.18, 0.18, 1.0)),
    RampStop(1.0, (0.04, 0.04, 0.04, 1.0)),
)

# Circle cookie: center open, rim closed.
CIRCLE_RAMP = (
    RampStop(0.0, WHITE),
    RampStop(0.48, WHITE),
    RampStop(0.78, (0.22, 0.22, 0.22, 1.0)),
    RampStop(1.0, BLACK),
)


def preset_enum_items() -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (preset.id, preset.label, preset.description) for preset in PRESETS.values()
    )


def is_gobo(value: str) -> bool:
    return value in PRESETS


def get_preset(preset_id: str) -> GoboPreset | None:
    return PRESETS.get((preset_id or "").strip())


def clamp_scale(value: float) -> float:
    return max(MIN_SCALE, min(MAX_SCALE, float(value)))


def clamp_strength(value: float) -> float:
    return max(MIN_STRENGTH, min(MAX_STRENGTH, float(value)))


def owned_node_name(name: str) -> bool:
    return str(name or "").startswith(OWNED_PREFIX)


def mapping_for(pattern: PatternId, scale: float) -> MappingValues:
    amount = clamp_scale(scale)
    if pattern == "NONE":
        return MappingValues(IDENTITY_MAPPING_LOCATION, (1.0, 1.0, 1.0))
    if pattern == "WAVE":
        return MappingValues(IDENTITY_MAPPING_LOCATION, (1.0, 6.0 * amount, 1.0))
    if pattern == "BRICK":
        return MappingValues(IDENTITY_MAPPING_LOCATION, (2.0 * amount, 3.0 * amount, 1.0))
    if pattern == "SPHERE":
        span = 2.0 * amount
        return MappingValues(CENTER_MAPPING_LOCATION, (span, span, span))
    unreachable: Never = pattern
    raise RuntimeError(f"unhandled gobo pattern: {unreachable}")


def _common_tail() -> tuple[tuple[NodeSpec, ...], tuple[LinkSpec, ...]]:
    nodes = (
        NodeSpec("ramp", NODE_RAMP, TYPE_RAMP),
        NodeSpec("mix", NODE_MIX, TYPE_MIX),
        NodeSpec("emission", NODE_EMISSION, TYPE_EMISSION),
        NodeSpec("output", NODE_OUTPUT, TYPE_OUTPUT),
    )
    links = (
        LinkSpec("ramp", "Color", "mix", "Color2"),
        LinkSpec("mix", "Color", "emission", "Color"),
        LinkSpec("emission", "Emission", "output", "Surface"),
    )
    return nodes, links


def _head_nodes(pattern: PatternId) -> tuple[NodeSpec, ...]:
    head = (
        NodeSpec("tex_coord", NODE_TEX, TYPE_TEX),
        NodeSpec("mapping", NODE_MAP, TYPE_MAP),
    )
    if pattern == "WAVE":
        return head + (NodeSpec("wave", NODE_WAVE, TYPE_WAVE),)
    if pattern == "BRICK":
        return head + (NodeSpec("brick", NODE_BRICK, TYPE_BRICK),)
    if pattern == "SPHERE":
        return head + (NodeSpec("gradient", NODE_GRAD, TYPE_GRAD),)
    if pattern == "NONE":
        return ()
    unreachable: Never = pattern
    raise RuntimeError(f"unhandled gobo pattern: {unreachable}")


def _head_links(pattern: PatternId) -> tuple[LinkSpec, ...]:
    base = (
        LinkSpec("tex_coord", TEXCOORD_UV, "mapping", "Vector"),
    )
    if pattern == "WAVE":
        return base + (
            LinkSpec("mapping", "Vector", "wave", "Vector"),
            LinkSpec("wave", "Fac", "ramp", "Fac"),
        )
    if pattern == "BRICK":
        return base + (
            LinkSpec("mapping", "Vector", "brick", "Vector"),
            LinkSpec("brick", "Fac", "ramp", "Fac"),
        )
    if pattern == "SPHERE":
        return base + (
            LinkSpec("mapping", "Vector", "gradient", "Vector"),
            LinkSpec("gradient", "Fac", "ramp", "Fac"),
        )
    if pattern == "NONE":
        return ()
    unreachable: Never = pattern
    raise RuntimeError(f"unhandled gobo pattern: {unreachable}")


def node_graph_for(
    preset_id: str,
    *,
    scale: float = DEFAULT_SCALE,
    strength: float = DEFAULT_STRENGTH,
) -> NodeGraph | None:
    """Procedural gobo graph, or None for a uniform / restored shape light."""
    preset = get_preset(preset_id)
    if preset is None or preset.pattern == "NONE":
        return None
    pattern = preset.pattern
    head = _head_nodes(pattern)
    tail, tail_links = _common_tail()
    links = _head_links(pattern) + tail_links
    mix_fac = clamp_strength(strength)
    if pattern == "WAVE":
        return NodeGraph(
            nodes=head + tail,
            links=links,
            mapping=mapping_for(pattern, scale),
            ramp=BLINDS_RAMP,
            pattern=pattern,
            mix_fac=mix_fac,
        )
    if pattern == "BRICK":
        return NodeGraph(
            nodes=head + tail,
            links=links,
            mapping=mapping_for(pattern, scale),
            ramp=WINDOW_RAMP,
            pattern=pattern,
            mix_fac=mix_fac,
            brick_offset=0.0,
            brick_mortar=0.08,
            brick_mortar_smooth=0.18,
        )
    if pattern == "SPHERE":
        return NodeGraph(
            nodes=head + tail,
            links=links,
            mapping=mapping_for(pattern, scale),
            ramp=CIRCLE_RAMP,
            pattern=pattern,
            mix_fac=mix_fac,
            gradient_type=GRADIENT_SPHERE,
        )
    unreachable: Never = pattern
    raise RuntimeError(f"unhandled gobo pattern: {unreachable}")


def applied_message(label: str, light_name: str) -> str:
    shown = light_name
    if shown.startswith("BEHOLD_"):
        shown = shown[len("BEHOLD_") :]
    return f"Applied {label} gobo to {shown}"


def cleared_message() -> str:
    return GOBO_CLEARED


def unknown_gobo_message(preset_id: str) -> str:
    shown = (preset_id or "").strip()
    if not shown:
        return UNKNOWN_GOBO
    return f"Unknown gobo “{shown}” — pick None, Blinds, Window, or Circle"
