# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD light naming — no Blender import."""

from __future__ import annotations

import re
from typing import Iterable

PREFIX = "BEHOLD"
COLLECTION_NAME = "BEHOLD_Studio"
RESERVED_RIG = (f"{PREFIX}_Key", f"{PREFIX}_Fill", f"{PREFIX}_Rim")

_INDEX_RE = {
    "Light": re.compile(rf"^{re.escape(PREFIX)}_Light_(\d+)$"),
    "Draw": re.compile(rf"^{re.escape(PREFIX)}_Draw_(\d+)$"),
}


def is_behold_light_name(name: str) -> bool:
    return name.startswith(f"{PREFIX}_")


def display_light_name(name: str) -> str:
    prefix = f"{PREFIX}_"
    if name.startswith(prefix):
        return name[len(prefix) :]
    return name


def next_indexed_name(existing_names: Iterable[str], kind: str) -> str:
    pattern = _INDEX_RE.get(kind)
    if pattern is None:
        raise ValueError(f"Unknown light kind: {kind}")
    highest = 0
    for name in existing_names:
        match = pattern.match(name)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{PREFIX}_{kind}_{highest + 1:03d}"
