# SPDX-License-Identifier: GPL-3.0-or-later
"""STEPper NEXT constants and bpy-free helpers.

Verified against Peak-Design/STEPper_NEXT ``main.py`` / ``worker.py``
(extension ``id = "stepper_next"``, ``blender_version_min = "5.1.0"``):

- Operator: ``import_scene.occ_import_step``
- Scripted call: ``filepath`` (absolute) + ``override_file`` (basename)
- ``override_file`` keeps ``ImportStepCADOperator.execute`` on the synchronous
  path (it skips ``stepper.background_import``)
- Optional RNA on that operator includes ``quality_preset``,
  ``lin_deflection_len``, ``lin_deflection``, ``directory``

Do not invent kwargs. Filter extras to RNA identifiers when they are known.
"""

from __future__ import annotations

import os
from typing import Any, Iterable, Literal, Mapping, Never

CadBackend = Literal["STEPPER", "OCP", "NONE"]

STEPPER_EXTENSION_ID = "stepper_next"
STEPPER_REPO_URL = "https://github.com/Peak-Design/STEPper_NEXT"
STEPPER_INSTALL_URL = "https://github.com/Peak-Design/STEPper_NEXT/releases"

STEPPER_OCC_IMPORT_OP = "import_scene.occ_import_step"
STEPPER_BACKGROUND_OP = "stepper.background_import"

# BEHOLD calls the documented synchronous operator only. Background exists in
# STEPper NEXT but is not used from this add-on (override_file keeps us sync).
STEPPER_IMPORT_OPS = (STEPPER_OCC_IMPORT_OP,)

STEPPER_MODULE_CANDIDATES = (
    "bl_ext.user_default.stepper_next",
    "bl_ext.blender_org.stepper_next",
    "bl_ext.vscode_default.stepper_next",
    "stepper_next",
    "STEPper_NEXT",
    "stepper",
)

STEPPER_OCC_REQUIRED_KWARGS = frozenset({"filepath", "override_file"})
STEPPER_OCC_OPTIONAL_KWARGS = frozenset(
    {
        "directory",
        "quality_preset",
        "lin_deflection_len",
        "lin_deflection",
        "ang_deflection",
        "ang_deflection_rot",
    }
)

DEFAULT_QUALITY_PRESET = "BALANCED"


def is_stepper_module_name(name: str) -> bool:
    """True for STEPper NEXT extension / legacy module ids."""
    lowered = name.lower().replace("-", "_")
    if lowered == STEPPER_EXTENSION_ID or lowered.endswith(f".{STEPPER_EXTENSION_ID}"):
        return True
    if lowered == "stepper" or lowered.endswith(".stepper"):
        return True
    if "stepper" in lowered and "next" in lowered:
        return True
    return False


def pick_stepper_module(names: Iterable[str]) -> str | None:
    """Pick the best STEPper module id from an iterable of addon names."""
    available = [name for name in names if name]
    lookup = set(available)
    for candidate in STEPPER_MODULE_CANDIDATES:
        if candidate in lookup:
            return candidate
    for name in available:
        if is_stepper_module_name(name) and name.startswith("bl_ext."):
            return name
    for name in available:
        if is_stepper_module_name(name):
            return name
    for name in available:
        if "stepper" in name.lower():
            return name
    return None


def filter_kwargs_to_known_props(
    kwargs: Mapping[str, Any],
    known_props: frozenset[str] | None,
) -> dict[str, Any]:
    """Keep required STEPper kwargs plus any extras that exist on the operator."""
    if known_props is None:
        return dict(kwargs)
    return {
        key: value
        for key, value in kwargs.items()
        if key in STEPPER_OCC_REQUIRED_KWARGS or key in known_props
    }


