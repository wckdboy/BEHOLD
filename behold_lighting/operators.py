# SPDX-License-Identifier: GPL-3.0-or-later
"""Lighting operators: inventory, shape, gobo, IES, linking, mixer, seed."""

from __future__ import annotations

import bpy
from bpy.props import EnumProperty, StringProperty
from bpy.types import Context, Operator
from bpy_extras.io_utils import ImportHelper

from . import gobo_apply
from . import ies as ies_lib
from . import ies_apply
from . import light_linking
from . import light_linking_apply
from . import light_presets
from . import light_shape
from . import lights as light_lib
from . import setup_lights
from .common.messages import (
    NO_LIGHT_TO_REMOVE,
    NO_LIGHTS,
    light_not_found,
    report_set,
    unknown_light_preset_message,
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


class BEHOLD_OT_apply_gobo(Operator):
    bl_idname = "behold.apply_gobo"
    bl_label = "Apply Gobo"
    bl_description = (
        "Apply a procedural gobo (blinds / window / circle) to the active "
        "BEHOLD area or spot light. None tears the graph down"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        result = gobo_apply.apply_gobo_in_scene(context)
        if not result["ok"]:
            message = result["message"]
            self.report(report_set(message), message)
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


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


class BEHOLD_OT_link_selected(Operator):
    bl_idname = "behold.link_selected"
    bl_label = "Link Selected"
    bl_description = (
        "Cycle include / exclude on selected objects for the active BEHOLD light "
        "(Cycles light linking). Same idea as Light Wrangler L, against the selection"
    )
    bl_options = {"REGISTER", "UNDO"}

    kind: EnumProperty(
        name="Kind",
        description="Light linking (receivers) or shadow linking (blockers)",
        items=light_linking.kind_enum_items(),
        default=light_linking.DEFAULT_KIND,
    )

    def execute(self, context: Context):
        result = light_linking_apply.link_selected(context, kind=self.kind)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


class BEHOLD_OT_exclude_selected(Operator):
    bl_idname = "behold.exclude_selected"
    bl_label = "Exclude Selected"
    bl_description = (
        "Exclude selected objects from the active BEHOLD light "
        "(Cycles light linking / shadow linking)"
    )
    bl_options = {"REGISTER", "UNDO"}

    kind: EnumProperty(
        name="Kind",
        description="Light linking (receivers) or shadow linking (blockers)",
        items=light_linking.kind_enum_items(),
        default=light_linking.DEFAULT_KIND,
    )

    def execute(self, context: Context):
        result = light_linking_apply.exclude_selected(context, kind=self.kind)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


class BEHOLD_OT_unlink_selected(Operator):
    bl_idname = "behold.unlink_selected"
    bl_label = "Unlink"
    bl_description = (
        "Remove selected objects from the active BEHOLD light's linking collection. "
        "With nothing selected, clear linking on that light"
    )
    bl_options = {"REGISTER", "UNDO"}

    kind: EnumProperty(
        name="Kind",
        description="Light linking (receivers) or shadow linking (blockers)",
        items=light_linking.kind_enum_items(),
        default=light_linking.DEFAULT_KIND,
    )

    def execute(self, context: Context):
        result = light_linking_apply.unlink_selected(context, kind=self.kind)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


class BEHOLD_OT_solo_product_link(Operator):
    bl_idname = "behold.solo_product_link"
    bl_label = "Solo product"
    bl_description = (
        "Only the product receives this light (and casts its shadows when "
        "shadow linking is available). Cyclorama stays unlit"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        result = light_linking_apply.solo_product(context)
        if not result["ok"]:
            self.report(report_set(result["message"]), result["message"])
            return {"CANCELLED"}
        self.report({"INFO"}, result["message"])
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_seed_studio_lights,
    BEHOLD_OT_refresh_lights,
    BEHOLD_OT_add_light,
    BEHOLD_OT_remove_light,
    BEHOLD_OT_set_active_light,
    BEHOLD_OT_apply_light_preset,
    BEHOLD_OT_apply_gobo,
    BEHOLD_OT_load_ies,
    BEHOLD_OT_load_ies_sample,
    BEHOLD_OT_clear_ies,
    BEHOLD_OT_apply_ies,
    BEHOLD_OT_link_selected,
    BEHOLD_OT_exclude_selected,
    BEHOLD_OT_unlink_selected,
    BEHOLD_OT_solo_product_link,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
