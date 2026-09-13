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
    # Approximate WB via look temperature when available; otherwise leave AgX alone.
    if hasattr(view, "temperature"):
        # Blender 4.x+ view settings temperature is relative; map Kelvin offset from D65.
        view.temperature = (settings.white_balance_kelvin - 6500.0) / 1000.0
    if settings.false_color:
        try:
            view.view_transform = "False Color"
        except TypeError:
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


class BEHOLD_OT_batch_angles(Operator):
    bl_idname = "behold.batch_angles"
    bl_label = "Batch Product Angles"
    bl_description = "Render front, three-quarter, and top stills around the selection"
    bl_options = {"REGISTER"}

    def execute(self, context: Context):
        targets = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not targets:
            self.report({"ERROR"}, "Select the product mesh(es)")
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
        size = max((max(corners) - min(corners)).length * 0.35, 0.5)
        # Use bounds diagonal for distance.
        mins = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
        maxs = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
        extent = max(maxs.x - mins.x, maxs.y - mins.y, maxs.z - mins.z, 0.1)
        distance = extent * 2.4

        angles = (
            ("front", Vector((0.0, -distance, extent * 0.35))),
            ("three_quarter", Vector((distance * 0.75, -distance * 0.85, extent * 0.45))),
            ("top", Vector((0.0, -distance * 0.15, distance))),
        )

        apply_exposure(context)
        scene = context.scene
        scene.render.engine = "CYCLES"
        scene.cycles.use_denoising = True
        scene.render.image_settings.file_format = "PNG"

        base = bpy.path.abspath("//behold_angles/")
        if base.startswith("//") or not base:
            base = bpy.path.abspath("//")
            if not base:
                import tempfile
                from pathlib import Path

                base = str(Path(tempfile.gettempdir()) / "behold_angles")
        import os

        os.makedirs(base, exist_ok=True)

        original = cam.matrix_world.copy()
        rendered = 0
        for name, offset in angles:
            cam.location = center + offset
            direction = center - cam.location
            cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = os.path.join(base, f"{name}.png")
            bpy.ops.render.render(write_still=True)
            rendered += 1

        cam.matrix_world = original
        self.report({"INFO"}, f"Rendered {rendered} angles to {base}")
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_apply_exposure,
    BEHOLD_OT_render_still,
    BEHOLD_OT_setup_turntable,
    BEHOLD_OT_render_turntable,
    BEHOLD_OT_batch_angles,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
