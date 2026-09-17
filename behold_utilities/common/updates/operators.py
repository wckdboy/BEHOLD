# SPDX-License-Identifier: GPL-3.0-or-later
"""Update check / install / open-release / dismiss operators.

Each suite add-on registers unique RNA ids so four zips can load together.
"""

from __future__ import annotations

import bpy
from bpy.types import Context, Operator

from ..brand import RELEASES_URL, package_slug_from
from ..messages import update_failure_report
from ..prefs import get_prefs
from . import runtime
from .core import (
    RESTART_MESSAGE,
    available_from_cache,
    describe_failure,
    installed_version,
    is_allowed_download_url,
)


def _slug() -> str:
    return package_slug_from(__package__)


def _ns() -> str:
    return f"behold_{_slug()}"


def _cache_update(context: Context) -> dict[str, str] | None:
    prefs = get_prefs(context, __package__)
    if prefs is None:
        return None
    return available_from_cache(
        getattr(prefs, "update_latest_tag", "") or "",
        installed=installed_version(),
        html_url=getattr(prefs, "update_latest_url", "") or "",
        zip_url=getattr(prefs, "update_latest_zip_url", "") or "",
    )


def build_classes() -> tuple[type, ...]:
    slug = _slug()
    ns = _ns()
    prefix = f"BEHOLD_{slug.upper()}_OT"

    class CheckUpdates(Operator):
        bl_idname = f"{ns}.check_updates"
        bl_label = "Check for updates"
        bl_description = (
            "Ask GitHub if a newer BEHOLD suite release exists. "
            "Runs in the background and never sends a token"
        )
        bl_options = {"REGISTER"}

        def execute(self, context: Context):
            prefs = get_prefs(context, __package__)
            if prefs is not None:
                prefs.update_checking = True
                prefs.update_last_error = ""
                prefs.update_error_kind = ""
            runtime.request_check(force=True)
            self.report({"INFO"}, "Checking GitHub for a newer BEHOLD…")
            return {"FINISHED"}

    class InstallUpdate(Operator):
        bl_idname = f"{ns}.install_update"
        bl_label = "Install update"
        bl_description = (
            "Download this add-on's zip from the GitHub release and install it. "
            "Restart Blender afterward"
        )
        bl_options = {"REGISTER"}

        def execute(self, context: Context):
            prefs = get_prefs(context, __package__)
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
                self.report({"ERROR"}, update_failure_report(copy))
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

    class OpenRelease(Operator):
        bl_idname = f"{ns}.open_release"
        bl_label = "Open release"
        bl_description = "Open the GitHub Releases page for this BEHOLD version"
        bl_options = {"REGISTER"}

        def execute(self, context: Context):
            update = _cache_update(context)
            url = (update or {}).get("url") or RELEASES_URL
            bpy.ops.wm.url_open(url=url)
            return {"FINISHED"}

    class DismissUpdate(Operator):
        bl_idname = f"{ns}.dismiss_update"
        bl_label = "Dismiss update notice"
        bl_description = "Hide the update notice until you restart Blender"
        bl_options = {"REGISTER"}

        def execute(self, context: Context):
            del context
            runtime.dismiss_notice()
            return {"FINISHED"}

    CheckUpdates.__name__ = f"{prefix}_check_updates"
    InstallUpdate.__name__ = f"{prefix}_install_update"
    OpenRelease.__name__ = f"{prefix}_open_release"
    DismissUpdate.__name__ = f"{prefix}_dismiss_update"
    return (CheckUpdates, InstallUpdate, OpenRelease, DismissUpdate)


CLASSES: tuple[type, ...] | None = None


def register() -> None:
    global CLASSES
    CLASSES = build_classes()
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    global CLASSES
    if not CLASSES:
        return
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    CLASSES = None
