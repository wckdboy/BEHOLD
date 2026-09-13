# SPDX-License-Identifier: GPL-3.0-or-later
"""Filename / part-name hints for Material Assist (no Blender import)."""

from __future__ import annotations

import os
import re

_NAME_HINTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"alum|al[\s_-]?6061|al[\s_-]?7075", re.I), "brushed aluminum"),
    (re.compile(r"titanium|ti[\s_-]?6al", re.I), "titanium metal"),
    (re.compile(r"steel|ss[\s_-]?304|inox", re.I), "brushed steel"),
    (re.compile(r"brass|bronze", re.I), "brass metal"),
    (re.compile(r"copper", re.I), "copper metal"),
    (re.compile(r"gold|gild", re.I), "gold metal"),
    (re.compile(r"silver", re.I), "silver metal"),
    (re.compile(r"chrome|mirror|polish", re.I), "chrome metal"),
    (re.compile(r"carbon[\s_-]?fiber|cfrp", re.I), "carbon fiber"),
    (re.compile(r"plastic|abs|pla|nylon|pom|delrin|pc\b|polycarb", re.I), "abs plastic"),
    (re.compile(r"rubber|tpu|silicone|gasket", re.I), "matte rubber"),
    (re.compile(r"glass|lens|acrylic|pmma", re.I), "clear glass"),
    (re.compile(r"paint|coated|anodiz", re.I), "matte paint"),
    (re.compile(r"wood|oak|walnut|maple", re.I), "wood grain"),
    (re.compile(r"ceramic|porcelain", re.I), "ceramic"),
    (re.compile(r"leather", re.I), "leather"),
)

# Print / mesh interchange formats default to plastic when the stem is generic.
_EXT_HINTS: dict[str, str] = {
    ".stl": "abs plastic",
    ".3mf": "abs plastic",
    ".obj": "brushed metal",
    ".fbx": "brushed metal",
    ".glb": "brushed metal",
    ".gltf": "brushed metal",
    ".step": "brushed metal",
    ".stp": "brushed metal",
    ".iges": "brushed metal",
    ".igs": "brushed metal",
    ".brep": "brushed metal",
    ".brp": "brushed metal",
}

DEFAULT_QUERY = "brushed metal"


def normalize_name(text: str) -> str:
    return re.sub(r"[\s_\-]+", " ", text).strip()


def suggest_query_for_text(text: str) -> str | None:
    """Return a BlenderKit query if `text` matches a material hint."""
    if not text or not text.strip():
        return None
    haystack = normalize_name(text)
    for pattern, query in _NAME_HINTS:
        if pattern.search(haystack):
            return query
    return None


def suggest_query_for_path(filepath: str) -> str:
    """Guess a material query from a product filename and extension."""
    stem = os.path.splitext(os.path.basename(filepath))[0]
    hit = suggest_query_for_text(stem)
    if hit:
        return hit
    ext = os.path.splitext(filepath)[1].lower()
    return _EXT_HINTS.get(ext, DEFAULT_QUERY)
