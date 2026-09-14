# SPDX-License-Identifier: GPL-3.0-or-later
"""Operator reports and empty-state copy — no Blender import.

Each failure is a short sentence plus what to do next. Empty-state CTAs
and operator reports share these strings so the N-panel and the Info bar
do not disagree.
"""

from __future__ import annotations

import os

from ..materials.presets import EMPTY_NO_MESH, EMPTY_NO_MESH_HINT
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

NO_LIGHTS_TITLE = "No BEHOLD lights yet"
NO_LIGHTS_NEXT = "Build Studio or Add Light"
NO_LIGHTS = f"{NO_LIGHTS_TITLE} — {NO_LIGHTS_NEXT}"
NO_LIGHTS_HINT = "Build Studio to seed Key, Fill, and Rim"

NO_CAMERAS_TITLE = "No BEHOLD cameras yet"
NO_CAMERAS_NEXT = "Build Studio or Add Camera"
NO_CAMERAS = f"{NO_CAMERAS_TITLE} — {NO_CAMERAS_NEXT}"
NO_CAMERAS_HINT = "Build Studio to add a framed product camera"

FRAME_NO_PRODUCT = "No product to frame — select the mesh or Import Product"
NO_CAMERA_TO_REMOVE = "No BEHOLD camera to remove — Build Studio or Add Camera"
NO_LIGHT_TO_REMOVE = "No BEHOLD light to remove — Build Studio or Add Light"
NO_CAMERAS_TO_CLEAR = "No BEHOLD cameras to clear — Build Studio or Add Camera"

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
BATCH_NO_MESH = "No mesh selected for batch — select the product or Import Product"

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
        NO_LIGHTS,
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
        UPDATE_CHECK_OFFLINE,
        UPDATE_CHECK_UNAVAILABLE,
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
    if message.startswith(("File not found:", "Unsupported file type:")):
        return WARNING
    return ERROR


def report_set(message: str) -> set[str]:
    return {report_type(message)}


def named_missing(kind: str, name: str, *, next_step: str) -> str:
    shown = name.strip() or kind.lower()
    return f"{kind} “{shown}” is gone — {next_step}"


def light_not_found(name: str) -> str:
    return named_missing("Light", name, next_step=NO_LIGHTS_NEXT)


def camera_not_found(name: str) -> str:
    return named_missing("Camera", name, next_step=NO_CAMERAS_NEXT)


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


def update_failure_report(copy: dict[str, str]) -> str:
    """Compose updates.core describe_failure dicts into operator copy."""
    line = (copy.get("line") or "").strip()
    detail = (copy.get("detail") or "").strip()
    if line and detail:
        return em_dash_join(line, detail)
    return line or detail
