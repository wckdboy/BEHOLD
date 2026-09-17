# SPDX-License-Identifier: GPL-3.0-or-later
"""Lighting IES operators — load / sample / apply / clear photometric profiles."""

from __future__ import annotations

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ImportHelper

from . import ies as ies_lib
from . import ies_apply
from .common.messages import report_set


class BEHOLD_OT_load_ies(Operator, ImportHelper):
    bl_idname = "behold.load_ies"
    bl_label = "Load IES"
    bl_description = (
        "Load a photometric .ies profile onto the active BEHOLD spot or point "
        "light (area lights become spots while IES is on)"
    )
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".ies"
    filter_glob: StringProperty(
        default=ies_lib.IES_FILTER_GLOB,
        options={"HIDDEN"},
    )

    def execute(self, context: Context):
        settings = context.scene.behold_lighting
        settings.light_ies_filepath = self.filepath
        result = ies_apply.apply_ies_in_scene(context)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


class BEHOLD_OT_load_ies_sample(Operator):
    bl_idname = "behold.load_ies_sample"
    bl_label = "Sample IES"
    bl_description = (
        "Load the bundled CC0 sample spot IES onto the active BEHOLD light. "
        "Bring your own .ies for a real fixture"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        path = ies_lib.bundled_sample_path()
        settings = context.scene.behold_lighting
        settings.light_ies_filepath = path
        result = ies_apply.apply_ies_in_scene(context)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


class BEHOLD_OT_clear_ies(Operator):
    bl_idname = "behold.clear_ies"
    bl_label = "Clear IES"
    bl_description = (
        "Remove the IES profile and restore the light's prior type, Shape, and Gobo"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        result = ies_apply.teardown_ies_in_scene(context)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


class BEHOLD_OT_apply_ies(Operator):
    bl_idname = "behold.apply_ies"
    bl_label = "Apply IES"
    bl_description = (
        "Apply the IES path / strength / scale on the active BEHOLD light. "
        "Clear tears the graph down"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        result = ies_apply.apply_ies_in_scene(context)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_load_ies,
    BEHOLD_OT_load_ies_sample,
    BEHOLD_OT_clear_ies,
    BEHOLD_OT_apply_ies,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
