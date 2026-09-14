# SPDX-License-Identifier: GPL-3.0-or-later
"""Single-pass N-panel scene flags — no Blender import.

``flow_state_from_context`` used to walk ``scene.objects`` three times plus
separate light and camera iterators. Draw only needs booleans. Build a snap
from typed rows so tests cover the reducer without bpy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .flow import product_present, studio_present


@dataclass(frozen=True)
class ObjectDrawRow:
    name: str
    ob_type: str
    tagged_product: bool = False
    has_look: bool = False
    selected: bool = False
    is_behold_light: bool = False
    is_behold_camera: bool = False


@dataclass(frozen=True)
class SceneDrawSnap:
    has_product: bool
    has_studio: bool
    has_look: bool
    has_camera: bool
    has_selected_mesh: bool
    has_tagged_product: bool

    @property
    def has_imported_product(self) -> bool:
        """Tagged product mesh — same as the old ``_has_imported_product``."""
        return self.has_tagged_product


def snap_from_rows(
    rows: Iterable[ObjectDrawRow],
    *,
    has_scene_camera: bool,
) -> SceneDrawSnap:
    """Reduce object rows to the flags N-panel draw needs."""
    mesh_names: list[str] = []
    tagged = False
    has_look = False
    has_light = False
    has_behold_cam = False
    has_selected_mesh = False
    for row in rows:
        if row.ob_type == "MESH":
            mesh_names.append(row.name)
            tagged = tagged or row.tagged_product
            has_look = has_look or row.has_look
            has_selected_mesh = has_selected_mesh or row.selected
        if row.is_behold_light:
            has_light = True
        if row.is_behold_camera:
            has_behold_cam = True
    return SceneDrawSnap(
        has_product=product_present(
            mesh_names=mesh_names, tagged_product=tagged
        ),
        has_studio=studio_present(
            mesh_names=mesh_names, has_behold_light=has_light
        ),
        has_look=has_look,
        has_camera=has_behold_cam or has_scene_camera,
        has_selected_mesh=has_selected_mesh,
        has_tagged_product=tagged,
    )
