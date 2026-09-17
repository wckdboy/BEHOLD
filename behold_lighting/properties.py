# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene-level BEHOLD Lighting settings."""

from __future__ import annotations

import bpy
from bpy.props import EnumProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup, Scene

from .gobo_apply import on_gobo_update
from .gobos import DEFAULT_PRESET as LIGHT_GOBO_DEFAULT
from .gobos import DEFAULT_SCALE as LIGHT_GOBO_SCALE_DEFAULT
from .gobos import DEFAULT_STRENGTH as LIGHT_GOBO_STRENGTH_DEFAULT
from .gobos import MAX_SCALE as LIGHT_GOBO_SCALE_MAX
from .gobos import MIN_SCALE as LIGHT_GOBO_SCALE_MIN
from .gobos import preset_enum_items as light_gobo_enum_items
from .ies import DEFAULT_SCALE as LIGHT_IES_SCALE_DEFAULT
from .ies import DEFAULT_STRENGTH as LIGHT_IES_STRENGTH_DEFAULT
from .ies import MAX_SCALE as LIGHT_IES_SCALE_MAX
from .ies import MAX_STRENGTH as LIGHT_IES_STRENGTH_MAX
from .ies import MIN_SCALE as LIGHT_IES_SCALE_MIN
from .ies_apply import on_ies_filepath_update, on_ies_values_update
from .light_linking import DEFAULT_KIND as LIGHT_LINKING_DEFAULT
from .light_linking import kind_enum_items as light_linking_kind_enum_items
from .light_presets import DEFAULT_PRESET as LIGHT_SHAPE_DEFAULT
from .light_presets import preset_enum_items as light_shape_enum_items


class BEHOLDLightingSettings(PropertyGroup):
    studio_light_rig: EnumProperty(
        name="Light Rig",
        description="Default light layout",
        items=(
            ("THREE_POINT", "Three Point", "Key, fill, and rim"),
            ("SOFTBOX", "Softbox", "Large soft key + fill"),
        ),
        default="THREE_POINT",
    )

    key_power: FloatProperty(
        name="Key Power",
        description="Key light strength multiplier",
        default=1.0,
        min=0.0,
        soft_max=5.0,
    )

    fill_ratio: FloatProperty(
        name="Fill Ratio",
        description="Fill light as a fraction of key",
        default=0.35,
        min=0.0,
        max=2.0,
    )

    rim_ratio: FloatProperty(
        name="Rim Ratio",
        description="Rim / back light as a fraction of key",
        default=0.55,
        min=0.0,
        max=2.0,
    )

    light_temperature: FloatProperty(
        name="Temperature",
        description="Shared light color temperature in Kelvin",
        default=5500.0,
        min=1000.0,
        max=12000.0,
        subtype="TEMPERATURE",
    )

    light_draw_mode: EnumProperty(
        name="Light Draw Mode",
        description="Placement mode for Light Draw",
        items=(
            ("REFLECT", "Reflect", "Place light for a specular highlight under the cursor"),
            ("DIRECT", "Direct", "Place light along the surface normal"),
            ("ORBIT", "Orbit", "Orbit the active light around a pinned target"),
        ),
        default="REFLECT",
    )

    light_draw_distance: FloatProperty(
        name="Light Distance",
        description="Distance from surface hit to light in Light Draw",
        default=2.0,
        min=0.1,
        soft_max=20.0,
        unit="LENGTH",
    )

    active_light_name: StringProperty(
        name="Active Light",
        description="BEHOLD light used by Light Draw and the intensity list",
        default="",
        maxlen=128,
    )

    new_light_energy: FloatProperty(
        name="New Light Power",
        description="Default wattage for lights created with Add Light / Light Draw",
        default=200.0,
        min=0.01,
        soft_max=2000.0,
    )

    light_draw_target: EnumProperty(
        name="Light Draw Target",
        description="Whether Light Draw moves the active light or creates a new one",
        items=(
            ("ACTIVE", "Active", "Move and aim the active BEHOLD light"),
            ("NEW", "New", "Create a new BEHOLD light and aim it"),
        ),
        default="ACTIVE",
    )

    light_shape_preset: EnumProperty(
        name="Shape",
        description="Softbox / area look applied to the active BEHOLD light",
        items=light_shape_enum_items(),
        default=LIGHT_SHAPE_DEFAULT,
    )

    light_gobo_preset: EnumProperty(
        name="Gobo",
        description="Procedural gobo on the active BEHOLD area / spot light",
        items=light_gobo_enum_items(),
        default=LIGHT_GOBO_DEFAULT,
        update=on_gobo_update,
    )

    light_gobo_scale: FloatProperty(
        name="Gobo Scale",
        description="Repeat / size of the gobo pattern on the active light",
        default=LIGHT_GOBO_SCALE_DEFAULT,
        min=LIGHT_GOBO_SCALE_MIN,
        max=LIGHT_GOBO_SCALE_MAX,
        soft_min=0.25,
        soft_max=4.0,
        step=10,
        precision=2,
        update=on_gobo_update,
    )

    light_gobo_strength: FloatProperty(
        name="Gobo Strength",
        description="How hard the gobo cuts (0 = open, 1 = full pattern)",
        default=LIGHT_GOBO_STRENGTH_DEFAULT,
        min=0.0,
        max=1.0,
        subtype="FACTOR",
        update=on_gobo_update,
    )

    light_ies_filepath: StringProperty(
        name="IES",
        description="Photometric .ies profile on the active BEHOLD spot / point light",
        default="",
        subtype="FILE_PATH",
        maxlen=1024,
        update=on_ies_filepath_update,
    )

    light_ies_strength: FloatProperty(
        name="IES Strength",
        description="IES intensity multiplier on the active light (Cycles IES Strength)",
        default=LIGHT_IES_STRENGTH_DEFAULT,
        min=0.0,
        max=LIGHT_IES_STRENGTH_MAX,
        soft_max=4.0,
        step=10,
        precision=2,
        update=on_ies_values_update,
    )

    light_ies_scale: FloatProperty(
        name="IES Scale",
        description="Zoom the IES distribution on the active light",
        default=LIGHT_IES_SCALE_DEFAULT,
        min=LIGHT_IES_SCALE_MIN,
        max=LIGHT_IES_SCALE_MAX,
        soft_min=0.25,
        soft_max=4.0,
        step=10,
        precision=2,
        update=on_ies_values_update,
    )

    light_linking_kind: EnumProperty(
        name="Linking",
        description="Light linking (who is lit) or shadow linking (who casts)",
        items=light_linking_kind_enum_items(),
        default=LIGHT_LINKING_DEFAULT,
    )


CLASSES = (BEHOLDLightingSettings,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    Scene.behold_lighting = PointerProperty(type=BEHOLDLightingSettings)


def unregister() -> None:
    del Scene.behold_lighting
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
