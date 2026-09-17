# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene-level BEHOLD Studio settings."""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup, Scene

from .bake import DEFAULT_RESOLUTION as BAKE_DEFAULT_RESOLUTION
from .bake import resolution_enum_items as bake_resolution_enum_items
from .catcher_apply import on_catcher_update
from .world_apply import on_hdri_filepath_update, on_hdri_values_update


class BEHOLDStudioSettings(PropertyGroup):
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

    include_shadow_catcher: BoolProperty(
        name="Catcher",
        description=(
            "Ground contact after Build: soft contact on the cyclorama, "
            "or a Cycles shadow-catcher plane (EEVEE fallback) for Solid / HDRI"
        ),
        default=True,
        update=on_catcher_update,
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

    bake_hdri_filepath: StringProperty(
        name="Bake HDRI",
        description=(
            "Output path for the baked equirectangular HDR/EXR. "
            "Empty uses the folder next to the .blend, or a temp path"
        ),
        default="",
        subtype="FILE_PATH",
        maxlen=1024,
    )

    bake_hdri_resolution: EnumProperty(
        name="Bake Size",
        description="Equirectangular resolution (2:1)",
        items=bake_resolution_enum_items(),
        default=BAKE_DEFAULT_RESOLUTION,
    )

    bake_hdri_include_world: BoolProperty(
        name="Include world",
        description="Bake the current world together with studio lights",
        default=False,
    )

    bake_hdri_apply: BoolProperty(
        name="Apply after bake",
        description="Load the baked HDRI as the scene world when the render finishes",
        default=False,
    )


CLASSES = (BEHOLDStudioSettings,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    Scene.behold_studio = PointerProperty(type=BEHOLDStudioSettings)


def unregister() -> None:
    del Scene.behold_studio
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
