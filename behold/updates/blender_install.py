# SPDX-License-Identifier: GPL-3.0-or-later
"""Install a downloaded ``behold-*.zip`` via Blender 5.2 extension / add-on ops."""

from __future__ import annotations

from typing import Any, Literal, Never

import bpy

from ..preferences import addon_id
from .core import (
    ADDON_ENABLE_OP,
    ADDON_INSTALL_OP,
    EXTENSIONS_INSTALL_OP,
    RESTART_MESSAGE,
    addon_install_kwargs,
    extensions_install_kwargs,
    pick_install_operator,
)

InstallOp = Literal[
    "extensions.package_install_files",
    "preferences.addon_install",
]


def _operator_from_id(op_id: str):
    path, name = op_id.split(".", 1)
    return getattr(getattr(bpy.ops, path), name)


def _rna_property_ids(op) -> frozenset[str] | None:
    try:
        rna = op.get_rna_type()
        return frozenset(prop.identifier for prop in rna.properties)
    except Exception:  # noqa: BLE001 — RNA is optional in tests / older builds
        return None


def _available_ops() -> list[str]:
    names: list[str] = []
    for op_id in (EXTENSIONS_INSTALL_OP, ADDON_INSTALL_OP):
        try:
            _operator_from_id(op_id)
        except AttributeError:
            continue
        names.append(op_id)
    return names


def _call_install(op_id: InstallOp, filepath: str) -> Any:
    op = _operator_from_id(op_id)
    known = _rna_property_ids(op)
    if op_id == EXTENSIONS_INSTALL_OP:
        kwargs = extensions_install_kwargs(filepath, known)
    elif op_id == ADDON_INSTALL_OP:
        kwargs = addon_install_kwargs(filepath, known)
    else:
        unreachable: Never = op_id
        raise RuntimeError(f"unhandled install operator: {unreachable}")
    return op("EXEC_DEFAULT", **kwargs)


def _enable_behold() -> None:
    try:
        enable = _operator_from_id(ADDON_ENABLE_OP)
    except AttributeError:
        return
    modules = (addon_id(), "behold")
    for module in modules:
        try:
            enable(module=module)
            return
        except Exception:  # noqa: BLE001 — enable is best-effort; restart still required
            continue


def install_zip_file(filepath: str) -> dict[str, Any]:
    """Install from disk, then tell the artist to restart.

    Blender 5.2: ``extensions.package_install_files`` (Install from Disk) with
    ``repo='user_default'``, ``overwrite=True``, ``enable_on_install=True``.
    Older 4.2+ zips fall back to ``preferences.addon_install``.
    Replacing a loaded add-on in-place is fragile, so a restart is always required.
    """
    picked = pick_install_operator(_available_ops())
    if picked is None:
        return {
            "ok": False,
            "method": "",
            "message": (
                "Blender has no Install from Disk operator. "
                "Open release, download behold-*.zip, then Preferences → Install from Disk."
            ),
        }
    chosen: InstallOp = (
        EXTENSIONS_INSTALL_OP
        if picked == EXTENSIONS_INSTALL_OP
        else ADDON_INSTALL_OP
    )
    try:
        result = _call_install(chosen, filepath)
    except Exception as exc:  # noqa: BLE001
        if chosen == EXTENSIONS_INSTALL_OP:
            try:
                result = _call_install(ADDON_INSTALL_OP, filepath)
                chosen = ADDON_INSTALL_OP
            except Exception as fallback_exc:  # noqa: BLE001
                return {
                    "ok": False,
                    "method": chosen,
                    "message": f"Install failed: {fallback_exc or exc}",
                }
        else:
            return {
                "ok": False,
                "method": chosen,
                "message": f"Install failed: {exc}",
            }

    if result is not None and "FINISHED" not in result and "CANCELLED" in result:
        return {
            "ok": False,
            "method": chosen,
            "message": (
                "Install from Disk did not finish. "
                "Open release, download behold-*.zip, then Preferences → Install from Disk."
            ),
        }

    if chosen == ADDON_INSTALL_OP:
        _enable_behold()

    return {
        "ok": True,
        "method": chosen,
        "message": f"Installed the zip. {RESTART_MESSAGE}",
    }
