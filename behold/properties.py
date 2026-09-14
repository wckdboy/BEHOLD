# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene-level BEHOLD settings."""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup, Scene

from .shoot.exposure_apply import on_exposure_update
from .studio.light_presets import DEFAULT_PRESET as LIGHT_SHAPE_DEFAULT
from .studio.light_presets import preset_enum_items as light_shape_enum_items
from .studio.world_apply import on_hdri_filepath_update, on_hdri_values_update


class BEHOLDShotItem(PropertyGroup):
    """Named shoot preset stored on the scene (survives save / reload)."""

    name: StringProperty(
        name="Shot",
        description="Shot name",
        default="Shot",
        maxlen=128,
    )
    camera_name: StringProperty(
        name="Camera",
        description="Active / bookmarked camera object name",
        default="",
        maxlen=128,
    )
    main_camera_name: StringProperty(
        name="Main Camera",
        description="Bookmarked camera object name at save time",
        default="",
        maxlen=128,
    )
    render_quality: EnumProperty(
        name="Quality",
        description="Cycles sample preset stored with this shot",
        items=(
            ("DRAFT", "Draft", "Fast look-dev (32 samples)"),
            ("FINAL", "Final", "First-ship client still (256 samples)"),
            ("PRODUCT", "Product", "Client-ready stills (128 samples)"),
            ("HERO", "Hero", "Chrome / glass hero shots (512 samples)"),
        ),
        default="DRAFT",
    )
    turntable_seconds: FloatProperty(
        name="Turntable Seconds",
        description="Turntable duration stored with this shot",
        default=6.0,
        min=1.0,
        max=60.0,
        step=10,
        precision=1,
    )
    hdri_filepath: StringProperty(
        name="HDRI",
        description="World environment image path stored with this shot",
        default="",
        subtype="FILE_PATH",
        maxlen=1024,
    )
    hdri_strength: FloatProperty(
        name="HDRI Strength",
        default=1.0,
        min=0.0,
        max=100.0,
    )
    hdri_rotation: FloatProperty(
        name="HDRI Rotation",
        description="HDRI Z rotation in degrees",
        default=0.0,
        min=-360.0,
        max=360.0,
        step=100,
        precision=1,
    )
    hdri_reflections_only: BoolProperty(
        name="Reflections only",
        default=False,
    )
    hdri_background_strength: FloatProperty(
        name="HDRI Background",
        default=0.0,
        min=0.0,
        max=100.0,
    )
    studio_backdrop_tone: EnumProperty(
        name="Backdrop",
        items=(
            ("WHITE", "White", "Bright product sweep"),
            ("GREY", "Grey", "Neutral product sweep"),
            ("BLACK", "Black", "Dark product sweep"),
        ),
        default="WHITE",
    )
    output_directory: StringProperty(
        name="Output Folder",
        description="Render folder token template stored with this shot",
        default="//behold_out/",
        subtype="DIR_PATH",
        maxlen=1024,
    )


