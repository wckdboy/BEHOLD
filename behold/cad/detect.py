# SPDX-License-Identifier: GPL-3.0-or-later
"""Detect STEPper NEXT and optional OCP (OpenCASCADE) bindings."""

from __future__ import annotations

from typing import Any

import bpy


STEPPER_INSTALL_URL = "https://github.com/Peak-Design/STEPper_NEXT"

STEPPER_MODULE_CANDIDATES = (
    "bl_ext.user_default.stepper_next",
    "bl_ext.blender_org.stepper_next",
    "stepper_next",
    "STEPper_NEXT",
    "stepper",
)

# STEPper NEXT uses import_scene.occ_import_step (see Peak-Design/STEPper_NEXT worker.py).
STEPPER_IMPORT_OPS = (
    "import_scene.occ_import_step",
    "stepper.background_import",
)


def find_stepper_module() -> str | None:
    addons = bpy.context.preferences.addons.keys()
    for name in STEPPER_MODULE_CANDIDATES:
        if name in addons:
            return name
    for name in addons:
        if "stepper" in name.lower():
            return name
    return None


def stepper_operator_available() -> str | None:
    """Return the first available STEPper import operator id, if any."""
    for op_id in STEPPER_IMPORT_OPS:
        try:
            path, name = op_id.split(".", 1)
            category = getattr(bpy.ops, path, None)
            if category is None:
                continue
            if getattr(category, name, None) is not None:
                return op_id
        except Exception:  # noqa: BLE001
            continue
    return None


def probe_ocp() -> dict[str, Any]:
    """Try importing OCP. Never raises."""
    try:
        import OCP  # noqa: F401
        from OCP.STEPControl import STEPControl_Reader  # noqa: F401

        return {
            "available": True,
            "label": "OCP ready",
            "detail": "OpenCASCADE (OCP) bindings found — BEHOLD can import STEP itself.",
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "available": False,
            "label": "OCP not installed",
            "detail": (
                "Install STEPper NEXT from github.com/Peak-Design/STEPper_NEXT "
                "(Blender 5.1+) or add cadquery-ocp / cadquery-ocp-novtk into "
                f"Blender's Python. ({type(exc).__name__})"
            ),
        }


def cad_status() -> dict[str, Any]:
    """High-level CAD backend status for the UI."""
    stepper_mod = find_stepper_module()
    stepper_op = stepper_operator_available()
    ocp = probe_ocp()

    if stepper_mod is not None or stepper_op is not None:
        return {
            "backend": "STEPPER",
            "label": "STEPper NEXT detected",
            "detail": "Imports will hand off to STEPper NEXT, then Material Assist.",
            "can_import": True,
            "stepper_module": stepper_mod,
            "stepper_operator": stepper_op,
            "ocp": ocp,
        }

    if ocp["available"]:
        return {
            "backend": "OCP",
            "label": "BEHOLD OCP importer",
            "detail": "No STEPper NEXT — using BEHOLD's OpenCASCADE path.",
            "can_import": True,
            "stepper_module": None,
            "stepper_operator": None,
            "ocp": ocp,
        }

    return {
        "backend": "NONE",
        "label": "No CAD backend",
        "detail": ocp["detail"],
        "can_import": False,
        "stepper_module": None,
        "stepper_operator": None,
        "ocp": ocp,
    }
