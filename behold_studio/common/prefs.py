# SPDX-License-Identifier: GPL-3.0-or-later
"""Add-on id / preferences lookup that works for classic and extension installs."""

from __future__ import annotations

from typing import Any


def package_root(package: str | None) -> str:
    """Top-level add-on module: ``behold_studio`` or ``bl_ext.repo.behold_studio``."""
    parts = [part for part in (package or "").split(".") if part]
    if not parts:
        return "behold"
    if parts[0] == "bl_ext" and len(parts) >= 3:
        return ".".join(parts[:3])
    if "common" in parts:
        return ".".join(parts[: parts.index("common")])
    return parts[0]


def addon_id_from(package: str | None) -> str:
    return package_root(package)


def get_prefs(context: Any, package: str | None = None):
    addons = context.preferences.addons
    wanted = addon_id_from(package)
    addon = addons.get(wanted)
    if addon is None and wanted.startswith("bl_ext."):
        addon = addons.get(wanted.rsplit(".", 1)[-1])
    if addon is None:
        for key in (
            "behold_product",
            "behold_studio",
            "behold_lighting",
            "behold_utilities",
            "behold",
        ):
            addon = addons.get(key)
            if addon is not None:
                break
    if addon is None:
        return None
    return addon.preferences
