# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene-level BEHOLD settings."""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup, Scene


class BEHOLDSceneSettings(PropertyGroup):
    studio_backdrop: EnumProperty(
        name="Backdrop",
        description="Studio backdrop style",
        items=(
            ("CYCLORAMA", "Cyclorama", "Seamless sweep for product shots"),
            ("SOLID", "Solid", "Flat infinite-looking solid color"),
            ("HDRI", "HDRI World", "Environment lighting (bring your own or BlenderKit)"),
        ),
        default="CYCLORAMA",
    )
    studio_light_rig: EnumProperty(
        name="Light Rig",
        description="Default light layout",
        items=(
            ("THREE_POINT", "Three Point", "Key, fill, and rim"),
            ("SOFTBOX", "Softbox", "Large soft key + fill"),
        ),
        default="THREE_POINT",
    )
    include_shadow_catcher: BoolProperty(
        name="Shadow Catcher",
        description="Add a ground plane that catches shadows",
        default=True,
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
    exposure_ev: FloatProperty(
        name="EV",
        description="Exposure compensation in stops",
        default=0.0,
        min=-6.0,
        max=6.0,
    )
    turntable_frames: IntProperty(
        name="Turntable Frames",
        description="Frame count for a full 360° turntable",
        default=120,
        min=24,
        max=360,
    )
    blenderkit_query: StringProperty(
        name="BlenderKit Search",
        description="Search query for BlenderKit materials",
        default="brushed metal",
        maxlen=256,
    )
    false_color: BoolProperty(
        name="False Color",
        description="Toggle false-color look for exposure checks",
        default=False,
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
    white_balance_kelvin: FloatProperty(
        name="White Balance",
        description="Scene white-balance temperature in Kelvin (view look)",
        default=6500.0,
        min=2000.0,
        max=10000.0,
        subtype="TEMPERATURE",
    )
    render_quality: EnumProperty(
        name="Quality",
        description="Cycles sample / denoise preset for product shots",
        items=(
            ("DRAFT", "Draft", "Fast look-dev (32 samples)"),
            ("PRODUCT", "Product", "Client-ready stills (128 samples)"),
            ("HERO", "Hero", "Chrome / glass hero shots (512 samples)"),
        ),
        default="PRODUCT",
    )
    output_directory: StringProperty(
        name="Output Folder",
        description="Render folder. Tokens: {angle} {camera} {quality}",
        default="//behold_out/",
        subtype="DIR_PATH",
        maxlen=1024,
    )
    main_camera_name: StringProperty(
        name="Main Camera",
        description="Bookmarked BEHOLD camera object name",
        default="",
        maxlen=128,
    )
    import_auto_studio: BoolProperty(
        name="Build Studio after Import",
        description="Run Build Studio on meshes created by Import Product",
        default=True,
    )
    import_auto_material_assist: BoolProperty(
        name="Material Assist after Import",
        description="Guess a BlenderKit query from the product filename and part names",
        default=True,
    )


CLASSES = (BEHOLDSceneSettings,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    Scene.behold = PointerProperty(type=BEHOLDSceneSettings)


def unregister() -> None:
    del Scene.behold
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
