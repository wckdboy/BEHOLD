# SPDX-License-Identifier: GPL-3.0-or-later
"""Operator reports and empty-state copy — no Blender import.

Each failure is a short sentence plus what to do next. Empty-state CTAs
and operator reports share these strings so the N-panel and the Info bar
do not disagree.
"""

from __future__ import annotations

import os

from ..materials.presets import EMPTY_NO_MESH, EMPTY_NO_MESH_HINT
from ..shoot.exposure import (
    EXPOSURE_APPLIED,
    FALSE_COLOR_OFF,
    FALSE_COLOR_ON,
    FALSE_COLOR_UNAVAILABLE,
    NO_VIEW_SETTINGS,
)
from ..studio.bake import (
    BAKE_FAILED,
    BAKE_RENDER_FAILED,
    NO_BAKE_PATH,
    NO_LIGHTS_TO_BAKE,
    UNSUPPORTED_BAKE,
    baked_message,
    path_problem_message as bake_path_problem_message,
)
from ..shoot.batch import (
    BATCH_NO_CAMERA,
    BATCH_NO_MESH,
    BATCH_NO_SHOTS,
    BATCH_NOTHING,
    BATCH_RENDER_FAILED,
)
from ..shoot.looks import (
    LOOK_COMPOSITOR_BUSY,
    LOOK_DISABLED,
    LOOK_NODES_FAILED,
    NO_COMPOSITOR,
    UNKNOWN_LOOK_PRESET,
    unknown_look_message,
)
from ..shoot.shots import (
    EMPTY_NO_SHOTS,
    EMPTY_NO_SHOTS_NEXT,
    EMPTY_NO_SHOTS_TITLE,
    NO_SHOT_TO_APPLY,
    NO_SHOT_TO_REMOVE,
    NO_SHOT_TO_RENAME,
    SHOT_NAME_EMPTY,
    shot_applied_message,
    shot_name_taken,
    shot_removed_message,
    shot_renamed_message,
    shot_saved_message,
)
from ..shoot.turntable import (
    EMPTY_NO_CAMERA,
    EMPTY_NO_PRODUCT,
    TURNTABLE_NO_SETUP,
    TURNTABLE_NOTHING_TO_CLEAR,
    TURNTABLE_READY_PLAY,
)

# Blender self.report types. Missing-prerequisite → WARNING; real failure → ERROR.
WARNING = "WARNING"
ERROR = "ERROR"

NO_MESH_SELECTED = EMPTY_NO_MESH
NO_MESH_HINT = EMPTY_NO_MESH_HINT
NO_CAMERA = EMPTY_NO_CAMERA
NO_PRODUCT = EMPTY_NO_PRODUCT

NO_FILE_SELECTED = "No file selected — pick a product mesh or CAD file"
NO_HDRI_FILE = "No HDRI selected — pick an HDR, EXR, or image from disk"
NO_WORLD = "No world on this scene — Build Studio, then Load HDRI"
WORLD_RESET = "World reset to solid studio"
HDRI_LOAD_FAILED = "Could not load that HDRI — pick another .hdr / .exr and try Load HDRI"

NO_LIGHTS_TITLE = "No BEHOLD lights yet"
NO_LIGHTS_NEXT = "Build Studio or Add Light"
NO_LIGHTS = f"{NO_LIGHTS_TITLE} — {NO_LIGHTS_NEXT}"
NO_LIGHTS_HINT = "Build Studio to seed Key, Fill, and Rim"

NO_CAMERAS_TITLE = "No BEHOLD cameras yet"
NO_CAMERAS_NEXT = "Build Studio or Add Camera"
NO_CAMERAS = f"{NO_CAMERAS_TITLE} — {NO_CAMERAS_NEXT}"
NO_CAMERAS_HINT = "Build Studio to add a framed product camera"

NO_SHOTS_TITLE = EMPTY_NO_SHOTS_TITLE
NO_SHOTS_NEXT = EMPTY_NO_SHOTS_NEXT
NO_SHOTS = EMPTY_NO_SHOTS

FRAME_NO_PRODUCT = "No product to frame — select the mesh or Import Product"
NO_CAMERA_TO_REMOVE = "No BEHOLD camera to remove — Build Studio or Add Camera"
NO_LIGHT_TO_REMOVE = "No BEHOLD light to remove — Build Studio or Add Light"
NO_CAMERAS_TO_CLEAR = "No BEHOLD cameras to clear — Build Studio or Add Camera"

UNKNOWN_LIGHT_PRESET = (
    "Unknown light shape — pick Softbox, Strip, Octa, Hard, or Rim"
)

LIGHT_DRAW_NEEDS_VIEWPORT = (
    "Light Draw needs a 3D Viewport — open a 3D View and run it from Lights"
)
LIGHT_DRAW_NO_LIGHTS = (
    "No BEHOLD lights yet — drawing a new light. Build Studio or Add Light for a full rig"
)
LIGHT_DRAW_LIGHT_MISSING = (
    "Light Draw cancelled — the light is gone. Add Light or Build Studio"
)

NO_MAIN_CAMERA = (
    "No main camera bookmarked yet — Bookmark on Advanced → Shoot, or Add Camera"
)
# BATCH_NO_MESH / BATCH_NO_SHOTS / BATCH_NOTHING live in shoot.batch.

