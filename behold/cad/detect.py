# SPDX-License-Identifier: GPL-3.0-or-later
"""Detect STEPper NEXT and optional OCP (OpenCASCADE) bindings."""

from __future__ import annotations

from typing import Any

import bpy

from . import ocp_core
from . import stepper_api
from .stepper_api import (
    STEPPER_IMPORT_OPS,
    STEPPER_INSTALL_URL,
    STEPPER_MODULE_CANDIDATES,
    STEPPER_OCC_IMPORT_OP,
    import_panel_copy,
    is_stepper_module_name,
    missing_cad_backend_message,
    pick_stepper_module,
    stepper_enable_failed_message,
)


def _unique_names(names: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for name in names:
        if name and name not in seen:
            seen.add(name)
            ordered.append(name)
    return ordered


def installed_addon_module_names() -> list[str]:
    """Enabled add-ons plus installed-but-disabled modules (extensions too)."""
    names: list[str] = []
    try:
        names.extend(bpy.context.preferences.addons.keys())
    except Exception:  # noqa: BLE001
        pass

    try:
        import addon_utils

        for mod in addon_utils.modules():
            names.append(getattr(mod, "__name__", "") or "")
    except Exception:  # noqa: BLE001
        pass

    try:
        import pkgutil

        import bl_ext

        for repo in pkgutil.iter_modules(list(getattr(bl_ext, "__path__", []))):
            repo_mod_name = f"bl_ext.{repo.name}"
            try:
                repo_mod = __import__(repo_mod_name, fromlist=["*"])
            except Exception:  # noqa: BLE001
                continue
            for ext in pkgutil.iter_modules(list(getattr(repo_mod, "__path__", []))):
                names.append(f"{repo_mod_name}.{ext.name}")
    except Exception:  # noqa: BLE001
        pass

    return _unique_names(names)


def enabled_addon_module_names() -> list[str]:
    try:
        return _unique_names(list(bpy.context.preferences.addons.keys()))
    except Exception:  # noqa: BLE001
        return []


def find_stepper_module() -> str | None:
    """Installed STEPper NEXT module id (enabled or disabled)."""
    return pick_stepper_module(installed_addon_module_names())


def find_enabled_stepper_module() -> str | None:
    return pick_stepper_module(enabled_addon_module_names())


def stepper_operator_available() -> str | None:
    """Return ``import_scene.occ_import_step`` if the operator is registered."""
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
    return ocp_core.probe_ocp()


def ensure_stepper_enabled() -> dict[str, Any]:
    """Enable STEPper NEXT if it is installed but disabled. Never raises."""
    operator = stepper_operator_available()
    if operator == STEPPER_OCC_IMPORT_OP:
        return {
            "ok": True,
            "installed": True,
            "module": find_stepper_module() or find_enabled_stepper_module(),
            "operator": operator,
            "error": None,
        }

    module = find_stepper_module()
    if module is None:
        return {
            "ok": False,
            "installed": False,
            "module": None,
            "operator": None,
            "error": None,
        }

    try:
        bpy.ops.preferences.addon_enable(module=module)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "installed": True,
            "module": module,
            "operator": None,
            "error": stepper_enable_failed_message(module, str(exc)),
        }

    operator = stepper_operator_available()
    if operator == STEPPER_OCC_IMPORT_OP:
        return {
            "ok": True,
            "installed": True,
            "module": module,
            "operator": operator,
            "error": None,
        }

    return {
        "ok": False,
        "installed": True,
        "module": module,
        "operator": operator,
        "error": stepper_enable_failed_message(
            module,
            f"{STEPPER_OCC_IMPORT_OP} is not registered after enable",
        ),
    }


def cad_status() -> dict[str, Any]:
    """High-level CAD backend status for the UI. Does not enable add-ons."""
    stepper_mod = find_stepper_module()
    stepper_enabled = find_enabled_stepper_module()
    stepper_op = stepper_operator_available()
    ocp = probe_ocp()
    needs_enable = (
        stepper_mod is not None
        and stepper_enabled is None
        and stepper_op != STEPPER_OCC_IMPORT_OP
    )

    if stepper_mod is not None or stepper_op == STEPPER_OCC_IMPORT_OP:
        copy = import_panel_copy("STEPPER", stepper_needs_enable=needs_enable)
        return {
            "backend": "STEPPER",
            "label": copy["line"],
            "detail": copy["detail"],
            "can_import": True,
            "stepper_module": stepper_mod,
            "stepper_operator": stepper_op,
            "stepper_needs_enable": needs_enable,
            "ocp": ocp,
        }

    if ocp["available"]:
        copy = import_panel_copy("OCP")
        return {
            "backend": "OCP",
            "label": copy["line"],
            "detail": copy["detail"],
            "can_import": True,
            "stepper_module": None,
            "stepper_operator": None,
            "stepper_needs_enable": False,
            "ocp": ocp,
        }

    copy = import_panel_copy("NONE")
    return {
        "backend": "NONE",
        "label": copy["line"],
        "detail": copy["detail"],
        "can_import": False,
        "stepper_module": None,
        "stepper_operator": None,
        "stepper_needs_enable": False,
        "ocp": ocp,
        "message": missing_cad_backend_message(),
    }


__all__ = (
    "STEPPER_IMPORT_OPS",
    "STEPPER_INSTALL_URL",
    "STEPPER_MODULE_CANDIDATES",
    "STEPPER_OCC_IMPORT_OP",
    "cad_status",
    "ensure_stepper_enabled",
    "find_enabled_stepper_module",
    "find_stepper_module",
    "import_panel_copy",
    "installed_addon_module_names",
    "is_stepper_module_name",
    "missing_cad_backend_message",
    "pick_stepper_module",
    "probe_ocp",
    "stepper_api",
    "stepper_operator_available",
)
