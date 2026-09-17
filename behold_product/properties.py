# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene-level BEHOLD Product settings."""

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

from .cad.defeaturing import DEFAULT_BLEND_MM as CAD_BLEND_DEFAULT
from .cad.defeaturing import DEFAULT_HOLE_MM as CAD_HOLE_DEFAULT
from .cad.defeaturing import MAX_SIZE_MM as CAD_SIZE_MAX
from .cad.defeaturing import MIN_SIZE_MM as CAD_SIZE_MIN
from .cad.regenerate import DEFAULT_DEFLECTION as CAD_DEFAULT_DEFLECTION
from .cad.regenerate import DEFAULT_QUALITY as CAD_QUALITY_DEFAULT
from .cad.regenerate import MAX_DEFLECTION as CAD_DEFLECTION_MAX
from .cad.regenerate import MIN_DEFLECTION as CAD_DEFLECTION_MIN
from .cad.regenerate import quality_enum_items as cad_quality_enum_items
from .dof import DEFAULT_FSTOP as DOF_DEFAULT_FSTOP
from .dof import FSTOP_MAX as DOF_FSTOP_MAX
from .dof import FSTOP_MIN as DOF_FSTOP_MIN
from .dof_apply import on_dof_update
from .shoot.exposure_apply import on_exposure_update
from .shoot.looks import DEFAULT_PRESET as LOOK_DEFAULT
from .shoot.looks import preset_enum_items as look_preset_enum_items
from .shoot.looks_apply import on_look_update
from .shoot.quality import DEFAULT_QUALITY as QUALITY_DEFAULT
from .shoot.quality import quality_enum_items
from .shoot.quality_apply import on_quality_update
from .shoot.resolution import DEFAULT_ASPECT as RESOLUTION_ASPECT_DEFAULT
from .shoot.resolution import DEFAULT_SIZE as RESOLUTION_SIZE_DEFAULT
from .shoot.resolution import aspect_enum_items as resolution_aspect_enum_items
from .shoot.resolution import size_enum_items as resolution_size_enum_items
from .shoot.resolution_apply import on_resolution_update


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
        description="Draft = EEVEE Next; Final / Product / Hero = Cycles",
        items=quality_enum_items(),
        default=QUALITY_DEFAULT,
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