def stepper_occ_import_kwargs(
    filepath: str,
    *,
    known_props: frozenset[str] | None = None,
    quality_preset: str | None = DEFAULT_QUALITY_PRESET,
    lin_deflection_len: float | None = None,
) -> dict[str, Any]:
    """Build ``occ_import_step`` kwargs. Never includes invented RNA names."""
    abs_path = os.path.abspath(filepath)
    kwargs: dict[str, Any] = {
        "filepath": abs_path,
        "override_file": os.path.basename(abs_path),
        "directory": os.path.dirname(abs_path),
    }
    if quality_preset:
        kwargs["quality_preset"] = quality_preset
    if lin_deflection_len is not None:
        kwargs["lin_deflection_len"] = lin_deflection_len
    return filter_kwargs_to_known_props(kwargs, known_props)


def stepper_occ_import_attempts(
    filepath: str,
    *,
    known_props: frozenset[str] | None = None,
    quality_preset: str | None = DEFAULT_QUALITY_PRESET,
    lin_deflection_len: float | None = None,
) -> tuple[dict[str, Any], ...]:
    """Canonical call, then strip optional RNA if a TypeError is possible."""
    full = stepper_occ_import_kwargs(
        filepath,
        known_props=known_props,
        quality_preset=quality_preset,
        lin_deflection_len=lin_deflection_len,
    )
    required = {
        "filepath": full["filepath"],
        "override_file": full["override_file"],
    }
    with_directory = dict(required)
    if "directory" in full:
        with_directory["directory"] = full["directory"]
    attempts = (full, with_directory, required)
    unique: list[dict[str, Any]] = []
    seen: set[tuple[tuple[str, Any], ...]] = set()
    for kwargs in attempts:
        key = tuple(sorted(kwargs.items()))
        if key in seen:
            continue
        seen.add(key)
        unique.append(kwargs)
    return tuple(unique)


def import_panel_copy(
    backend: CadBackend,
    *,
    stepper_needs_enable: bool = False,
) -> dict[str, Any]:
    """First-ship Import panel strings. No bpy."""
    if backend == "STEPPER":
        detail = (
            "Installed — will enable on Import Product"
            if stepper_needs_enable
            else "CAD files import via STEPper NEXT"
        )
        return {
            "line": "STEPper NEXT ready",
            "detail": detail,
            "show_install": False,
            "install_label": "Install STEPper NEXT",
        }
    if backend == "OCP":
        return {
            "line": "OCP fallback",
            "detail": "Install STEPper NEXT for CAD on 5.1+/5.2 LTS",
            "show_install": True,
            "install_label": "Install STEPper NEXT",
        }
    if backend == "NONE":
        return {
            "line": "Install STEPper NEXT",
            "detail": "Required for STEP/IGES/BREP — mesh formats never need it",
            "show_install": True,
            "install_label": "Install STEPper NEXT",
        }
    unreachable: Never = backend
    raise RuntimeError(f"unhandled CAD backend: {unreachable}")


def missing_cad_backend_message() -> str:
    return (
        "No CAD backend. Install STEPper NEXT for Blender 5.1+/5.2 LTS: "
        f"{STEPPER_INSTALL_URL} "
        "(Preferences → Get Extensions → Install from Disk). "
        "Mesh files (OBJ/FBX/STL/GLB/3MF) never need STEPper. "
        "Optional OCP fallback: cadquery-ocp / cadquery-ocp-novtk in Blender's Python."
    )


def stepper_enable_failed_message(module: str, error: str) -> str:
    return (
        f"STEPper NEXT is installed as {module} but could not be enabled ({error}). "
        "Enable it in Preferences → Add-ons, or reinstall from "
        f"{STEPPER_INSTALL_URL}"
    )


def stepper_operator_failed_message(detail: str) -> str:
    return (
        f"STEPper NEXT import failed: {detail}. "
        "Confirm STEPper NEXT (Blender 5.1+/5.2 LTS) is enabled, or install from "
        f"{STEPPER_INSTALL_URL}"
    )


def stepper_no_mesh_message() -> str:
    return (
        "STEPper NEXT finished but produced no mesh objects. "
        "Check the STEP/IGES/BREP file, or File → Import → "
        "STEP/IGES/BREP CAD [STEPper NEXT]."
    )
