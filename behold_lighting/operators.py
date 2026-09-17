# SPDX-License-Identifier: GPL-3.0-or-later
"""Lighting inventory operators: seed, mixer, add / remove / set active."""

from __future__ import annotations

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator

from . import lights as light_lib
from . import setup_lights
from .common.messages import (
    NO_LIGHT_TO_REMOVE,
    NO_LIGHTS,
    light_not_found,
    report_set,
)


class BEHOLD_OT_seed_studio_lights(Operator):
    bl_idname = "behold.seed_studio_lights"
    bl_label = "Seed Studio Lights"
    bl_description = "Create Key / Fill / Rim around the selected product"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context: Context):
        count = setup_lights.seed_studio_lights(context)
        self.report({"INFO"}, f"Seeded {count} studio light(s)")
        return {"FINISHED"}


class BEHOLD_OT_refresh_lights(Operator):
    bl_idname = "behold.refresh_lights"
    bl_label = "Apply Light Mixer"
    bl_description = "Push key/fill/rim and temperature to studio lights"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        if not light_lib.iter_behold_lights(context):
            self.report(report_set(NO_LIGHTS), NO_LIGHTS)
            return {"CANCELLED"}
        count = setup_lights.refresh_light_mixer(context)
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
            self.report(report_set(NO_LIGHT_TO_REMOVE), NO_LIGHT_TO_REMOVE)
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
            message = light_not_found(self.light_name)
            self.report(report_set(message), message)
            return {"CANCELLED"}
        light_lib.set_active_behold_light(context, light)
        self.report({"INFO"}, f"Active light: {light.name}")
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_seed_studio_lights,
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
