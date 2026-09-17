# SPDX-License-Identifier: GPL-3.0-or-later
"""Product camera operators — seed, inventory, frame, bookmark, DoF."""

from __future__ import annotations

import bpy
from bpy.props import StringProperty
from bpy.types import Context, Operator

from . import cameras as camera_lib
from . import dof_apply
from .common.messages import (
    FRAME_NO_PRODUCT,
    NO_CAMERA,
    NO_CAMERA_TO_REMOVE,
    NO_CAMERAS_TO_CLEAR,
    NO_MAIN_CAMERA,
    bookmark_camera_missing,
    camera_not_found,
    report_set,
)


class BEHOLD_OT_bookmark_camera(Operator):
    bl_idname = "behold.bookmark_camera"
    bl_label = "Bookmark Main Camera"
    bl_description = "Remember the scene camera as BEHOLD's main camera"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        cam = context.scene.camera
        if cam is None or cam.type != "CAMERA":
            self.report(report_set(NO_CAMERA), NO_CAMERA)
            return {"CANCELLED"}
        if camera_lib.is_behold_camera(cam):
            camera_lib.set_active_behold_camera(context, cam)
        else:
            context.scene.behold_product.main_camera_name = cam.name
        self.report({"INFO"}, f"Main camera: {cam.name}")
        return {"FINISHED"}


class BEHOLD_OT_use_main_camera(Operator):
    bl_idname = "behold.use_main_camera"
    bl_label = "Use Main Camera"
    bl_description = "Make the bookmarked camera the scene camera"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        name = context.scene.behold_product.main_camera_name
        if not name:
            self.report(report_set(NO_MAIN_CAMERA), NO_MAIN_CAMERA)
            return {"CANCELLED"}
        cam = bpy.data.objects.get(name)
        if cam is None or cam.type != "CAMERA":
            message = bookmark_camera_missing(name)
            self.report(report_set(message), message)
            return {"CANCELLED"}
        if camera_lib.is_behold_camera(cam):
            camera_lib.set_active_behold_camera(context, cam)
        else:
            context.scene.camera = cam
        self.report({"INFO"}, f"Scene camera → {name}")
        return {"FINISHED"}


class BEHOLD_OT_seed_studio_camera(Operator):
    bl_idname = "behold.seed_studio_camera"
    bl_label = "Seed Studio Camera"
    bl_description = "Create or frame the default BEHOLD camera around the product"
    bl_options = {"REGISTER", "UNDO", "INTERNAL"}

    def execute(self, context: Context):
        cam = camera_lib.seed_studio_camera(context)
        if cam is None:
            self.report(report_set(NO_CAMERA), NO_CAMERA)
            return {"CANCELLED"}
        self.report({"INFO"}, f"Studio camera {cam.name}")
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
            self.report(report_set(NO_CAMERA_TO_REMOVE), NO_CAMERA_TO_REMOVE)
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
            message = camera_not_found(self.camera_name)
            self.report(report_set(message), message)
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
            self.report(report_set(NO_CAMERA), NO_CAMERA)
            return {"CANCELLED"}
        if not camera_lib.product_targets(context):
            self.report(report_set(FRAME_NO_PRODUCT), FRAME_NO_PRODUCT)
            return {"CANCELLED"}
        camera_lib.frame_behold_camera(context, cam)
        self.report({"INFO"}, f"Framed {cam.name}")
        return {"FINISHED"}


class BEHOLD_OT_apply_camera_dof(Operator):
    bl_idname = "behold.apply_camera_dof"
    bl_label = "Apply DoF"
    bl_description = (
        "Push DoF on/off and f-stop to the active BEHOLD camera (Blender 5.2 Camera.dof)"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        result = dof_apply.apply_dof(context, focus="KEEP")
        message = result["message"]
        if result["ok"]:
            self.report({"INFO"}, message)
            return {"FINISHED"}
        self.report(report_set(message), message)
        return {"CANCELLED"}


class BEHOLD_OT_focus_product(Operator):
    bl_idname = "behold.focus_product"
    bl_label = "Focus on product"
    bl_description = (
        "Enable DoF and set focus distance to the product (studio sweep excluded)"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        settings = context.scene.behold_product
        settings.dof_enabled = True
        result = dof_apply.apply_dof(context, use_dof=True, focus="PRODUCT")
        message = result["message"]
        if result["ok"]:
            self.report({"INFO"}, message)
            return {"FINISHED"}
        self.report(report_set(message), message)
        return {"CANCELLED"}


class BEHOLD_OT_focus_selected(Operator):
    bl_idname = "behold.focus_selected"
    bl_label = "Focus on selected"
    bl_description = (
        "Enable DoF and set focus distance to the selected mesh / surface"
    )
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        settings = context.scene.behold_product
        settings.dof_enabled = True
        result = dof_apply.apply_dof(context, use_dof=True, focus="SELECTED")
        message = result["message"]
        if result["ok"]:
            self.report({"INFO"}, message)
            return {"FINISHED"}
        self.report(report_set(message), message)
        return {"CANCELLED"}


class BEHOLD_OT_clear_cameras(Operator):
    bl_idname = "behold.clear_cameras"
    bl_label = "Clear Cameras"
    bl_description = "Remove all BEHOLD cameras from the scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        count = camera_lib.clear_behold_cameras(context)
        if count == 0:
            self.report(report_set(NO_CAMERAS_TO_CLEAR), NO_CAMERAS_TO_CLEAR)
            return {"CANCELLED"}
        self.report({"INFO"}, f"Cleared {count} camera(s)")
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_bookmark_camera,
    BEHOLD_OT_use_main_camera,
    BEHOLD_OT_seed_studio_camera,
    BEHOLD_OT_add_camera,
    BEHOLD_OT_remove_camera,
    BEHOLD_OT_set_active_camera,
    BEHOLD_OT_frame_camera,
    BEHOLD_OT_apply_camera_dof,
    BEHOLD_OT_focus_product,
    BEHOLD_OT_focus_selected,
    BEHOLD_OT_clear_cameras,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
