# SPDX-License-Identifier: GPL-3.0-or-later
"""Update check / install / open-release / dismiss operators."""

from __future__ import annotations

import bpy
from bpy.types import Context, Operator

from ..brand import RELEASES_URL
from ..preferences import get_prefs
from . import runtime
from .core import (
    RESTART_MESSAGE,
    available_from_cache,
    describe_failure,
    installed_version,
    is_allowed_download_url,
)


def _cache_update(context: Context) -> dict[str, str] | None:
    prefs = get_prefs(context)
    if prefs is None:
        return None
    return available_from_cache(
        getattr(prefs, "update_latest_tag", "") or "",
        installed=installed_version(),
        html_url=getattr(prefs, "update_latest_url", "") or "",
        zip_url=getattr(prefs, "update_latest_zip_url", "") or "",
    )


class BEHOLD_OT_check_updates(Operator):
    bl_idname = "behold.check_updates"
    bl_label = "Check for updates"
    bl_description = (
        "Ask GitHub if a newer BEHOLD release exists. "
        "Runs in the background and never sends a token"
    )
    bl_options = {"REGISTER"}

    def execute(self, context: Context):
        prefs = get_prefs(context)
        if prefs is not None:
            prefs.update_checking = True
            prefs.update_last_error = ""
            prefs.update_error_kind = ""
        runtime.request_check(force=True)
        self.report({"INFO"}, "Checking GitHub for a newer BEHOLD…")
        return {"FINISHED"}


class BEHOLD_OT_install_update(Operator):
    bl_idname = "behold.install_update"
    bl_label = "Install update"
    bl_description = (
        "Download the behold-*.zip from the GitHub release and install it. "
        "Restart Blender afterward"
    )
    bl_options = {"REGISTER"}

    def execute(self, context: Context):
        prefs = get_prefs(context)
        update = _cache_update(context)
        zip_url = ""
        if prefs is not None:
            zip_url = getattr(prefs, "update_latest_zip_url", "") or ""
        if update and update.get("zip_url"):
            zip_url = update["zip_url"]
        if not is_allowed_download_url(zip_url):
            copy = describe_failure("no_zip")
            if prefs is not None:
                prefs.update_installing = False
                prefs.update_last_error = copy["line"]
                prefs.update_error_kind = copy["kind"]
            self.report({"ERROR"}, f"{copy['line']}. {copy['detail']}")
            return {"CANCELLED"}
        if prefs is not None:
            prefs.update_installing = True
            prefs.update_last_error = ""
            prefs.update_error_kind = ""
        runtime.request_install()
        version = update["version"] if update else "update"
        self.report(
            {"INFO"},
            f"Downloading BEHOLD {version}… {RESTART_MESSAGE}",
        )
        return {"FINISHED"}


class BEHOLD_OT_open_release(Operator):
    bl_idname = "behold.open_release"
    bl_label = "Open release"
    bl_description = "Open the GitHub Releases page for this BEHOLD version"
    bl_options = {"REGISTER"}

    def execute(self, context: Context):
        update = _cache_update(context)
        url = (update or {}).get("url") or RELEASES_URL
        bpy.ops.wm.url_open(url=url)
        return {"FINISHED"}


class BEHOLD_OT_dismiss_update(Operator):
    bl_idname = "behold.dismiss_update"
    bl_label = "Dismiss update notice"
    bl_description = "Hide the update notice until you restart Blender"
    bl_options = {"REGISTER"}

    def execute(self, context: Context):
        del context
        runtime.dismiss_notice()
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_check_updates,
    BEHOLD_OT_install_update,
    BEHOLD_OT_open_release,
    BEHOLD_OT_dismiss_update,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
