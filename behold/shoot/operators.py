# SPDX-License-Identifier: GPL-3.0-or-later
"""Still and turntable shoot operators."""

from __future__ import annotations

import math

import bpy
from bpy.types import Context, Operator


def _ensure_camera(context: Context) -> bpy.types.Object | None:
    if context.scene.camera is not None:
        return context.scene.camera
    cam = bpy.data.objects.get("BEHOLD_Camera")
    if cam is not None:
        context.scene.camera = cam
    return context.scene.camera


def apply_exposure(context: Context) -> None:
    settings = context.scene.behold
    view = context.scene.view_settings
    view.exposure = settings.exposure_ev
    if settings.false_color:
        try:
            view.view_transform = "False Color"
        except TypeError:
            # Older/custom OCIO configs may lack False Color.
            pass
    else:
        try:
            view.view_transform = "AgX"
        except TypeError:
            pass


class BEHOLD_OT_apply_exposure(Operator):
    bl_idname = "behold.apply_exposure"
    bl_label = "Apply Exposure"
    bl_description = "Push EV and false-color settings to the scene view"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        apply_exposure(context)
        self.report({"INFO"}, "Exposure applied")
        return {"FINISHED"}


class BEHOLD_OT_render_still(Operator):
    bl_idname = "behold.render_still"
    bl_label = "Render Still"
    bl_description = "Render a still with product-friendly Cycles defaults"

    def execute(self, context: Context):
        if _ensure_camera(context) is None:
            self.report({"ERROR"}, "No camera — Build Studio first")
            return {"CANCELLED"}

        apply_exposure(context)
        scene = context.scene
        scene.render.engine = "CYCLES"
        scene.cycles.samples = max(scene.cycles.samples, 128)
        scene.cycles.use_denoising = True
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)
        self.report({"INFO"}, "Still render started")
        return {"FINISHED"}


class BEHOLD_OT_setup_turntable(Operator):
    bl_idname = "behold.setup_turntable"
    bl_label = "Setup Turntable"
    bl_description = "Animate a 360° orbit of the active camera around the selection"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        targets = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not targets:
            self.report({"ERROR"}, "Select the product mesh(es) to orbit")
            return {"CANCELLED"}

        cam = _ensure_camera(context)
        if cam is None:
            self.report({"ERROR"}, "No camera — Build Studio first")
            return {"CANCELLED"}

        from mathutils import Vector

        corners = [
            obj.matrix_world @ Vector(corner)
            for obj in targets
            for corner in obj.bound_box
        ]
        center = sum(corners, Vector()) / len(corners)

        pivot_name = "BEHOLD_TurntablePivot"
        pivot = bpy.data.objects.get(pivot_name)
        if pivot is None:
            pivot = bpy.data.objects.new(pivot_name, None)
            context.scene.collection.objects.link(pivot)
        pivot.empty_display_type = "PLAIN_AXES"
        pivot.location = center

        # Parent camera to pivot while keeping world transform.
        mw = cam.matrix_world.copy()
        cam.parent = pivot
        cam.matrix_world = mw

        frames = int(context.scene.behold.turntable_frames)
        scene = context.scene
        scene.frame_start = 1
        scene.frame_end = frames
        pivot.rotation_euler = (0.0, 0.0, 0.0)
        pivot.keyframe_insert(data_path="rotation_euler", frame=1)
        pivot.rotation_euler = (0.0, 0.0, math.tau)
        pivot.keyframe_insert(data_path="rotation_euler", frame=frames)

        # Linear interpolation for constant spin.
        if pivot.animation_data and pivot.animation_data.action:
            for fcurve in pivot.animation_data.action.fcurves:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = "LINEAR"

        apply_exposure(context)
        self.report({"INFO"}, f"Turntable set for {frames} frames")
        return {"FINISHED"}


class BEHOLD_OT_render_turntable(Operator):
    bl_idname = "behold.render_turntable"
    bl_label = "Render Turntable"
    bl_description = "Render the turntable animation"

    def execute(self, context: Context):
        if bpy.data.objects.get("BEHOLD_TurntablePivot") is None:
            self.report({"ERROR"}, "Run Setup Turntable first")
            return {"CANCELLED"}
        if _ensure_camera(context) is None:
            self.report({"ERROR"}, "No camera in the scene")
            return {"CANCELLED"}

        apply_exposure(context)
        scene = context.scene
        scene.render.engine = "CYCLES"
        scene.cycles.use_denoising = True
        scene.render.image_settings.file_format = "FFMPEG"
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
        bpy.ops.render.render("INVOKE_DEFAULT", animation=True)
        self.report({"INFO"}, "Turntable render started")
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_apply_exposure,
    BEHOLD_OT_render_still,
    BEHOLD_OT_setup_turntable,
    BEHOLD_OT_render_turntable,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
