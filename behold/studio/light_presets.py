# SPDX-License-Identifier: GPL-3.0-or-later
"""Area-light shape presets + procedural softbox graph — no Blender import.

Maps Softbox / Strip / Octa / Hard / Rim onto Cycles area-light RNA that
exists on 4.2+ and 5.2 LTS: ``shape``, ``size``, ``size_y``, ``energy``,
``spread`` (radians). Optional emission falloff is a tiny node graph, not
a bundled image, so the zip stays small. Procedural gobos are 1.1.0; IES
is still out of scope.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Literal, Never

ShapeId = Literal["SQUARE", "RECTANGLE", "DISK", "ELLIPSE"]
NodeLook = Literal["NONE", "SOFTBOX", "STRIP", "OCTA"]

DEFAULT_PRESET = "SOFTBOX"
MIN_SIZE = 0.05
MIN_ENERGY = 0.01
PRESET_ID_KEY = "behold_shape_preset"

NODE_TEX = "BEHOLD_LightTexCoord"
NODE_MAP = "BEHOLD_LightMapping"
NODE_GRAD = "BEHOLD_LightGradient"
NODE_RAMP = "BEHOLD_LightRamp"
NODE_EMISSION = "BEHOLD_LightEmission"
NODE_OUTPUT = "BEHOLD_LightOutput"

TYPE_TEX = "ShaderNodeTexCoord"
TYPE_MAP = "ShaderNodeMapping"
TYPE_GRAD = "ShaderNodeTexGradient"
TYPE_RAMP = "ShaderNodeValToRGB"
TYPE_EMISSION = "ShaderNodeEmission"
TYPE_OUTPUT = "ShaderNodeOutputLight"

GRADIENT_SPHERE = "QUADRATIC_SPHERE"
GRADIENT_LINEAR = "LINEAR"

# Generated 0–1 → centered -1..1 so Quadratic Sphere falls off from the middle.
CENTER_MAPPING_LOCATION = (-0.5, -0.5, -0.5)
CENTER_MAPPING_SCALE = (2.0, 2.0, 2.0)
IDENTITY_MAPPING_LOCATION = (0.0, 0.0, 0.0)
IDENTITY_MAPPING_SCALE = (1.0, 1.0, 1.0)


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
class NodeGraph:
    nodes: tuple[NodeSpec, ...]
    links: tuple[LinkSpec, ...]
    gradient_type: str
    mapping: MappingValues
    ramp: tuple[RampStop, ...]
    emission_strength: float = 1.0


@dataclass(frozen=True)
class LightPreset:
    id: str
    label: str
    description: str
    shape: ShapeId
    size: float
    size_y: float
    energy: float
    spread_deg: float
    nodes: NodeLook


# Soft fabric: white field, darker rim (the “box”).
SOFTBOX_RAMP = (
    RampStop(0.0, (1.0, 1.0, 1.0, 1.0)),
    RampStop(0.58, (1.0, 1.0, 1.0, 1.0)),
    RampStop(0.84, (0.32, 0.32, 0.32, 1.0)),
    RampStop(1.0, (0.02, 0.02, 0.02, 1.0)),
)

# Strip: even along the long axis, dark on the short edges (linear X).
STRIP_RAMP = (
    RampStop(0.0, (0.04, 0.04, 0.04, 1.0)),
    RampStop(0.12, (1.0, 1.0, 1.0, 1.0)),
    RampStop(0.88, (1.0, 1.0, 1.0, 1.0)),
    RampStop(1.0, (0.04, 0.04, 0.04, 1.0)),
)

# Octa: center-bright disk, no hard frame.
OCTA_RAMP = (
    RampStop(0.0, (1.0, 1.0, 1.0, 1.0)),
    RampStop(0.62, (0.92, 0.92, 0.92, 1.0)),
    RampStop(1.0, (0.0, 0.0, 0.0, 1.0)),
)

# Relative to product/rig scale (same units as Build Studio key size).
PRESETS: dict[str, LightPreset] = {
    "SOFTBOX": LightPreset(
        id="SOFTBOX",
        label="Softbox",
        description="Large rectangle, full spread, fabric falloff",
        shape="RECTANGLE",
        size=1.6,
        size_y=1.2,
        energy=250.0,
        spread_deg=180.0,
        nodes="SOFTBOX",
    ),
    "SOFTBOX_STRIP": LightPreset(
        id="SOFTBOX_STRIP",
        label="Strip",
        description="Tall narrow softbox for edge / hair lights",
        shape="RECTANGLE",
        size=0.32,
        size_y=1.8,
        energy=180.0,
        spread_deg=180.0,
        nodes="STRIP",
    ),
    "OCTA": LightPreset(
        id="OCTA",
        label="Octa",
        description="Round disk area (octabox-ish), soft radial falloff",
        shape="DISK",
        size=1.5,
        size_y=1.5,
        energy=220.0,
        spread_deg=180.0,
        nodes="OCTA",
    ),
    "HARD_KEY": LightPreset(
        id="HARD_KEY",
        label="Hard",
        description="Small square, tight spread, hard specular",
        shape="SQUARE",
        size=0.22,
        size_y=0.22,
        energy=400.0,
        spread_deg=35.0,
        nodes="NONE",
    ),
    "RIM_EDGE": LightPreset(
        id="RIM_EDGE",
        label="Rim",
        description="Thin rectangle, moderate spread, rim / edge",
        shape="RECTANGLE",
        size=0.12,
        size_y=1.4,
        energy=160.0,
        spread_deg=70.0,
        nodes="STRIP",
    ),
}


def preset_enum_items() -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (preset.id, preset.label, preset.description) for preset in PRESETS.values()
    )


def get_preset(preset_id: str) -> LightPreset | None:
    return PRESETS.get((preset_id or "").strip())


def spread_radians(degrees: float) -> float:
    return math.radians(float(degrees))


def uses_size_y(shape: ShapeId) -> bool:
    if shape in ("RECTANGLE", "ELLIPSE"):
        return True
    if shape in ("SQUARE", "DISK"):
        return False
    unreachable: Never = shape
    raise RuntimeError(f"unhandled area shape: {unreachable}")


def resolve_shape_scale(*, product_size: float, current_size: float) -> float:
    """Product AABB when present; otherwise keep the light’s current size scale."""
    if product_size >= 0.1:
        return float(product_size)
    return max(float(current_size), MIN_SIZE)


def scaled_size(preset: LightPreset, scale: float) -> tuple[float, float]:
    size = max(preset.size * scale, MIN_SIZE)
    size_y = max(preset.size_y * scale, MIN_SIZE)
    return size, size_y


def scaled_energy(preset: LightPreset, scale: float) -> float:
    return max(preset.energy * scale, MIN_ENERGY)


def apply_shape_props(
    data: Any,
    preset: LightPreset,
    *,
    scale: float,
) -> dict[str, Any]:
    """Write shape / size / energy / spread onto a Light datablock (or a fake)."""
    written: dict[str, Any] = {}
    if hasattr(data, "type"):
        data.type = "AREA"
        written["type"] = "AREA"
    data.shape = preset.shape
    written["shape"] = preset.shape
    size, size_y = scaled_size(preset, scale)
    data.size = size
    written["size"] = size
    if hasattr(data, "size_y"):
        data.size_y = size_y
        written["size_y"] = size_y
    energy = scaled_energy(preset, scale)
    data.energy = energy
    written["energy"] = energy
    spread = spread_radians(preset.spread_deg)
    if hasattr(data, "spread"):
        data.spread = spread
        written["spread"] = spread
    written["uses_size_y"] = uses_size_y(preset.shape)
    written["nodes"] = preset.nodes
    return written


def _base_nodes() -> tuple[NodeSpec, ...]:
    return (
        NodeSpec("tex_coord", NODE_TEX, TYPE_TEX),
        NodeSpec("mapping", NODE_MAP, TYPE_MAP),
        NodeSpec("gradient", NODE_GRAD, TYPE_GRAD),
        NodeSpec("ramp", NODE_RAMP, TYPE_RAMP),
        NodeSpec("emission", NODE_EMISSION, TYPE_EMISSION),
        NodeSpec("output", NODE_OUTPUT, TYPE_OUTPUT),
    )


def _base_links() -> tuple[LinkSpec, ...]:
    return (
        LinkSpec("tex_coord", "Generated", "mapping", "Vector"),
        LinkSpec("mapping", "Vector", "gradient", "Vector"),
        LinkSpec("gradient", "Fac", "ramp", "Fac"),
        LinkSpec("ramp", "Color", "emission", "Color"),
        LinkSpec("emission", "Emission", "output", "Surface"),
    )


def node_graph_for(look: NodeLook) -> NodeGraph | None:
    """Procedural emission falloff, or None for a uniform area (Hard key)."""
    if look == "NONE":
        return None
    nodes = _base_nodes()
    links = _base_links()
    if look == "SOFTBOX":
        return NodeGraph(
            nodes=nodes,
            links=links,
            gradient_type=GRADIENT_SPHERE,
            mapping=MappingValues(CENTER_MAPPING_LOCATION, CENTER_MAPPING_SCALE),
            ramp=SOFTBOX_RAMP,
        )
    if look == "STRIP":
        return NodeGraph(
            nodes=nodes,
            links=links,
            gradient_type=GRADIENT_LINEAR,
            mapping=MappingValues(IDENTITY_MAPPING_LOCATION, IDENTITY_MAPPING_SCALE),
            ramp=STRIP_RAMP,
        )
    if look == "OCTA":
        return NodeGraph(
            nodes=nodes,
            links=links,
            gradient_type=GRADIENT_SPHERE,
            mapping=MappingValues(CENTER_MAPPING_LOCATION, CENTER_MAPPING_SCALE),
            ramp=OCTA_RAMP,
        )
    unreachable: Never = look
    raise RuntimeError(f"unhandled light node look: {unreachable}")


def applied_message(label: str, light_name: str) -> str:
    shown = light_name
    if shown.startswith("BEHOLD_"):
        shown = shown[len("BEHOLD_") :]
    return f"Applied {label} to {shown}"


def unknown_preset_message(preset_id: str) -> str:
    shown = (preset_id or "").strip() or "that shape"
    return f"Unknown light shape “{shown}” — pick Softbox, Strip, Octa, Hard, or Rim"
