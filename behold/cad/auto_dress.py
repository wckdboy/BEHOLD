# SPDX-License-Identifier: GPL-3.0-or-later
"""Per-body auto-dress — STEP color / name → a local rack look (no Blender).

Assist still applies one look to the whole selection. This planner dresses
each body on its own: part-name hints first (same Material Assist regexes),
then a real STEP / viewport color. The CAD filename is not a per-body
fallback — that would paint every solid the same. Not a material library.
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass
from typing import Literal, Mapping, Never, Sequence

from ..materials.presets import PRESETS, material_name_for, preset_for_query
from .hints import (
    DEFAULT_QUERY,
    suggest_query_for_text,
    suggest_query_from_parts_or_none,
)

DressSource = Literal["name", "material", "color", "skip"]

NO_BODY_HINT = (
    "No STEP color or part-name hint — "
    "name the bodies or use Assist for one look"
)
AUTO_DRESS_FAILED = (
    "Could not auto-dress those bodies — select the product or Import Product"
)

# Blender object-color white and Principled's factory 0.8 grey are not STEP.
_PLACEHOLDER_RGB: tuple[tuple[float, float, float], ...] = (
    (1.0, 1.0, 1.0),
    (0.8, 0.8, 0.8),
)
_PLACEHOLDER_EPS = 0.02
_COLOR_255 = 1.0 + 1e-6


@dataclass(frozen=True)
class BodyHint:
    """One imported CAD body (or selected mesh) as the planner sees it."""

    name: str = ""
    custom_hints: tuple[str, ...] = ()
    material_names: tuple[str, ...] = ()
    color: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class BodyDressPlan:
    body_name: str
    query: str
    preset_id: str
    source: DressSource
    base_color: tuple[float, float, float] | None
    material_name: str


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def rgb_channel_distance(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> float:
    return max(abs(left[i] - right[i]) for i in range(3))


def is_placeholder_color(rgb: tuple[float, float, float]) -> bool:
    """True for unset Blender defaults, not for a real CAD aluminium/paint."""
    for placeholder in _PLACEHOLDER_RGB:
        if rgb_channel_distance(rgb, placeholder) <= _PLACEHOLDER_EPS:
            return True
    return False


def rgb_from_any(value: object) -> tuple[float, float, float] | None:
    """Parse a STEP / viewport color. Accepts RGB, RGBA, 0–255, or #RRGGBB."""
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.startswith("#") and len(text) >= 7:
            try:
                r = int(text[1:3], 16) / 255.0
                g = int(text[3:5], 16) / 255.0
                b = int(text[5:7], 16) / 255.0
            except ValueError:
                return None
            return (clamp01(r), clamp01(g), clamp01(b))
        parts = text.replace(",", " ").split()
        if len(parts) >= 3:
            try:
                nums = [float(parts[0]), float(parts[1]), float(parts[2])]
            except ValueError:
                return None
            return _rgb_from_floats(nums)
        return None
    try:
        seq = [float(value[0]), float(value[1]), float(value[2])]  # type: ignore[index]
    except (TypeError, ValueError, IndexError):
        return None
    return _rgb_from_floats(seq)


def _rgb_from_floats(values: Sequence[float]) -> tuple[float, float, float] | None:
    if len(values) < 3:
        return None
    r, g, b = float(values[0]), float(values[1]), float(values[2])
    if max(r, g, b) > _COLOR_255:
        r, g, b = r / 255.0, g / 255.0, b / 255.0
    return (clamp01(r), clamp01(g), clamp01(b))


def usable_color(
    rgb: tuple[float, float, float] | None,
) -> tuple[float, float, float] | None:
    if rgb is None or is_placeholder_color(rgb):
        return None
    return rgb


def preset_for_color(rgb: tuple[float, float, float] | None) -> str | None:
    """Map a real STEP RGB onto the local rack. None = no color look."""
    color = usable_color(rgb)
    if color is None:
        return None
    hue, sat, val = colorsys.rgb_to_hsv(color[0], color[1], color[2])
    if val < 0.16 and sat < 0.35:
        return "RUBBER"
    if sat >= 0.22 and val >= 0.35:
        if 0.04 <= hue <= 0.13:
            return "METAL"
        if hue <= 0.04 or hue >= 0.92:
            if sat >= 0.45:
                return "PAINT"
            return "METAL"
    if sat < 0.18:
        if val < 0.22:
            return "RUBBER"
        return "METAL"
    if sat >= 0.4 and (hue <= 0.08 or hue >= 0.92):
        return "PAINT"
    if 0.08 <= hue <= 0.18 and sat >= 0.4:
        return "PAINT"
    return "PLASTIC"


