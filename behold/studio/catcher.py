# SPDX-License-Identifier: GPL-3.0-or-later
"""Ground contact / shadow catcher plan — no Blender import.

Product shots need believable contact after Build Studio. Cyclorama keeps
the visible sweep and gets a soft contact disc; Solid / HDRI backdrops
get an optional catcher plane (Cycles ``Object.is_shadow_catcher`` plus
an EEVEE-friendly material fallback when that RNA is missing). Light
contact-shadow RNA is the Draft/EEVEE extra. Gobos / IES / logo / engine
panel changes are out of scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Never

from .fit import MIN_EXTENT

BackdropId = Literal["CYCLORAMA", "SOLID", "HDRI"]
HostId = Literal["CYCLORAMA", "PLANE"]
KindId = Literal["NONE", "CONTACT", "PLANE"]

DEFAULT_BACKDROP: BackdropId = "CYCLORAMA"
DEFAULT_ENABLED = True

CONTACT_OBJECT = "BEHOLD_ContactShadow"
CATCHER_OBJECT = "BEHOLD_ShadowCatcher"
CONTACT_MATERIAL = "BEHOLD_ContactShadow"
FALLBACK_MATERIAL = "BEHOLD_CatcherFallback"

CONTACT_MARGIN = 1.6
CONTACT_STRENGTH = 0.5
CONTACT_STRENGTH_WITH_PLANE = 0.28
CONTACT_OFFSET_RATIO = 0.001
CONTACT_OFFSET_MIN = 0.0002
LIGHT_CONTACT_DISTANCE_RATIO = 0.4
LIGHT_CONTACT_DISTANCE_MIN = 0.05
LIGHT_CONTACT_BIAS = 0.03
LIGHT_CONTACT_THICKNESS = 0.15

# Generated 0–1 → centered -1..1 so Quadratic Sphere falls off from the middle.
CENTER_MAPPING_LOCATION = (-0.5, -0.5, -0.5)
CENTER_MAPPING_SCALE = (2.0, 2.0, 2.0)
GRADIENT_SPHERE = "QUADRATIC_SPHERE"

NODE_TEX = "BEHOLD_CatcherTexCoord"
NODE_MAP = "BEHOLD_CatcherMapping"
NODE_GRAD = "BEHOLD_CatcherGradient"
NODE_MATH = "BEHOLD_CatcherStrength"
NODE_TRANSPARENT = "BEHOLD_CatcherTransparent"
NODE_DIFFUSE = "BEHOLD_CatcherDiffuse"
NODE_MIX = "BEHOLD_CatcherMix"
NODE_OUTPUT = "BEHOLD_CatcherOutput"
NODE_LIGHT_PATH = "BEHOLD_CatcherLightPath"

TYPE_TEX = "ShaderNodeTexCoord"
TYPE_MAP = "ShaderNodeMapping"
TYPE_GRAD = "ShaderNodeTexGradient"
TYPE_MATH = "ShaderNodeMath"
TYPE_TRANSPARENT = "ShaderNodeBsdfTransparent"
TYPE_DIFFUSE = "ShaderNodeBsdfDiffuse"
TYPE_MIX = "ShaderNodeMixShader"
TYPE_OUTPUT = "ShaderNodeOutputMaterial"
TYPE_LIGHT_PATH = "ShaderNodeLightPath"

NO_CATCHER_API = (
    "Shadow catcher needs object Visibility RNA — update Blender, then Catcher"
)
NO_STUDIO = "No studio yet — Build Studio, then Catcher"
NO_PRODUCT_FOR_CATCHER = (
    "No product for ground contact — select the mesh or Import Product"
)
CATCHER_FAILED = (
    "Could not set ground contact — Build Studio, then try Catcher again"
)
CATCHER_OFF = "Catcher off — the product has no extra ground contact"
UNKNOWN_BACKDROP = "Unknown backdrop — pick Cyclorama, Solid, or HDRI"


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
class MappingValues:
    location: tuple[float, float, float]
    scale: tuple[float, float, float]


@dataclass(frozen=True)
class NodeGraph:
    nodes: tuple[NodeSpec, ...]
    links: tuple[LinkSpec, ...]
    gradient_type: str | None
    mapping: MappingValues | None
    math_operation: str | None
    math_value: float
    diffuse_color: tuple[float, float, float, float]


@dataclass(frozen=True)
class LightContact:
    use_contact_shadow: bool
    distance: float
    bias: float
    thickness: float


@dataclass(frozen=True)
class CatcherPlan:
    enabled: bool
    backdrop: BackdropId
    host: HostId
    kind: KindId
    use_cycles_catcher: bool
    use_eevee_fallback: bool
    use_contact: bool
    catcher_size: float
    contact_size: float
    contact_offset: float
    contact_strength: float
    light_contact: LightContact


def is_backdrop(value: str) -> bool:
    return value in ("CYCLORAMA", "SOLID", "HDRI")


def normalize_backdrop(
    value: str, default: BackdropId = DEFAULT_BACKDROP
) -> BackdropId:
    raw = (value or "").strip().upper()
    if raw == "CYCLORAMA":
        return "CYCLORAMA"
    if raw == "SOLID":
        return "SOLID"
    if raw == "HDRI":
        return "HDRI"
    if default == "CYCLORAMA":
        return "CYCLORAMA"
    if default == "SOLID":
        return "SOLID"
    if default == "HDRI":
        return "HDRI"
    unreachable: Never = default
    raise RuntimeError(f"unhandled backdrop default: {unreachable}")


def host_for(backdrop: BackdropId) -> HostId:
    if backdrop == "CYCLORAMA":
        return "CYCLORAMA"
    if backdrop == "SOLID":
        return "PLANE"
    if backdrop == "HDRI":
        return "PLANE"
    unreachable: Never = backdrop
    raise RuntimeError(f"unhandled backdrop: {unreachable}")


def host_label(host: HostId) -> str:
    if host == "CYCLORAMA":
        return "cyclorama"
    if host == "PLANE":
        return "plane"
    unreachable: Never = host
    raise RuntimeError(f"unhandled catcher host: {unreachable}")


def kind_for(*, enabled: bool, host: HostId) -> KindId:
    if not enabled:
        return "NONE"
    if host == "CYCLORAMA":
        return "CONTACT"
    if host == "PLANE":
        return "PLANE"
    unreachable: Never = host
    raise RuntimeError(f"unhandled catcher host: {unreachable}")


def capability_problem(*, has_shadow_catcher: bool, needs_cycles_flag: bool) -> str | None:
    """Missing RNA is not fatal when the EEVEE fallback / contact disc can run."""
    if needs_cycles_flag and not has_shadow_catcher:
        return None
    return None


def clamp_positive(value: float, *, fallback: float = MIN_EXTENT) -> float:
    number = float(value)
    if number != number or number <= 0.0:  # NaN-safe
        return fallback
    return max(number, fallback)


def contact_size_for(width: float, depth: float, floor_size: float) -> float:
    footprint = max(clamp_positive(width), clamp_positive(depth))
    wanted = max(footprint * CONTACT_MARGIN, MIN_EXTENT)
    ceiling = clamp_positive(floor_size)
    return min(wanted, ceiling)


def contact_offset_for(product_size: float) -> float:
    return max(CONTACT_OFFSET_MIN, clamp_positive(product_size) * CONTACT_OFFSET_RATIO)


def light_contact_distance_for(height: float) -> float:
    return max(
        LIGHT_CONTACT_DISTANCE_MIN,
        clamp_positive(height) * LIGHT_CONTACT_DISTANCE_RATIO,
    )


def contact_strength_for(*, use_plane: bool) -> float:
    if use_plane:
        return CONTACT_STRENGTH_WITH_PLANE
    return CONTACT_STRENGTH


def light_contact_for(*, enabled: bool, height: float) -> LightContact:
    return LightContact(
        use_contact_shadow=bool(enabled),
        distance=light_contact_distance_for(height),
        bias=LIGHT_CONTACT_BIAS,
        thickness=LIGHT_CONTACT_THICKNESS,
    )


def _contact_graph(strength: float) -> NodeGraph:
    return NodeGraph(
        nodes=(
            NodeSpec("tex", NODE_TEX, TYPE_TEX),
            NodeSpec("mapping", NODE_MAP, TYPE_MAP),
            NodeSpec("gradient", NODE_GRAD, TYPE_GRAD),
            NodeSpec("math", NODE_MATH, TYPE_MATH),
            NodeSpec("transparent", NODE_TRANSPARENT, TYPE_TRANSPARENT),
            NodeSpec("diffuse", NODE_DIFFUSE, TYPE_DIFFUSE),
            NodeSpec("mix", NODE_MIX, TYPE_MIX),
            NodeSpec("output", NODE_OUTPUT, TYPE_OUTPUT),
        ),
        links=(
            LinkSpec("tex", "Generated", "mapping", "Vector"),
            LinkSpec("mapping", "Vector", "gradient", "Vector"),
            LinkSpec("gradient", "Color", "math", 0),
            LinkSpec("math", "Value", "mix", 0),
            LinkSpec("transparent", "BSDF", "mix", 1),
            LinkSpec("diffuse", "BSDF", "mix", 2),
            LinkSpec("mix", "Shader", "output", "Surface"),
        ),
        gradient_type=GRADIENT_SPHERE,
        mapping=MappingValues(
            location=CENTER_MAPPING_LOCATION,
            scale=CENTER_MAPPING_SCALE,
        ),
        math_operation="MULTIPLY",
        math_value=float(strength),
        diffuse_color=(0.0, 0.0, 0.0, 1.0),
    )


def _fallback_graph() -> NodeGraph:
    """Cycles Light Path catcher: camera rays see air, shadow rays see black."""
    return NodeGraph(
        nodes=(
            NodeSpec("light_path", NODE_LIGHT_PATH, TYPE_LIGHT_PATH),
            NodeSpec("transparent", NODE_TRANSPARENT, TYPE_TRANSPARENT),
            NodeSpec("diffuse", NODE_DIFFUSE, TYPE_DIFFUSE),
            NodeSpec("mix", NODE_MIX, TYPE_MIX),
            NodeSpec("output", NODE_OUTPUT, TYPE_OUTPUT),
        ),
        links=(
            LinkSpec("light_path", "Is Shadow Ray", "mix", 0),
            LinkSpec("transparent", "BSDF", "mix", 1),
            LinkSpec("diffuse", "BSDF", "mix", 2),
            LinkSpec("mix", "Shader", "output", "Surface"),
        ),
        gradient_type=None,
        mapping=None,
        math_operation=None,
        math_value=0.0,
        diffuse_color=(0.0, 0.0, 0.0, 1.0),
    )


def contact_graph(strength: float = CONTACT_STRENGTH) -> NodeGraph:
    return _contact_graph(max(0.0, min(1.0, float(strength))))


def fallback_graph() -> NodeGraph:
    return _fallback_graph()


def plan_catcher(
    *,
    enabled: bool,
    backdrop: str,
    width: float,
    depth: float,
    height: float,
    floor_size: float,
    has_shadow_catcher: bool = True,
) -> CatcherPlan | str:
    raw = (backdrop or "").strip()
    if raw and not is_backdrop(raw.upper()):
        return UNKNOWN_BACKDROP
    bid = normalize_backdrop(raw)
    host = host_for(bid)
    kind = kind_for(enabled=bool(enabled), host=host)
    use_plane = bool(enabled) and host == "PLANE"
    use_contact = bool(enabled)
    use_cycles = use_plane and bool(has_shadow_catcher)
    use_eevee_fallback = use_plane and not bool(has_shadow_catcher)
    product_size = max(
        clamp_positive(width),
        clamp_positive(depth),
        clamp_positive(height),
    )
    return CatcherPlan(
        enabled=bool(enabled),
        backdrop=bid,
        host=host,
        kind=kind,
        use_cycles_catcher=use_cycles,
        use_eevee_fallback=use_eevee_fallback,
        use_contact=use_contact,
        catcher_size=clamp_positive(floor_size),
        contact_size=contact_size_for(width, depth, floor_size),
        contact_offset=contact_offset_for(product_size),
        contact_strength=contact_strength_for(use_plane=use_plane),
        light_contact=light_contact_for(enabled=bool(enabled), height=height),
    )


def apply_message(plan: CatcherPlan) -> str:
    if not plan.enabled or plan.kind == "NONE":
        return CATCHER_OFF
    if plan.kind == "CONTACT":
        return "Ground contact on cyclorama — soft contact shadow"
    if plan.kind == "PLANE":
        if plan.use_eevee_fallback:
            return "Shadow catcher plane — EEVEE fallback material"
        return "Shadow catcher plane — Cycles catcher"
    unreachable: Never = plan.kind
    raise RuntimeError(f"unhandled catcher kind: {unreachable}")
