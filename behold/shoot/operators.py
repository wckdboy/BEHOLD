# SPDX-License-Identifier: GPL-3.0-or-later
"""Still and turntable shoot operators (Photographer-depth slice)."""

from __future__ import annotations

import math
import os

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator

from ..studio import cameras as camera_lib


QUALITY_SAMPLES = {
    "DRAFT": 32,
    "FINAL": 256,
    "PRODUCT": 128,
    "HERO": 512,
}


def _ensure_camera(context: Context) -> bpy.types.Object | None:
    cam = camera_lib.resolve_shoot_camera(context)
    if cam is not None:
        context.scene.camera = cam
    return cam


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


def apply_render_quality(context: Context) -> int:
    """Push quality preset to Cycles. Returns sample count."""
    settings = context.scene.behold
    quality = settings.render_quality
    samples = QUALITY_SAMPLES.get(quality, 128)

    scene = context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    # Prefer OptiX/OIDN when available; ignore if the build lacks the attr.
    if hasattr(scene.cycles, "denoiser"):
        try:
            scene.cycles.denoiser = "OPENIMAGEDENOISE"
        except TypeError:
            pass
    return samples


def resolve_output_dir(context: Context, *, angle: str = "") -> str:
    """Resolve output folder with {angle} {camera} {quality} tokens."""
    settings = context.scene.behold
    cam = context.scene.camera
    camera_name = cam.name if cam is not None else "camera"
    template = settings.output_directory.strip() or "//behold_out/"
    filled = (
        template.replace("{angle}", angle or "still")
        .replace("{camera}", camera_name)
        .replace("{quality}", settings.render_quality.lower())
    )
    path = bpy.path.abspath(filled)
    if not path or path.startswith("//"):
        path = os.path.join(tempfile_fallback(), "behold_out", angle or "still")
    os.makedirs(path, exist_ok=True)
    return path


def tempfile_fallback() -> str:
    import tempfile

    return tempfile.gettempdir()


class BEHOLD_OT_apply_exposure(Operator):
    bl_idname = "behold.apply_exposure"
    bl_label = "Apply Exposure"
    bl_description = "Push EV and false-color settings to the scene view"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        apply_exposure(context)
        self.report({"INFO"}, "Exposure applied")
        return {"FINISHED"}


class BEHOLD_OT_apply_quality(Operator):
    bl_idname = "behold.apply_quality"
    bl_label = "Apply Quality Preset"
    bl_description = "Push Draft / Final / Product / Hero sample counts to Cycles"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        samples = apply_render_quality(context)
        quality = context.scene.behold.render_quality
        self.report({"INFO"}, f"{quality.title()} quality — {samples} samples")
        return {"FINISHED"}


class BEHOLD_OT_bookmark_camera(Operator):
    bl_idname = "behold.bookmark_camera"
    bl_label = "Bookmark Main Camera"
    bl_description = "Remember the scene camera as BEHOLD's main camera"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        cam = context.scene.camera
        if cam is None or cam.type != "CAMERA":
            self.report({"ERROR"}, "Set a scene camera first (Build Studio or Add Camera)")
            return {"CANCELLED"}
        if camera_lib.is_behold_camera(cam):
            camera_lib.set_active_behold_camera(context, cam)
        else:
            context.scene.behold.main_camera_name = cam.name
        self.report({"INFO"}, f"Main camera: {cam.name}")
        return {"FINISHED"}


class BEHOLD_OT_use_main_camera(Operator):
    bl_idname = "behold.use_main_camera"
    bl_label = "Use Main Camera"
    bl_description = "Make the bookmarked camera the scene camera"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        name = context.scene.behold.main_camera_name
        if not name:
            self.report({"ERROR"}, "No main camera bookmarked yet")
            return {"CANCELLED"}
        cam = bpy.data.objects.get(name)
        if cam is None or cam.type != "CAMERA":
            self.report({"ERROR"}, f"Bookmarked camera “{name}” is missing")
            return {"CANCELLED"}
        if camera_lib.is_behold_camera(cam):
            camera_lib.set_active_behold_camera(context, cam)
        else:
            context.scene.camera = cam
        self.report({"INFO"}, f"Scene camera → {name}")
        return {"FINISHED"}


class BEHOLD_OT_add_camera(Operator):
    bl_idname = "behold.add_camera"
    bl_label = "Add Camera"
    bl_description = "Create a BEHOLD product camera and make it the Shoot camera"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        cam = camera_lib.add_product_camera(context)
        self.report({"INFO"}, f"Added {cam.name} ({cam.data.lens:.0f} mm)")
        return {"FINISHED"}


class BEHOLD_OT_remove_camera(Operator):
    bl_idname = "behold.remove_camera"
    bl_label = "Remove Camera"
    bl_description = "Remove a BEHOLD camera"
    bl_options = {"REGISTER", "UNDO"}

    camera_name: StringProperty(name="Camera", default="")

    def execute(self, context: Context):
        name = (self.camera_name or "").strip()
        cam = bpy.data.objects.get(name) if name else camera_lib.get_active_behold_camera(context)
        if cam is None or not camera_lib.is_behold_camera(cam):
            self.report({"ERROR"}, "Pick a BEHOLD camera to remove")
            return {"CANCELLED"}
        removed = cam.name
        camera_lib.remove_behold_camera(context, cam)
        self.report({"INFO"}, f"Removed {removed}")
        return {"FINISHED"}


