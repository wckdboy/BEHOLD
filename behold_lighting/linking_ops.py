# SPDX-License-Identifier: GPL-3.0-or-later
"""Lighting linking operators — include / exclude / unlink / solo product."""

from __future__ import annotations

import bpy
from bpy.props import EnumProperty
from bpy.types import Context, Operator

from . import light_linking
from . import light_linking_apply
from .common.messages import report_set


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
