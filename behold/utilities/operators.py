# SPDX-License-Identifier: GPL-3.0-or-later
"""Utilities operators — registered only while the feature flag is on."""

from __future__ import annotations

from pathlib import Path

import bpy
from bpy.types import Context, Operator

from ..preferences import get_prefs
from . import build as build_lib
from .flag import show_utilities_panel
from .messages import NO_UTILITIES, report_set, scad_exported_message
from .openscad import generate_wall_stack_scad, suggest_scad_path


def _enabled(context: Context) -> bool:
    return show_utilities_panel(get_prefs(context))


class BEHOLD_OT_build_danish_wall(Operator):
    bl_idname = "behold.build_danish_wall"
    bl_label = "Build Wall"
    bl_description = "Build a layered Danish wall (masonry + insulation + plaster)"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return _enabled(context)

    def execute(self, context: Context):
        if not _enabled(context):
            self.report(report_set(NO_UTILITIES), NO_UTILITIES)
            return {"CANCELLED"}
        spec = build_lib.spec_from_settings(context.scene.behold.utilities)
        result = build_lib.build_wall(context, spec)
        self.report(report_set(result["message"]) if not result["ok"] else {"INFO"}, result["message"])
        return {"FINISHED"} if result["ok"] else {"CANCELLED"}


class BEHOLD_OT_build_balcony_legs(Operator):
    bl_idname = "behold.build_balcony_legs"
    bl_label = "Build Legs"
    bl_description = "Front posts, base plates, and rear wall brackets against the wall"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return _enabled(context)

    def execute(self, context: Context):
        if not _enabled(context):
            self.report(report_set(NO_UTILITIES), NO_UTILITIES)
            return {"CANCELLED"}
        result = build_lib.build_mount(context, "LEGS")
        self.report(report_set(result["message"]) if not result["ok"] else {"INFO"}, result["message"])
        return {"FINISHED"} if result["ok"] else {"CANCELLED"}


class BEHOLD_OT_build_balcony_bracket(Operator):
    bl_idname = "behold.build_balcony_bracket"
    bl_label = "Build L-bracket"
    bl_description = "Under-frame L-brackets with a diagonal brace against the wall"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return _enabled(context)

    def execute(self, context: Context):
        if not _enabled(context):
            self.report(report_set(NO_UTILITIES), NO_UTILITIES)
            return {"CANCELLED"}
        result = build_lib.build_mount(context, "BRACKET")
        self.report(report_set(result["message"]) if not result["ok"] else {"INFO"}, result["message"])
        return {"FINISHED"} if result["ok"] else {"CANCELLED"}


class BEHOLD_OT_export_wall_scad(Operator):
    bl_idname = "behold.export_wall_scad"
    bl_label = "Export wall .scad"
    bl_description = "Write the current wall stack as OpenSCAD (optional helper)"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: Context) -> bool:
        return _enabled(context)

    def execute(self, context: Context):
        if not _enabled(context):
            self.report(report_set(NO_UTILITIES), NO_UTILITIES)
            return {"CANCELLED"}
        spec = build_lib.spec_from_settings(context.scene.behold.utilities)
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
    BEHOLD_OT_export_wall_scad,
)