class BEHOLDSceneSettings(PropertyGroup):
    studio_backdrop_tone: EnumProperty(
        name="Backdrop",
        description="First-ship sweep / solid backdrop tone",
        items=(
            ("WHITE", "White", "Bright product sweep"),
            ("GREY", "Grey", "Neutral product sweep"),
            ("BLACK", "Black", "Dark product sweep"),
        ),
        default="WHITE",
    )
    studio_backdrop: EnumProperty(
        name="Backdrop Type",
        description="Studio backdrop style (Advanced)",
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
    studio_margin: FloatProperty(
        name="Studio Margin",
        description="Cyclorama floor scale vs product XY diagonal (Build Studio)",
        default=2.0,
        min=1.0,
        max=4.0,
        soft_min=1.5,
        soft_max=2.5,
        step=10,
        precision=2,
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
        description="Exposure compensation in stops (Color Management)",
        default=0.0,
        min=-6.0,
        max=6.0,
        step=10,
        precision=2,
        update=on_exposure_update,
    )
    turntable_seconds: FloatProperty(
        name="Seconds",
        description="Turntable duration. Default 6 s (144 frames at 24 fps) for a 360° loop",
        default=6.0,
        min=1.0,
        max=60.0,
        step=10,
        precision=1,
    )
    turntable_interpolation: EnumProperty(
        name="Spin",
        description="Linear is a constant loop-friendly spin. Ease is a one-shot in/out",
        items=(
            ("LINEAR", "Linear", "Constant 360° spin, loop-friendly"),
            ("EASE", "Ease", "Ease in/out — one-shot spin, not a loop"),
        ),
        default="LINEAR",
    )
    turntable_frames: IntProperty(
        name="Turntable Frames",
        description="Frame count written at Setup from seconds × scene fps (6 s × 24 fps = 144)",
        default=144,
        min=24,
        max=3600,
    )
    blenderkit_query: StringProperty(
        name="BlenderKit Search",
        description="Search query for BlenderKit materials",
        default="brushed metal",
        maxlen=256,
    )
    false_color: BoolProperty(
        name="False Color",
        description="AgX-safe false-color heat map for exposure checks",
        default=False,
        update=on_exposure_update,
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
        description="Scene white-balance temperature in Kelvin (Color Management)",
        default=6500.0,
        min=2000.0,
        max=10000.0,
        subtype="TEMPERATURE",
        update=on_exposure_update,
    )
    view_transform_restore: StringProperty(
        name="Saved View Transform",
        description="View transform restored when False Color turns off",
        default="AgX",
        maxlen=64,
    )
    render_quality: EnumProperty(
        name="Quality",
        description="Cycles sample / denoise preset for product shots",
        items=(
            ("DRAFT", "Draft", "Fast look-dev (32 samples)"),
            ("FINAL", "Final", "First-ship client still (256 samples)"),
            ("PRODUCT", "Product", "Client-ready stills (128 samples)"),
            ("HERO", "Hero", "Chrome / glass hero shots (512 samples)"),
        ),
        default="DRAFT",
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
        description=(
            "Apply a local product look from the filename and part names. "
            "Searches BlenderKit only when signed in — no account needed locally"
        ),
        default=True,
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
    active_camera_name: StringProperty(
        name="Active Camera",
        description="BEHOLD camera used by Shoot still / batch / turntable",
        default="",
        maxlen=128,
    )
    new_camera_lens: FloatProperty(
        name="New Camera Lens",
        description="Focal length in mm for cameras created with Add Camera",
        default=85.0,
        min=12.0,
        max=300.0,
    )
    hdri_filepath: StringProperty(
        name="HDRI",
        description="World environment image (HDR / EXR from OpenHDRI, Poly Haven, or disk)",
        default="",
        subtype="FILE_PATH",
        maxlen=1024,
        update=on_hdri_filepath_update,
    )
    hdri_strength: FloatProperty(
        name="Strength",
        description="HDRI lighting / reflection strength",
        default=1.0,
        min=0.0,
        soft_max=5.0,
        max=100.0,
        update=on_hdri_values_update,
    )
    hdri_rotation: FloatProperty(
        name="Rotation",
        description="Rotate the HDRI around Z, in degrees",
        default=0.0,
        min=-360.0,
        max=360.0,
        step=100,
        precision=1,
        update=on_hdri_values_update,
    )
    hdri_reflections_only: BoolProperty(
        name="Reflections only",
        description=(
            "Keep the HDRI in reflections and lighting, and use Background "
            "strength for what the camera sees (Cycles and EEVEE)"
        ),
        default=False,
        update=on_hdri_values_update,
    )
    hdri_background_strength: FloatProperty(
        name="Background",
        description="Camera-visible HDRI strength when Reflections only is on (0 hides it)",
        default=0.0,
        min=0.0,
        soft_max=5.0,
        max=100.0,
        update=on_hdri_values_update,
    )
    shots: CollectionProperty(
        type=BEHOLDShotItem,
        name="Shots",
        description="Named shoot presets (camera, quality, HDRI, backdrop, output)",
    )
    active_shot_index: IntProperty(
        name="Active Shot",
        description="Index of the last applied or saved shot",
        default=-1,
        min=-1,
    )


CLASSES = (BEHOLDShotItem, BEHOLDSceneSettings)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    Scene.behold = PointerProperty(type=BEHOLDSceneSettings)


def unregister() -> None:
    del Scene.behold
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
