# SPDX-License-Identifier: GPL-3.0-or-later
"""Studio operators: Build, HDRI world, bake, catcher."""

from __future__ import annotations

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ImportHelper

from . import bake_apply
from . import catcher_apply
from . import setup as studio_setup
from . import world as world_lib
from . import world_apply
from .common.messages import NO_MESH_SELECTED, report_set
from .common.tones import backdrop_tone_rgba


class BEHOLD_OT_build_studio(Operator):
    bl_idname = "behold.build_studio"
    bl_label = "Build Studio"
    bl_description = "Create the cyclorama, world, and catcher around the selection"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        message = studio_setup.build_studio(context)
        if message in (studio_setup.BUILD_NEEDS_MESH, NO_MESH_SELECTED):
            self.report(report_set(NO_MESH_SELECTED), NO_MESH_SELECTED)
            return {"CANCELLED"}
        self.report({"INFO"}, message)
        return {"FINISHED"}


class BEHOLD_OT_load_hdri(Operator, ImportHelper):
    bl_idname = "behold.load_hdri"
    bl_label = "Load HDRI"
    bl_description = (
        "Load a world HDRI (OpenHDRI, Poly Haven, or disk) and wire strength / rotation"
    )
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".hdr"
    filter_glob: StringProperty(
        default=world_lib.HDRI_FILTER_GLOB,
        options={"HIDDEN"},
    )

    def execute(self, context: Context):
        settings = context.scene.behold_studio
        settings.hdri_filepath = self.filepath
        result = world_apply.apply_hdri_from_settings(context)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


class BEHOLD_OT_reset_world(Operator):
    bl_idname = "behold.reset_world"
    bl_label = "Reset World"
    bl_description = "Clear the HDRI and restore a solid studio world"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        result = world_apply.reset_world(context)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


class BEHOLD_OT_bake_hdri(Operator):
    bl_idname = "behold.bake_hdri"
    bl_label = "Bake HDRI"
    bl_description = (
        "Render BEHOLD studio lights (and optional world) to an "
        "equirectangular HDR/EXR"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        result = bake_apply.bake_studio_hdri(context)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


class BEHOLD_OT_apply_catcher(Operator):
    bl_idname = "behold.apply_catcher"
    bl_label = "Apply Catcher"
    bl_description = (
        "Apply ground contact: soft contact on the cyclorama, or a "
        "Cycles shadow-catcher plane (EEVEE fallback) for Solid / HDRI"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        result = catcher_apply.apply_ground_contact(context)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


class BEHOLD_OT_apply_studio_look(Operator):
    bl_idname = "behold.apply_studio_look"
    bl_label = "Apply Studio Look"
    bl_description = "Load the HDRI and retint the cyclorama from the current studio settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        settings = context.scene.behold_studio
        if getattr(settings, "hdri_filepath", ""):
            result = world_apply.apply_hdri_from_settings(context)
            if not result["ok"]:
                self.report(report_set(result["message"]), result["message"])
                return {"CANCELLED"}
        else:
            world_apply.setup_solid_world(context.scene)
        tone = backdrop_tone_rgba(settings)
        mat = bpy.data.materials.get("BEHOLD_Sweep")
        if mat is not None and getattr(mat, "use_nodes", False) and mat.node_tree is not None:
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            if bsdf is not None and "Base Color" in bsdf.inputs:
                bsdf.inputs["Base Color"].default_value = tone
        self.report({"INFO"}, "Studio look applied")
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_build_studio,
    BEHOLD_OT_load_hdri,
    BEHOLD_OT_reset_world,
    BEHOLD_OT_bake_hdri,
    BEHOLD_OT_apply_catcher,
    BEHOLD_OT_apply_studio_look,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