def named_query(hint: BodyHint) -> tuple[str, DressSource] | None:
    """Name-side ranking only — same regexes as Assist, no filename default."""
    custom = tuple(
        value.strip()
        for value in hint.custom_hints
        if isinstance(value, str)
        and value.strip()
        and value.strip().lower() != DEFAULT_QUERY
    )
    if custom:
        hit = suggest_query_from_parts_or_none(custom_hints=custom)
        if hit:
            return hit, "name"
    if hint.name:
        hit = suggest_query_for_text(hint.name)
        if hit:
            return hit, "name"
    hit = suggest_query_from_parts_or_none(material_names=hint.material_names)
    if hit:
        return hit, "material"
    return None


def tint_for_preset(
    preset_id: str,
    rgb: tuple[float, float, float] | None,
) -> tuple[float, float, float] | None:
    """Keep glass clear. Otherwise keep the STEP color on the rack look."""
    if preset_id == "GLASS":
        return None
    color = usable_color(rgb)
    if color is None:
        return None
    default = PRESETS[preset_id]["base_color"][:3]
    if rgb_channel_distance(color, (float(default[0]), float(default[1]), float(default[2]))) <= (
        _PLACEHOLDER_EPS
    ):
        return None
    return color


def auto_material_name(
    preset_id: str,
    base_color: tuple[float, float, float] | None,
) -> str:
    """Tinted looks stay `BEHOLD_Metal.RRGGBB` so the flow strip still counts."""
    base = material_name_for(preset_id)
    if base_color is None:
        return base
    hex_rgb = "".join(f"{int(round(clamp01(channel) * 255.0)):02X}" for channel in base_color)
    return f"{base}.{hex_rgb}"


def skipped_plan(body_name: str) -> BodyDressPlan:
    return BodyDressPlan(
        body_name=body_name,
        query="",
        preset_id="",
        source="skip",
        base_color=None,
        material_name="",
    )


def plan_body_dress(hint: BodyHint) -> BodyDressPlan:
    """One body → one rack look, or skip when there is nothing to go on."""
    named = named_query(hint)
    color_preset = preset_for_color(hint.color)
    if named is not None:
        query, source = named
        preset_id = preset_for_query(query)
        tint = tint_for_preset(preset_id, hint.color)
        return BodyDressPlan(
            body_name=hint.name,
            query=query,
            preset_id=preset_id,
            source=source,
            base_color=tint,
            material_name=auto_material_name(preset_id, tint),
        )
    if color_preset is not None:
        tint = tint_for_preset(color_preset, hint.color)
        query = PRESETS[color_preset]["label"].lower() + " (STEP color)"
        return BodyDressPlan(
            body_name=hint.name,
            query=query,
            preset_id=color_preset,
            source="color",
            base_color=tint,
            material_name=auto_material_name(color_preset, tint),
        )
    return skipped_plan(hint.name)


def plan_bodies(hints: Sequence[BodyHint]) -> tuple[BodyDressPlan, ...]:
    return tuple(plan_body_dress(hint) for hint in hints)


def count_by_preset(plans: Sequence[BodyDressPlan]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for plan in plans:
        if plan.source == "skip":
            continue
        counts[plan.preset_id] = counts.get(plan.preset_id, 0) + 1
    return counts


def _looks_caption(counts: Mapping[str, int]) -> str:
    bits: list[str] = []
    for preset_id in PRESETS:
        n = counts.get(preset_id, 0)
        if n:
            bits.append(f"{PRESETS[preset_id]['label']} ×{n}")
    for preset_id, n in counts.items():
        if preset_id not in PRESETS and n:
            bits.append(f"{preset_id} ×{n}")
    return ", ".join(bits)


def auto_dress_summary(
    plans: Sequence[BodyDressPlan],
    *,
    applied: int | None = None,
) -> str:
    dressed = sum(1 for plan in plans if plan.source != "skip")
    skipped = sum(1 for plan in plans if plan.source == "skip")
    landed = dressed if applied is None else applied
    if landed <= 0:
        return NO_BODY_HINT
    looks = _looks_caption(count_by_preset(plans))
    body_word = "body" if landed == 1 else "bodies"
    if looks:
        base = f"Auto-dressed {landed} {body_word} ({looks})"
    else:
        base = f"Auto-dressed {landed} {body_word}"
    if skipped:
        return f"{base}; {skipped} skipped — Assist for one look"
    return base


def source_label(source: DressSource) -> str:
    if source == "name":
        return "part name"
    if source == "material":
        return "STEP material name"
    if source == "color":
        return "STEP color"
    if source == "skip":
        return "skipped"
    unreachable: Never = source
    raise RuntimeError(f"unhandled dress source: {unreachable}")
