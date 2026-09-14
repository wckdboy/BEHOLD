# SPDX-License-Identifier: GPL-3.0-or-later
"""Studio operators: build, light mixer, multi-light CRUD."""

from __future__ import annotations

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator

from . import lights as light_lib
from . import setup as studio_setup


class BEHOLD_OT_build_studio(Operator):
    bl_idname = "behold.build_studio"
    bl_label = "Build Studio"
    bl_description = "Create lights, camera, and backdrop around the selection"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        message = studio_setup.build_studio(context)
        if message == studio_setup.BUILD_NEEDS_MESH:
            self.report({"ERROR"}, message)
            return {"CANCELLED"}
        self.report({"INFO"}, message)
        return {"FINISHED"}


class BEHOLD_OT_refresh_lights(Operator):
    bl_idname = "behold.refresh_lights"
    bl_label = "Apply Light Mixer"
    bl_description = "Push key/fill/rim and temperature to studio lights"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        if not light_lib.iter_behold_lights(context):
            self.report({"ERROR"}, "No BEHOLD lights — Build Studio or Add Light first")
            return {"CANCELLED"}
        count = studio_setup.refresh_light_mixer(context)
        self.report({"INFO"}, f"Light mixer applied ({count} light(s))")
        return {"FINISHED"}


class BEHOLD_OT_add_light(Operator):
    bl_idname = "behold.add_light"
    bl_label = "Add Light"
    bl_description = "Add another BEHOLD area light and make it active"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        light = light_lib.add_extra_light(context)
        self.report({"INFO"}, f"Added {light.name} ({light.data.energy:.0f} W)")
        return {"FINISHED"}


class BEHOLD_OT_remove_light(Operator):
    bl_idname = "behold.remove_light"
    bl_label = "Remove Light"
    bl_description = "Remove a BEHOLD light"
    bl_options = {"REGISTER", "UNDO"}

    light_name: StringProperty(name="Light", default="")

    def execute(self, context: Context):
        name = (self.light_name or "").strip()
        light = bpy.data.objects.get(name) if name else light_lib.get_active_behold_light(context)
        if light is None or not light_lib.is_behold_light(light):
            self.report({"ERROR"}, "Pick a BEHOLD light to remove")
            return {"CANCELLED"}
        removed = light.name
        light_lib.remove_behold_light(context, light)
        self.report({"INFO"}, f"Removed {removed}")
        return {"FINISHED"}


class BEHOLD_OT_set_active_light(Operator):
    bl_idname = "behold.set_active_light"
    bl_label = "Set Active Light"
    bl_description = "Make this the active light for Light Draw and intensity edits"
    bl_options = {"REGISTER", "UNDO"}

    light_name: StringProperty(name="Light", default="")

    def execute(self, context: Context):
        light = bpy.data.objects.get(self.light_name)
        if light is None or not light_lib.is_behold_light(light):
            self.report({"ERROR"}, f"Light “{self.light_name}” not found")
            return {"CANCELLED"}
        light_lib.set_active_behold_light(context, light)
        self.report({"INFO"}, f"Active light: {light.name}")
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_build_studio,
    BEHOLD_OT_refresh_lights,
    BEHOLD_OT_add_light,
    BEHOLD_OT_remove_light,
    BEHOLD_OT_set_active_light,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
