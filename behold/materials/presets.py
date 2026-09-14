# SPDX-License-Identifier: GPL-3.0-or-later
"""Local PBR rack + Material Assist mapping (no Blender import).

Principled BSDF sockets differ across Blender 4.2 and 5.x (Transmission vs
Transmission Weight, Clearcoat vs Coat Weight). Apply through SOCKET_ALIASES
so product looks land on whichever name the host shader exposes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

DEFAULT_PRESET = "METAL"
DEFAULT_QUERY = "brushed metal"

EMPTY_NO_MESH = "Select a product mesh"
EMPTY_NO_MESH_HINT = "Import a product or select a mesh in the viewport"

# Studio sweep / catcher — do not dress these as the product.
STUDIO_SKIP_MESHES = frozenset({"BEHOLD_Cyclorama", "BEHOLD_ShadowCatcher"})

# 4.2+ / 5.2 LTS Principled BSDF. First name is the current Cycles/EEVEE Next
# identifier; fallbacks cover older RNA still present on some 4.x builds.
SOCKET_ALIASES: dict[str, tuple[str, ...]] = {
    "base_color": ("Base Color",),
    "metallic": ("Metallic",),
    "roughness": ("Roughness",),
    "ior": ("IOR",),
    "transmission": ("Transmission Weight", "Transmission"),
    "coat": ("Coat Weight", "Clearcoat"),
    "coat_roughness": ("Coat Roughness", "Clearcoat Roughness"),
    "specular": ("Specular IOR Level", "Specular"),
    "sheen": ("Sheen Weight", "Sheen"),
    "sheen_roughness": ("Sheen Roughness",),
    "alpha": ("Alpha",),
}

PRESETS: dict[str, dict[str, Any]] = {
    "METAL": {
        "label": "Metal",
        "base_color": (0.72, 0.73, 0.75, 1.0),
        "metallic": 1.0,
        "roughness": 0.22,
        "ior": 1.45,
        "specular": 0.5,
        "transmission": 0.0,
        "coat": 0.0,
        "coat_roughness": 0.0,
        "sheen": 0.0,
        "alpha": 1.0,
    },
    "PLASTIC": {
        "label": "Plastic",
        "base_color": (0.12, 0.35, 0.75, 1.0),
        "metallic": 0.0,
        "roughness": 0.32,
        "ior": 1.46,
        "specular": 0.5,
        "transmission": 0.0,
        "coat": 0.0,
        "coat_roughness": 0.0,
        "sheen": 0.0,
        "alpha": 1.0,
    },
    "RUBBER": {
        "label": "Rubber",
        "base_color": (0.04, 0.04, 0.04, 1.0),
        "metallic": 0.0,
        "roughness": 0.72,
        "ior": 1.50,
        "specular": 0.2,
        "transmission": 0.0,
        "coat": 0.0,
        "coat_roughness": 0.0,
        "sheen": 0.35,
        "sheen_roughness": 0.5,
        "alpha": 1.0,
    },
    "GLASS": {
        "label": "Glass",
        "base_color": (1.0, 1.0, 1.0, 1.0),
        "metallic": 0.0,
        "roughness": 0.02,
        "ior": 1.50,
        "specular": 1.0,
        "transmission": 1.0,
        "coat": 0.0,
        "coat_roughness": 0.0,
        "sheen": 0.0,
        "alpha": 1.0,
    },
    "PAINT": {
        "label": "Paint",
        "base_color": (0.75, 0.12, 0.10, 1.0),
        "metallic": 0.05,
        "roughness": 0.35,
        "ior": 1.45,
        "specular": 0.5,
        "transmission": 0.0,
        "coat": 1.0,
        "coat_roughness": 0.08,
        "sheen": 0.0,
        "alpha": 1.0,
    },
}

_QUERY_PRESET: dict[str, str] = {
    "brushed aluminum": "METAL",
    "titanium metal": "METAL",
    "brushed steel": "METAL",
    "brass metal": "METAL",
    "copper metal": "METAL",
    "gold metal": "METAL",
    "silver metal": "METAL",
    "chrome metal": "METAL",
    "brushed metal": "METAL",
    "carbon fiber": "PLASTIC",
    "abs plastic": "PLASTIC",
    "matte rubber": "RUBBER",
    "clear glass": "GLASS",
    "matte paint": "PAINT",
    "wood grain": "PAINT",
    "ceramic": "PAINT",
    "leather": "RUBBER",
}

# Order matters: glass/paint before metal so "anodized aluminum" stays paint.
_KEYWORD_PRESET: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"glass|lens|acrylic|pmma|transparent", re.I), "GLASS"),
    (re.compile(r"rubber|tpu|silicone|gasket|elastomer", re.I), "RUBBER"),
    (re.compile(r"paint|coated|anodiz|enamel|lacquer", re.I), "PAINT"),
    (
        re.compile(
            r"plastic|abs|pla|nylon|pom|delrin|polycarb|polymer|cfrp|carbon",
            re.I,
        ),
        "PLASTIC",
    ),
    (
        re.compile(
            r"metal|steel|alum|chrome|gold|copper|brass|titanium|silver|"
            r"iron|zinc|nickel|inox",
            re.I,
        ),
        "METAL",
    ),
    (re.compile(r"wood|oak|walnut|maple|ceramic|porcelain", re.I), "PAINT"),
    (re.compile(r"leather", re.I), "RUBBER"),
)


@dataclass(frozen=True)
class AssistPlan:
    query: str
    preset_id: str
    apply_local: bool
    search_blenderkit: bool


def preset_enum_items() -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (key, data["label"], f"Apply {data['label']} product look")
        for key, data in PRESETS.items()
    )


def material_name_for(preset_id: str) -> str:
    return f"BEHOLD_{preset_id.title()}"


def is_dressable_mesh_name(name: str) -> bool:
    return name.split(".", 1)[0] not in STUDIO_SKIP_MESHES


def empty_state(*, has_product_mesh: bool) -> str | None:
    if not has_product_mesh:
        return EMPTY_NO_MESH
    return None


def preset_for_query(query: str) -> str:
    """Map a Material Assist / BlenderKit query onto a local rack id."""
    if not query or not query.strip():
        return DEFAULT_PRESET
    key = " ".join(query.lower().split())
    hit = _QUERY_PRESET.get(key)
    if hit is not None:
        return hit
    for pattern, preset in _KEYWORD_PRESET:
        if pattern.search(query):
            return preset
    return DEFAULT_PRESET


def plan_assist(query: str, blenderkit: Mapping[str, Any] | None = None) -> AssistPlan:
    """Always apply a local look. Search BlenderKit only when signed in."""
    status = blenderkit or {}
    cleaned = query.strip() if query else DEFAULT_QUERY
    if not cleaned:
        cleaned = DEFAULT_QUERY
    search = bool(status.get("installed")) and bool(status.get("logged_in"))
    return AssistPlan(
        query=cleaned,
        preset_id=preset_for_query(cleaned),
        apply_local=True,
        search_blenderkit=search,
    )


def assist_summary(plan: AssistPlan, *, applied: int, searched: bool) -> str:
    label = PRESETS[plan.preset_id]["label"]
    if applied:
        base = f"Applied {label} from “{plan.query}” to {applied} mesh(es)"
    else:
        base = f"No product mesh to dress (“{plan.query}” → {label})"
    if searched:
        return base + "; searched BlenderKit"
    return base + " (local look, no BlenderKit account needed)"


def _socket_from(inputs: Any, name: str) -> Any | None:
    try:
        if name in inputs:
            return inputs[name]
    except TypeError:
        pass
    getter = getattr(inputs, "get", None)
    if getter is not None:
        try:
            return getter(name)
        except Exception:  # noqa: BLE001 — bpy RNA collections vary
            return None
    return None


def apply_preset_to_sockets(inputs: Any, preset: Mapping[str, Any]) -> dict[str, str]:
    """Write preset fields onto Principled BSDF inputs (4.2 or 5.2 names)."""
    written: dict[str, str] = {}
    for field, aliases in SOCKET_ALIASES.items():
        if field not in preset:
            continue
        value = preset[field]
        for name in aliases:
            sock = _socket_from(inputs, name)
            if sock is None:
                continue
            sock.default_value = value
            written[field] = name
            break
    return written