class BEHOLDProductSettings(PropertyGroup):
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

    look_preset: EnumProperty(
        name="Look",
        description="Compositor still look: Clean, Catalog, or Dramatic",
        items=look_preset_enum_items(),
        default=LOOK_DEFAULT,
        update=on_look_update,
    )

    look_enabled: BoolProperty(
        name="Compositor",
        description="Apply the Look preset through the compositor (vignette / grain)",
        default=False,
        update=on_look_update,
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
        description="Draft = EEVEE Next look-dev; Final / Product / Hero = Cycles stills",
        items=quality_enum_items(),
        default=QUALITY_DEFAULT,
        update=on_quality_update,
    )

    resolution_aspect: EnumProperty(
        name="Aspect",
        description="Catalog still aspect: Square 1:1, Portrait 4:5, Landscape 16:9",
        items=resolution_aspect_enum_items(),
        default=RESOLUTION_ASPECT_DEFAULT,
        update=on_resolution_update,
    )

    resolution_size: EnumProperty(
        name="Size",
        description="Long-edge pixel size: 2048², 1080p, or 4K",
        items=resolution_size_enum_items(),
        default=RESOLUTION_SIZE_DEFAULT,
        update=on_resolution_update,
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
        name="Dress after Import",
        description=(
            "Optional. After CAD import, Auto-dress each body. Mesh files get "
            "one Assist look. Off by default — Import is import; dress on Materials"
        ),
        default=False,
    )

    cad_source_filepath: StringProperty(
        name="CAD Source",
        description="Last imported STEP / IGES / BREP path (Regenerate uses this)",
        default="",
        subtype="FILE_PATH",
        maxlen=1024,
    )

    cad_source_backend: StringProperty(
        name="CAD Backend",
        description="Backend that imported the cached CAD (STEPPER or OCP)",
        default="",
        maxlen=16,
    )

    cad_quality: EnumProperty(
        name="Quality",
        description=(
            "Tessellation quality for Regenerate. Draft / Balanced / Fine / Ultra "
            "match STEPper NEXT physical deflection; Custom uses the slider"
        ),
        items=cad_quality_enum_items(),
        default=CAD_QUALITY_DEFAULT,
    )

    cad_deflection: FloatProperty(
        name="Deflection",
        description=(
            "Linear deflection in meters when Quality is Custom. "
            "OCP uses it directly; STEPper gets lin_deflection_len on Custom"
        ),
        default=CAD_DEFAULT_DEFLECTION,
        min=CAD_DEFLECTION_MIN,
        max=CAD_DEFLECTION_MAX,
        soft_min=0.00005,
        soft_max=0.002,
        precision=5,
        step=1,
    )

    cad_cleanup_fillets: BoolProperty(
        name="Fillets",
        description=(
            "Suppress small constant-radius fillets (cylinders / tori / spheres) "
            "before tessellate. OCP only — STEPper NEXT has no cleanup RNA"
        ),
        default=False,
    )

    cad_cleanup_chamfers: BoolProperty(
        name="Chamfers",
        description=(
            "Suppress small planar chamfer strips before tessellate. "
            "OCP only — STEPper NEXT has no cleanup RNA"
        ),
        default=False,
    )

    cad_cleanup_holes: BoolProperty(
        name="Holes",
        description=(
            "Suppress small cylindrical holes and inner loops before tessellate. "
            "OCP only — STEPper NEXT has no cleanup RNA"
        ),
        default=False,
    )

    cad_blend_mm: FloatProperty(
        name="Blend",
        description="Fillet radius / chamfer width to suppress, in millimetres",
        default=CAD_BLEND_DEFAULT,
        min=CAD_SIZE_MIN,
        max=CAD_SIZE_MAX,
        soft_min=0.5,
        soft_max=10.0,
        precision=2,
        step=10,
    )

    cad_hole_mm: FloatProperty(
        name="Hole Ø",
        description="Hole diameter to suppress, in millimetres",
        default=CAD_HOLE_DEFAULT,
        min=CAD_SIZE_MIN,
        max=CAD_SIZE_MAX,
        soft_min=0.5,
        soft_max=12.0,
        precision=2,
        step=10,
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

    dof_enabled: BoolProperty(
        name="DoF",
        description="Enable depth of field on the active BEHOLD camera",
        default=False,
        update=on_dof_update,
    )

    dof_fstop: FloatProperty(
        name="f-stop",
        description="Aperture f-stop on the active BEHOLD camera (product default f/5.6)",
        default=DOF_DEFAULT_FSTOP,
        min=DOF_FSTOP_MIN,
        max=DOF_FSTOP_MAX,
        soft_min=2.8,
        soft_max=11.0,
        precision=1,
        step=10,
        update=on_dof_update,
    )

    hdri_filepath: StringProperty(
        name="HDRI",
        description="World environment image (HDR / EXR from OpenHDRI, Poly Haven, or disk)",
        default="",
        subtype="FILE_PATH",
        maxlen=1024,
    )

    hdri_strength: FloatProperty(
        name="Strength",
        description="HDRI lighting / reflection strength",
        default=1.0,
        min=0.0,
        soft_max=5.0,
        max=100.0,
    )

    hdri_rotation: FloatProperty(
        name="Rotation",
        description="Rotate the HDRI around Z, in degrees",
        default=0.0,
        min=-360.0,
        max=360.0,
        step=100,
        precision=1,
    )

    hdri_reflections_only: BoolProperty(
        name="Reflections only",
        description=(
            "Keep the HDRI in reflections and lighting, and use Background "
            "strength for what the camera sees (Cycles and EEVEE)"
        ),
        default=False,
    )

    hdri_background_strength: FloatProperty(
        name="Background",
        description="Camera-visible HDRI strength when Reflections only is on (0 hides it)",
        default=0.0,
        min=0.0,
        soft_max=5.0,
        max=100.0,
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

    batch_include_angles: BoolProperty(
        name="Front / ¾ / Top",
        description="Include catalog stills: front, three-quarter, and top",
        default=True,
    )

    batch_include_shots: BoolProperty(
        name="Saved shots",
        description="Also render each Shot Manager preset as a still",
        default=False,
    )


CLASSES = (BEHOLDShotItem, BEHOLDProductSettings)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    Scene.behold_product = PointerProperty(type=BEHOLDProductSettings)


def unregister() -> None:
    del Scene.behold_product
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
