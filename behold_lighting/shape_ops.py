# SPDX-License-Identifier: GPL-3.0-or-later
"""Lighting Shape operators — softbox / area looks on the active light."""

from __future__ import annotations

import bpy
from bpy.props import EnumProperty
from bpy.types import Context, Operator

from . import light_presets
from . import light_shape
from .common.messages import NO_LIGHTS, report_set, unknown_light_preset_message


class BEHOLD_OT_apply_light_preset(Operator):
    bl_idname = "behold.apply_light_preset"
    bl_label = "Apply Light Shape"
    bl_description = (
        "Apply a softbox / area look to the active BEHOLD light "
        "(adds a light if the studio has none)"
    )
    bl_options = {"REGISTER", "UNDO"}

    preset: EnumProperty(
        name="Shape",
        items=light_presets.preset_enum_items(),
        default=light_presets.DEFAULT_PRESET,
    )

    def execute(self, context: Context):
        preset = light_presets.get_preset(self.preset)
        if preset is None:
            message = unknown_light_preset_message(self.preset)
            self.report(report_set(message), message)
            return {"CANCELLED"}
        result = light_shape.apply_preset_in_scene(context, preset.id)
        if not result["ok"]:
            message = NO_LIGHTS if result["message"] == "NO_LIGHTS" else result["message"]
            self.report(report_set(message), message)
            return {"CANCELLED"}
        context.scene.behold_lighting.light_shape_preset = preset.id
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


CLASSES = (BEHOLD_OT_apply_light_preset,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
