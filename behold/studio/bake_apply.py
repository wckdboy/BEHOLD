# SPDX-License-Identifier: GPL-3.0-or-later
"""Render BEHOLD studio lights to an equirectangular HDR/EXR (Blender)."""

from __future__ import annotations

import os
import tempfile
from typing import Any

import bpy
from bpy.types import Camera, Context, Object, Scene

from . import bake as bake_lib
from . import cameras as camera_lib
from . import lights as light_lib
from . import world as world_lib
from . import world_apply


def bake_studio_hdri(context: Context) -> dict[str, Any]:
    """Render the current BEHOLD lights (+ optional world) to a 360° map."""
    scene = getattr(context, "scene", None)
    if scene is None:
        return {"ok": False, "message": bake_lib.BAKE_FAILED}

    if not light_lib.iter_behold_lights(context):
        return {"ok": False, "message": bake_lib.NO_LIGHTS_TO_BAKE}

    settings = scene.behold
    plan, error = bake_lib.plan_bake(
        filepath=getattr(settings, "bake_hdri_filepath", "") or "",
        blend_filepath=getattr(bpy.data, "filepath", "") or "",
        tempdir=tempfile.gettempdir(),
        resolution=getattr(
            settings, "bake_hdri_resolution", bake_lib.DEFAULT_RESOLUTION
        ),
        include_world=bool(getattr(settings, "bake_hdri_include_world", False)),
        apply_after=bool(getattr(settings, "bake_hdri_apply", False)),
    )
    if plan is None or error:
        return {"ok": False, "message": error or bake_lib.NO_BAKE_PATH}

    resolved = world_apply.resolve_filepath(plan.filepath) or plan.filepath
    parent = os.path.dirname(resolved)
    if parent:
        try:
            os.makedirs(parent, exist_ok=True)
        except OSError as exc:
            return {"ok": False, "message": f"{bake_lib.BAKE_FAILED}: {exc}"}

    settings.bake_hdri_filepath = plan.filepath
    snapshot = _snapshot_render(scene)
    hidden: list[Object] = []
    probe: Object | None = None
    try:
        hidden = _hide_meshes(scene)
        if not plan.include_world:
            scene.world = None
        probe = _ensure_probe(context, scene, plan)
        _apply_render_settings(scene, plan, resolved)
        if not _render_still():
            return {"ok": False, "message": bake_lib.BAKE_RENDER_FAILED}
        if not _save_render_result(resolved):
            return {"ok": False, "message": bake_lib.BAKE_FAILED}
    except Exception as exc:  # noqa: BLE001 — surface Cycles / IO failures
        return {"ok": False, "message": f"{bake_lib.BAKE_FAILED}: {exc}"}
    finally:
        _restore_render(scene, snapshot)
        _restore_hidden(hidden)
        _remove_probe(probe)

    applied = False
    if plan.apply_after:
        applied_ok, applied_message = _apply_baked_world(scene, settings, plan)
        if not applied_ok:
            return {
                "ok": False,
                "message": applied_message,
                "filepath": resolved,
            }
        applied = True

    return {
        "ok": True,
        "message": bake_lib.baked_message(resolved, applied=applied),
        "filepath": resolved,
        "applied": applied,
        "plan": plan,
    }


def _apply_baked_world(scene: Scene, settings, plan: bake_lib.BakePlan) -> tuple[bool, str]:
    settings.hdri_filepath = plan.filepath
    settings.hdri_strength = world_lib.DEFAULT_STRENGTH
    settings.hdri_rotation = world_lib.DEFAULT_ROTATION_DEG
    result = world_apply.apply_hdri(
        scene,
        filepath=plan.filepath,
        strength=world_lib.DEFAULT_STRENGTH,
        rotation_deg=world_lib.DEFAULT_ROTATION_DEG,
        reflections_only=bool(getattr(settings, "hdri_reflections_only", False)),
        background_strength=float(
            getattr(
                settings,
                "hdri_background_strength",
                world_lib.DEFAULT_BACKGROUND_STRENGTH,
            )
        ),
    )
    return bool(result["ok"]), str(result["message"])


def _snapshot_render(scene: Scene) -> dict[str, Any]:
    render = scene.render
    image = render.image_settings
    cycles = getattr(scene, "cycles", None)
    return {
        "engine": render.engine,
        "filepath": render.filepath,
        "resolution_x": render.resolution_x,
        "resolution_y": render.resolution_y,
        "resolution_percentage": render.resolution_percentage,
        "film_transparent": render.film_transparent,
        "use_file_extension": render.use_file_extension,
        "camera": scene.camera,
        "world": scene.world,
        "file_format": image.file_format,
        "color_mode": image.color_mode,
        "color_depth": image.color_depth,
        "exr_codec": getattr(image, "exr_codec", None),
        "cycles_samples": getattr(cycles, "samples", None) if cycles else None,
        "cycles_use_denoising": (
            getattr(cycles, "use_denoising", None) if cycles else None
        ),
    }


