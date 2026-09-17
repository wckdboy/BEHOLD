# SPDX-License-Identifier: GPL-3.0-or-later
"""Utilities operators — Danish wall, balcony mounts, eave, OpenSCAD export."""

from __future__ import annotations

from pathlib import Path

import bpy
from bpy.types import Context, Operator

from . import build as build_lib
from .messages import report_set, scad_exported_message
from .openscad import generate_wall_stack_scad, suggest_scad_path


class BEHOLD_OT_build_danish_wall(Operator):
    bl_idname = "behold.build_danish_wall"
    bl_label = "Build Wall"
    bl_description = "Build a layered Danish wall (masonry + insulation + plaster)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        spec = build_lib.spec_from_settings(context.scene.behold_utilities)
        result = build_lib.build_wall(context, spec)
        self.report(report_set(result["message"]) if not result["ok"] else {"INFO"}, result["message"])
        return {"FINISHED"} if result["ok"] else {"CANCELLED"}


class BEHOLD_OT_build_balcony_legs(Operator):
    bl_idname = "behold.build_balcony_legs"
    bl_label = "Build Legs"
    bl_description = "Front posts, base plates, and rear wall brackets against the wall"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        result = build_lib.build_mount(context, "LEGS")
        self.report(report_set(result["message"]) if not result["ok"] else {"INFO"}, result["message"])
        return {"FINISHED"} if result["ok"] else {"CANCELLED"}


class BEHOLD_OT_build_balcony_bracket(Operator):
    bl_idname = "behold.build_balcony_bracket"
    bl_label = "Build L-bracket"
    bl_description = "Under-frame L-brackets with a diagonal brace against the wall"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        result = build_lib.build_mount(context, "BRACKET")
        self.report(report_set(result["message"]) if not result["ok"] else {"INFO"}, result["message"])
        return {"FINISHED"} if result["ok"] else {"CANCELLED"}


class BEHOLD_OT_build_eave_section(Operator):
    bl_idname = "behold.build_eave_section"
    bl_label = "Build eave section"
    bl_description = (
        "Build a MinAltan roof / eave context mesh against the Danish wall "
        "(under/over eaves and related snit presets)"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        section = context.scene.behold_utilities.eave_section
        result = build_lib.build_eave(context, section)
        self.report(report_set(result["message"]) if not result["ok"] else {"INFO"}, result["message"])
        return {"FINISHED"} if result["ok"] else {"CANCELLED"}


class BEHOLD_OT_export_wall_scad(Operator):
    bl_idname = "behold.export_wall_scad"
    bl_label = "Export wall .scad"
    bl_description = "Write the current wall stack as OpenSCAD (optional helper)"
    bl_options = {"REGISTER"}

    def execute(self, context: Context):
        spec = build_lib.spec_from_settings(context.scene.behold_utilities)
        text = generate_wall_stack_scad(spec)
        name = "behold_danish_wall.scad"
        block = bpy.data.texts.get(name) or bpy.data.texts.new(name)
        block.clear()
        block.write(text)
        path = suggest_scad_path(getattr(bpy.data, "filepath", "") or "")
        written = name
        if path:
            Path(path).write_text(text, encoding="utf-8")
            written = path
        self.report({"INFO"}, scad_exported_message(written))
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_build_danish_wall,
    BEHOLD_OT_build_balcony_legs,
    BEHOLD_OT_build_balcony_bracket,
    BEHOLD_OT_build_eave_section,
    BEHOLD_OT_export_wall_scad,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
