# SPDX-License-Identifier: GPL-3.0-or-later
"""Lighting Gobo operators — procedural cookie on the active light."""

from __future__ import annotations

import bpy
from bpy.types import Context, Operator

from . import gobo_apply
from .common.messages import report_set


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


CLASSES = (BEHOLD_OT_apply_gobo,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