def _restore_render(scene: Scene, snapshot: dict[str, Any]) -> None:
    render = scene.render
    image = render.image_settings
    cycles = getattr(scene, "cycles", None)
    render.engine = snapshot["engine"]
    render.filepath = snapshot["filepath"]
    render.resolution_x = snapshot["resolution_x"]
    render.resolution_y = snapshot["resolution_y"]
    render.resolution_percentage = snapshot["resolution_percentage"]
    render.film_transparent = snapshot["film_transparent"]
    render.use_file_extension = snapshot["use_file_extension"]
    scene.camera = snapshot["camera"]
    scene.world = snapshot["world"]
    image.file_format = snapshot["file_format"]
    image.color_mode = snapshot["color_mode"]
    image.color_depth = snapshot["color_depth"]
    if snapshot["exr_codec"] is not None and hasattr(image, "exr_codec"):
        try:
            image.exr_codec = snapshot["exr_codec"]
        except TypeError:
            pass
    if cycles is None:
        return
    if snapshot["cycles_samples"] is not None:
        cycles.samples = snapshot["cycles_samples"]
    if snapshot["cycles_use_denoising"] is not None:
        cycles.use_denoising = snapshot["cycles_use_denoising"]


def _apply_render_settings(
    scene: Scene, plan: bake_lib.BakePlan, resolved: str
) -> None:
    render = scene.render
    image = render.image_settings
    render.engine = "CYCLES"
    render.resolution_x = plan.width
    render.resolution_y = plan.height
    render.resolution_percentage = 100
    render.film_transparent = False
    render.use_file_extension = True
    render.filepath = resolved
    image.file_format = plan.image_format
    image.color_mode = "RGB"
    if plan.image_format == "OPEN_EXR":
        image.color_depth = "32"
        if hasattr(image, "exr_codec"):
            try:
                image.exr_codec = "ZIP"
            except TypeError:
                pass
    cycles = getattr(scene, "cycles", None)
    if cycles is not None:
        cycles.samples = plan.samples
        cycles.use_denoising = False


def _hide_meshes(scene: Scene) -> list[Object]:
    hidden: list[Object] = []
    for obj in scene.objects:
        if not bake_lib.should_hide_for_bake(obj.type):
            continue
        if obj.hide_render:
            continue
        obj.hide_render = True
        hidden.append(obj)
    return hidden


def _restore_hidden(hidden: list[Object]) -> None:
    for obj in hidden:
        try:
            obj.hide_render = False
        except ReferenceError:
            continue


def _ensure_probe(context: Context, scene: Scene, plan: bake_lib.BakePlan) -> Object:
    _remove_named_probe()
    center, size = camera_lib.product_frame(context)
    clip_start, clip_end = bake_lib.probe_clip(size)
    data = bpy.data.cameras.new(bake_lib.PROBE_NAME)
    _configure_panoramic(data, clip_start, clip_end)
    probe = bpy.data.objects.new(bake_lib.PROBE_NAME, data)
    probe.location = center
    probe.rotation_euler = plan.rotation_xyz
    scene.collection.objects.link(probe)
    scene.camera = probe
    return probe


def _configure_panoramic(cam_data: Camera, clip_start: float, clip_end: float) -> None:
    cam_data.type = "PANO"
    if hasattr(cam_data, "panorama_type"):
        try:
            cam_data.panorama_type = "EQUIRECTANGULAR"
        except TypeError:
            pass
    cycles_cam = getattr(cam_data, "cycles", None)
    if cycles_cam is not None and hasattr(cycles_cam, "panorama_type"):
        try:
            cycles_cam.panorama_type = "EQUIRECTANGULAR"
        except TypeError:
            pass
    cam_data.clip_start = clip_start
    cam_data.clip_end = clip_end


def _remove_named_probe() -> None:
    _remove_probe(bpy.data.objects.get(bake_lib.PROBE_NAME))


def _remove_probe(probe: Object | None) -> None:
    if probe is None:
        return
    data = probe.data
    try:
        bpy.data.objects.remove(probe, do_unlink=True)
    except ReferenceError:
        data = None
    if data is not None and getattr(data, "users", 1) == 0:
        try:
            bpy.data.cameras.remove(data)
        except (ReferenceError, TypeError):
            pass


def _render_still() -> bool:
    try:
        result = bpy.ops.render.render(write_still=False)
    except Exception:  # noqa: BLE001 — Cycles missing / cancelled
        return False
    if result is None:
        return True
    if isinstance(result, set):
        return "FINISHED" in result
    if isinstance(result, str):
        return result == "FINISHED"
    return True


def _save_render_result(filepath: str) -> bool:
    image = bpy.data.images.get("Render Result")
    if image is None:
        return os.path.isfile(filepath)
    try:
        image.save_render(filepath)
    except Exception:  # noqa: BLE001 — fall back to a still already on disk
        return os.path.isfile(filepath)
    return os.path.isfile(filepath)
