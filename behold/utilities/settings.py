# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene settings for the feature-flagged Utilities panel."""

from __future__ import annotations

from bpy.props import BoolProperty, EnumProperty, FloatProperty
from bpy.types import PropertyGroup

from .mounts import DEFAULT_INSET_M, DEFAULT_LEG_HEIGHT_M
from .wall import (
    DEFAULT_DOOR_HEIGHT_M,
    DEFAULT_DOOR_WIDTH_M,
    DEFAULT_HEIGHT_M,
    DEFAULT_WIDTH_M,
    FOUNDATION_DEFAULT_MM,
    FOUNDATION_MAX_MM,
    FOUNDATION_MIN_MM,
    storey_enum_items,
)


class BEHOLDUtilitiesSettings(PropertyGroup):
    storey: EnumProperty(
        name="Storey",
        description="Danish wall thickness preset (foundation 600–700 mm, mid 480, top 360)",
        items=storey_enum_items(),
        default="MID",
    )
    wall_width: FloatProperty(
        name="Width",
        description="Wall width along the facade",
        default=DEFAULT_WIDTH_M,
        min=0.5,
        soft_max=12.0,
        unit="LENGTH",
    )
    wall_height: FloatProperty(
        name="Height",
        description="Wall height",
        default=DEFAULT_HEIGHT_M,
        min=0.5,
        soft_max=8.0,
        unit="LENGTH",
    )
    foundation_mm: FloatProperty(
        name="Foundation mm",
        description="Foundation / bottom thickness in millimetres (600–700, default 700)",
        default=FOUNDATION_DEFAULT_MM,
        min=FOUNDATION_MIN_MM,
        max=FOUNDATION_MAX_MM,
        step=100,
        precision=0,
    )
    exterior_mm: FloatProperty(
        name="Masonry mm",
        description="Exterior masonry thickness in millimetres (0 = storey default)",
        default=0.0,
        min=0.0,
        max=400.0,
        step=100,
        precision=0,
    )
    interior_mm: FloatProperty(
        name="Plaster mm",
        description="Interior plaster thickness in millimetres (0 = 13 mm default)",
        default=0.0,
        min=0.0,
        max=80.0,
        step=10,
        precision=0,
    )
    include_door: BoolProperty(
        name="Door opening",
        description="Cut a balcony-door opening through the wall layers",
        default=False,
    )
    door_width: FloatProperty(
        name="Door width",
        description="Balcony door opening width",
        default=DEFAULT_DOOR_WIDTH_M,
        min=0.6,
        max=2.4,
        unit="LENGTH",
    )
    door_height: FloatProperty(
        name="Door height",
        description="Balcony door opening height",
        default=DEFAULT_DOOR_HEIGHT_M,
        min=1.8,
        max=3.0,
        unit="LENGTH",
    )
    leg_height: FloatProperty(
        name="Leg height",
        description="Front post height when the product sits on the floor",
        default=DEFAULT_LEG_HEIGHT_M,
        min=0.5,
        soft_max=6.0,
        unit="LENGTH",
    )
    mount_inset: FloatProperty(
        name="Inset",
        description="Offset of posts / brackets from the balcony ends",
        default=DEFAULT_INSET_M,
        min=0.05,
        max=1.0,
        unit="LENGTH",
    )