UPDATE_CHECK_OFFLINE = (
    "Could not reach GitHub — Check your network, then Check for updates. Or Open release."
)
UPDATE_CHECK_UNAVAILABLE = (
    "This release has no behold-*.zip — "
    "Open release and install the zip the same way as the first time."
)

EMPTY_STATE_MESSAGES = frozenset(
    {
        NO_MESH_SELECTED,
        NO_CAMERA,
        NO_PRODUCT,
        NO_FILE_SELECTED,
        NO_HDRI_FILE,
        NO_WORLD,
        NO_LIGHTS,
        NO_LIGHTS_TO_BAKE,
        NO_BAKE_PATH,
        UNSUPPORTED_BAKE,
        NO_CAMERAS,
        FRAME_NO_PRODUCT,
        NO_CAMERA_TO_REMOVE,
        NO_LIGHT_TO_REMOVE,
        NO_CAMERAS_TO_CLEAR,
        LIGHT_DRAW_NEEDS_VIEWPORT,
        LIGHT_DRAW_NO_LIGHTS,
        LIGHT_DRAW_LIGHT_MISSING,
        NO_MAIN_CAMERA,
        TURNTABLE_NO_SETUP,
        TURNTABLE_NOTHING_TO_CLEAR,
        BATCH_NO_MESH,
        BATCH_NO_CAMERA,
        BATCH_NO_SHOTS,
        BATCH_NOTHING,
        UPDATE_CHECK_OFFLINE,
        UPDATE_CHECK_UNAVAILABLE,
        NO_SHOTS,
        NO_SHOT_TO_APPLY,
        NO_SHOT_TO_REMOVE,
        NO_SHOT_TO_RENAME,
        SHOT_NAME_EMPTY,
        FALSE_COLOR_UNAVAILABLE,
        NO_VIEW_SETTINGS,
        NO_COMPOSITOR,
        LOOK_COMPOSITOR_BUSY,
    }
)


def em_dash_join(title: str, next_step: str) -> str:
    """Title plus the next action, matching N-panel empty-state CTAs."""
    return f"{title} — {next_step}"


def warning_set() -> set[str]:
    return {WARNING}


def error_set() -> set[str]:
    return {ERROR}


def report_type(message: str) -> str:
    """WARNING for missing-prerequisite copy, ERROR for hard failures."""
    if message in EMPTY_STATE_MESSAGES:
        return WARNING
    if message.startswith(
        (
            "File not found:",
            "Unsupported file type:",
            "HDRI file not found:",
            "Unsupported HDRI:",
            "Unsupported bake format:",
            "Shot name “",
            "Shot camera “",
            "Batch export ",
        )
    ):
        return WARNING
    return ERROR


def report_set(message: str) -> set[str]:
    return {report_type(message)}


def named_missing(kind: str, name: str, *, next_step: str) -> str:
    shown = name.strip() or kind.lower()
    return f"{kind} “{shown}” is gone — {next_step}"


def light_not_found(name: str) -> str:
    return named_missing("Light", name, next_step=NO_LIGHTS_NEXT)


def unknown_light_preset_message(preset_id: str) -> str:
    shown = (preset_id or "").strip()
    if not shown:
        return UNKNOWN_LIGHT_PRESET
    return (
        f"Unknown light shape “{shown}” — "
        "pick Softbox, Strip, Octa, Hard, or Rim"
    )


def unknown_look_preset_message(preset_id: str) -> str:
    return unknown_look_message(preset_id)


def camera_not_found(name: str) -> str:
    return named_missing("Camera", name, next_step=NO_CAMERAS_NEXT)


def shot_not_found(name: str) -> str:
    return named_missing("Shot", name, next_step=NO_SHOTS_NEXT)


def shot_camera_missing(name: str) -> str:
    return named_missing(
        "Shot camera",
        name,
        next_step="Add Camera or pick another shot",
    )


def bookmark_camera_missing(name: str) -> str:
    return named_missing(
        "Bookmarked camera",
        name,
        next_step="Bookmark again or Add Camera",
    )


def file_not_found_message(filepath: str) -> str:
    name = os.path.basename(filepath) or filepath or "that file"
    return f"File not found: {name} — choose an existing product file"


def unsupported_file_message(ext: str) -> str:
    shown = (ext or "").strip() or "this file"
    return (
        f"Unsupported file type: {shown} — "
        "use OBJ, FBX, STL, GLB, 3MF, or STEP/IGES"
    )


def hdri_file_not_found(filepath: str) -> str:
    name = os.path.basename(filepath) or filepath or "that HDRI"
    return f"HDRI file not found: {name} — choose an existing .hdr / .exr"


def unsupported_hdri_message(ext: str) -> str:
    shown = (ext or "").strip() or "this file"
    return f"Unsupported HDRI: {shown} — use HDR, EXR, or a still image"


def hdri_loaded_message(filepath: str) -> str:
    name = os.path.basename(filepath) or filepath or "HDRI"
    return f"HDRI loaded: {name}"


def bake_hdri_message(filepath: str, *, applied: bool = False) -> str:
    return baked_message(filepath, applied=applied)


def update_failure_report(copy: dict[str, str]) -> str:
    """Compose updates.core describe_failure dicts into operator copy."""
    line = (copy.get("line") or "").strip()
    detail = (copy.get("detail") or "").strip()
    if line and detail:
        return em_dash_join(line, detail)
    return line or detail