class BEHOLD_OT_set_active_camera(Operator):
    bl_idname = "behold.set_active_camera"
    bl_label = "Set Active Camera"
    bl_description = "Make this the scene camera and BEHOLD main camera"
    bl_options = {"REGISTER", "UNDO"}

    camera_name: StringProperty(name="Camera", default="")

    def execute(self, context: Context):
        cam = bpy.data.objects.get(self.camera_name)
        if cam is None or not camera_lib.is_behold_camera(cam):
            self.report({"ERROR"}, f"Camera “{self.camera_name}” not found")
            return {"CANCELLED"}
        camera_lib.set_active_behold_camera(context, cam)
        self.report({"INFO"}, f"Active camera: {cam.name}")
        return {"FINISHED"}


class BEHOLD_OT_frame_camera(Operator):
    bl_idname = "behold.frame_camera"
    bl_label = "Frame Camera"
    bl_description = "Frame the selected mesh, or the product, in the active BEHOLD camera"
    bl_options = {"REGISTER", "UNDO"}

    camera_name: StringProperty(name="Camera", default="")

    def execute(self, context: Context):
        name = (self.camera_name or "").strip()
        cam = bpy.data.objects.get(name) if name else camera_lib.get_active_behold_camera(context)
        if cam is None or not camera_lib.is_behold_camera(cam):
            self.report({"ERROR"}, "Add a BEHOLD camera first")
            return {"CANCELLED"}
        if not camera_lib.product_targets(context):
            self.report({"ERROR"}, "Select a product mesh or Build Studio")
            return {"CANCELLED"}
        camera_lib.frame_behold_camera(context, cam)
        self.report({"INFO"}, f"Framed {cam.name}")
        return {"FINISHED"}


class BEHOLD_OT_clear_cameras(Operator):
    bl_idname = "behold.clear_cameras"
    bl_label = "Clear Cameras"
    bl_description = "Remove all BEHOLD cameras from the scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        count = camera_lib.clear_behold_cameras(context)
        if count == 0:
            self.report({"WARNING"}, "No BEHOLD cameras to clear")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Cleared {count} camera(s)")
        return {"FINISHED"}


class BEHOLD_OT_render_still(Operator):
    bl_idname = "behold.render_still"
    bl_label = "Render Still"
    bl_description = "Render a still with the active quality preset"

    def execute(self, context: Context):
        cam = _ensure_camera(context)
        if cam is None:
            self.report({"ERROR"}, "No camera — Build Studio or Add Camera")
            return {"CANCELLED"}

        apply_exposure(context)
        samples = apply_render_quality(context)
        scene = context.scene
        scene.render.image_settings.file_format = "PNG"
        out_dir = resolve_output_dir(context, angle="still")
        scene.render.filepath = os.path.join(out_dir, "still.png")
        bpy.ops.render.render("INVOKE_DEFAULT", write_still=True)
        self.report({"INFO"}, f"Still started ({samples} samples) → {out_dir}")
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
            self.report({"ERROR"}, "No camera — Build Studio or Add Camera")
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
    bl_description = "Render the turntable animation with the active quality preset"

    def execute(self, context: Context):
        if bpy.data.objects.get("BEHOLD_TurntablePivot") is None:
            self.report({"ERROR"}, "Run Setup Turntable first")
            return {"CANCELLED"}
        if _ensure_camera(context) is None:
            self.report({"ERROR"}, "No camera in the scene")
            return {"CANCELLED"}

        apply_exposure(context)
        samples = apply_render_quality(context)
        scene = context.scene
        scene.render.image_settings.file_format = "FFMPEG"
        scene.render.ffmpeg.format = "MPEG4"
        scene.render.ffmpeg.codec = "H264"
        out_dir = resolve_output_dir(context, angle="turntable")
        scene.render.filepath = os.path.join(out_dir, "turntable")
        bpy.ops.render.render("INVOKE_DEFAULT", animation=True)
        self.report({"INFO"}, f"Turntable started ({samples} samples) → {out_dir}")
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
            self.report({"ERROR"}, "No camera — Build Studio or Add Camera")
            return {"CANCELLED"}

        from mathutils import Vector

        corners = [
            obj.matrix_world @ Vector(corner)
            for obj in targets
            for corner in obj.bound_box
        ]
        center = sum(corners, Vector()) / len(corners)
        mins = Vector(
            (min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners))
        )
        maxs = Vector(
            (max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners))
        )
        extent = max(maxs.x - mins.x, maxs.y - mins.y, maxs.z - mins.z, 0.1)
        distance = extent * 2.4

        angles = (
            ("front", Vector((0.0, -distance, extent * 0.35))),
            ("three_quarter", Vector((distance * 0.75, -distance * 0.85, extent * 0.45))),
            ("top", Vector((0.0, -distance * 0.15, distance))),
        )

        apply_exposure(context)
        samples = apply_render_quality(context)
        scene = context.scene
        scene.render.image_settings.file_format = "PNG"

        original = cam.matrix_world.copy()
        rendered = 0
        last_dir = ""
        for name, offset in angles:
            out_dir = resolve_output_dir(context, angle=name)
            last_dir = out_dir
            cam.location = center + offset
            direction = center - cam.location
            cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = os.path.join(out_dir, f"{name}.png")
            bpy.ops.render.render(write_still=True)
            rendered += 1

        cam.matrix_world = original
        self.report(
            {"INFO"},
            f"Rendered {rendered} angles ({samples} samples) → {last_dir}",
        )
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_apply_exposure,
    BEHOLD_OT_apply_quality,
    BEHOLD_OT_bookmark_camera,
    BEHOLD_OT_use_main_camera,
    BEHOLD_OT_add_camera,
    BEHOLD_OT_remove_camera,
    BEHOLD_OT_set_active_camera,
    BEHOLD_OT_frame_camera,
    BEHOLD_OT_clear_cameras,
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
