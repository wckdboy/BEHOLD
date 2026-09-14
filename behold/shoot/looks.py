# SPDX-License-Identifier: GPL-3.0-or-later
"""Compositor look pack spec — vignette / grain / contrast / bloom-safe glare.

No Blender import. Maps Clean / Catalog / Dramatic onto a compositor node
graph BEHOLD builds and tears down by name prefix. Catalog stays bloom-safe
(no glare). Dramatic uses a mild Fog Glow mix so highlights do not blow.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Never

LookId = Literal["CLEAN", "CATALOG", "DRAMATIC"]

DEFAULT_PRESET = "CLEAN"
OWNED_PREFIX = "BEHOLD_Look"
TREE_OWNED_KEY = "behold_look_owned"

NODE_RLAYERS = "BEHOLD_LookRLayers"
NODE_COMPOSITE = "BEHOLD_LookComposite"
NODE_CONTRAST = "BEHOLD_LookContrast"
NODE_VIGNETTE_COLOR = "BEHOLD_LookVignetteColor"
NODE_VIGNETTE_MASK = "BEHOLD_LookVignetteMask"
NODE_VIGNETTE_BLUR = "BEHOLD_LookVignetteBlur"
NODE_VIGNETTE_INVERT = "BEHOLD_LookVignetteInvert"
NODE_VIGNETTE_AMOUNT = "BEHOLD_LookVignetteAmount"
NODE_VIGNETTE_MIX = "BEHOLD_LookVignetteMix"
NODE_GRAIN = "BEHOLD_LookGrain"
NODE_GRAIN_MIX = "BEHOLD_LookGrainMix"
NODE_GLARE = "BEHOLD_LookGlare"

TYPE_RLAYERS = "CompositorNodeRLayers"
TYPE_COMPOSITE = "CompositorNodeComposite"
TYPE_CONTRAST = "CompositorNodeBrightContrast"
TYPE_RGB = "CompositorNodeRGB"
TYPE_ELLIPSE = "CompositorNodeEllipseMask"
TYPE_BLUR = "CompositorNodeBlur"
TYPE_INVERT = "CompositorNodeInvert"
TYPE_MATH = "CompositorNodeMath"
TYPE_MIX = "CompositorNodeMixRGB"
TYPE_GRAIN = "CompositorNodeTexture"
TYPE_GLARE = "CompositorNodeGlare"

MIX_BLEND_MULTIPLY = "MULTIPLY"
MIX_BLEND_MIX = "MIX"
MATH_MULTIPLY = "MULTIPLY"
GLARE_FOG_GLOW = "FOG_GLOW"
GRAIN_TEXTURE_NAME = "BEHOLD_LookGrain"

LOOK_DISABLED = "Look compositor off — stills skip vignette and grain"
NO_COMPOSITOR = (
    "No compositor on this scene — pick a scene, then toggle Compositor on Shoot"
)
LOOK_COMPOSITOR_BUSY = (
    "This scene already has compositor nodes — clear them, then toggle Compositor"
)
LOOK_NODES_FAILED = (
    "Could not build that compositor look — this Blender build is missing a "
    "compositor node. Try Clean, or update Blender"
)
UNKNOWN_LOOK_PRESET = (
    "Unknown look — pick Clean, Catalog, or Dramatic"
)


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
class LookPreset:
    id: LookId
    label: str
    description: str
    vignette: float
    vignette_width: float
    vignette_height: float
    vignette_blur: float
    grain: float
    contrast: float
    glare_mix: float
    glare_threshold: float
    glare_size: int
    bloom_safe: bool


@dataclass(frozen=True)
class NodeGraph:
    nodes: tuple[NodeSpec, ...]
    links: tuple[LinkSpec, ...]
    preset_id: LookId
    include_vignette: bool
    include_grain: bool
    include_contrast: bool
    include_glare: bool
    contrast: float
    vignette: float
    vignette_width: float
    vignette_height: float
    vignette_blur: float
    grain: float
    glare_mix: float
    glare_threshold: float
    glare_size: int
    vignette_blend: str = MIX_BLEND_MULTIPLY
    grain_blend: str = MIX_BLEND_MIX
    math_operation: str = MATH_MULTIPLY
    glare_type: str = GLARE_FOG_GLOW


PRESETS: dict[str, LookPreset] = {
    "CLEAN": LookPreset(
        id="CLEAN",
        label="Clean",
        description="Compositor passthrough — no vignette, grain, or glare",
        vignette=0.0,
        vignette_width=0.95,
        vignette_height=0.95,
        vignette_blur=8.0,
        grain=0.0,
        contrast=0.0,
        glare_mix=-1.0,
        glare_threshold=1.0,
        glare_size=5,
        bloom_safe=True,
    ),
    "CATALOG": LookPreset(
        id="CATALOG",
        label="Catalog",
        description="Mild vignette and grain, contrast only, bloom off",
        vignette=0.22,
        vignette_width=0.88,
        vignette_height=0.78,
        vignette_blur=14.0,
        grain=0.018,
        contrast=0.08,
        glare_mix=-1.0,
        glare_threshold=1.0,
        glare_size=5,
        bloom_safe=True,
    ),
    "DRAMATIC": LookPreset(
        id="DRAMATIC",
        label="Dramatic",
        description="Stronger vignette and grain, mild bloom-safe glare",
        vignette=0.42,
        vignette_width=0.74,
        vignette_height=0.64,
        vignette_blur=18.0,
        grain=0.045,
        contrast=0.16,
        glare_mix=-0.88,
        glare_threshold=0.85,
        glare_size=7,
        bloom_safe=True,
    ),
}


def preset_enum_items() -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (preset.id, preset.label, preset.description) for preset in PRESETS.values()
    )


def get_preset(preset_id: str) -> LookPreset | None:
    return PRESETS.get((preset_id or "").strip())


def owned_node_name(name: str) -> bool:
    return (name or "").startswith(OWNED_PREFIX)


def remaining_after_teardown(names: Iterable[str]) -> tuple[str, ...]:
    """Node names that should survive a BEHOLD look teardown."""
    return tuple(name for name in names if not owned_node_name(name))


def unknown_look_message(preset_id: str) -> str:
    shown = (preset_id or "").strip()
    if not shown:
        return UNKNOWN_LOOK_PRESET
    return f"Unknown look “{shown}” — pick Clean, Catalog, or Dramatic"


def applied_message(preset: LookPreset) -> str:
    if preset.id == "CLEAN":
        return "Applied Clean look — compositor passthrough (no vignette or grain)"
    if preset.id == "CATALOG":
        return "Applied Catalog look — mild vignette and grain, bloom off"
    if preset.id == "DRAMATIC":
        return "Applied Dramatic look — vignette, grain, and mild bloom-safe glare"
    unreachable: Never = preset.id
    raise RuntimeError(f"unhandled look preset: {unreachable}")


def disabled_message() -> str:
    return LOOK_DISABLED


def _rlayers_and_composite() -> tuple[NodeSpec, NodeSpec]:
    return (
        NodeSpec("rlayers", NODE_RLAYERS, TYPE_RLAYERS),
        NodeSpec("composite", NODE_COMPOSITE, TYPE_COMPOSITE),
    )


def _passthrough_graph(preset: LookPreset) -> NodeGraph:
    rlayers, composite = _rlayers_and_composite()
    return NodeGraph(
        nodes=(rlayers, composite),
        links=(LinkSpec("rlayers", "Image", "composite", "Image"),),
        preset_id=preset.id,
        include_vignette=False,
        include_grain=False,
        include_contrast=False,
        include_glare=False,
        contrast=preset.contrast,
        vignette=preset.vignette,
        vignette_width=preset.vignette_width,
        vignette_height=preset.vignette_height,
        vignette_blur=preset.vignette_blur,
        grain=preset.grain,
        glare_mix=preset.glare_mix,
        glare_threshold=preset.glare_threshold,
        glare_size=preset.glare_size,
    )


def _effects_graph(preset: LookPreset, *, include_glare: bool) -> NodeGraph:
    rlayers, composite = _rlayers_and_composite()
    nodes: list[NodeSpec] = [
        rlayers,
        NodeSpec("contrast", NODE_CONTRAST, TYPE_CONTRAST),
        NodeSpec("vignette_color", NODE_VIGNETTE_COLOR, TYPE_RGB),
        NodeSpec("vignette_mask", NODE_VIGNETTE_MASK, TYPE_ELLIPSE),
        NodeSpec("vignette_blur", NODE_VIGNETTE_BLUR, TYPE_BLUR),
        NodeSpec("vignette_invert", NODE_VIGNETTE_INVERT, TYPE_INVERT),
        NodeSpec("vignette_amount", NODE_VIGNETTE_AMOUNT, TYPE_MATH),
        NodeSpec("vignette_mix", NODE_VIGNETTE_MIX, TYPE_MIX),
        NodeSpec("grain", NODE_GRAIN, TYPE_GRAIN),
        NodeSpec("grain_mix", NODE_GRAIN_MIX, TYPE_MIX),
    ]
    if include_glare:
        nodes.append(NodeSpec("glare", NODE_GLARE, TYPE_GLARE))
    nodes.append(composite)

    links: list[LinkSpec] = [
        LinkSpec("rlayers", "Image", "contrast", "Image"),
        LinkSpec("contrast", "Image", "vignette_mix", "Color1"),
        LinkSpec("vignette_color", "Image", "vignette_mix", "Color2"),
        LinkSpec("vignette_mask", "Mask", "vignette_blur", "Image"),
        LinkSpec("vignette_blur", "Image", "vignette_invert", "Color"),
        LinkSpec("vignette_invert", "Color", "vignette_amount", 0),
        LinkSpec("vignette_amount", "Value", "vignette_mix", "Fac"),
        LinkSpec("vignette_mix", "Image", "grain_mix", "Color1"),
        LinkSpec("grain", "Color", "grain_mix", "Color2"),
    ]
    if include_glare:
        links.append(LinkSpec("grain_mix", "Image", "glare", "Image"))
        links.append(LinkSpec("glare", "Image", "composite", "Image"))
    else:
        links.append(LinkSpec("grain_mix", "Image", "composite", "Image"))

    return NodeGraph(
        nodes=tuple(nodes),
        links=tuple(links),
        preset_id=preset.id,
        include_vignette=True,
        include_grain=True,
        include_contrast=True,
        include_glare=include_glare,
        contrast=preset.contrast,
        vignette=preset.vignette,
        vignette_width=preset.vignette_width,
        vignette_height=preset.vignette_height,
        vignette_blur=preset.vignette_blur,
        grain=preset.grain,
        glare_mix=preset.glare_mix,
        glare_threshold=preset.glare_threshold,
        glare_size=preset.glare_size,
    )


def node_graph_for(preset_id: str) -> NodeGraph | None:
    """Compositor graph for a look, or None when the id is unknown."""
    preset = get_preset(preset_id)
    if preset is None:
        return None
    if preset.id == "CLEAN":
        return _passthrough_graph(preset)
    if preset.id == "CATALOG":
        return _effects_graph(preset, include_glare=False)
    if preset.id == "DRAMATIC":
        return _effects_graph(preset, include_glare=True)
    unreachable: Never = preset.id
    raise RuntimeError(f"unhandled look preset: {unreachable}")
