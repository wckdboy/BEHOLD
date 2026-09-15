# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD add-on preferences — branding, docs, lean scene defaults."""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import AddonPreferences, Context, UILayout

from .brand import (
    DOCS_URL,
    PRODUCT_CREDIT,
    PRODUCT_NAME,
    PRODUCT_TAGLINE,
    RELEASES_URL,
    VERSION,
)
from .previews import draw_mark_label
from .updates.core import (
    available_from_cache,
    installed_version,
    prefs_status_copy,
    version_string,
)


def _on_enable_utilities(self, context: Context) -> None:
    # Imported here to avoid a preferences ↔ utilities import cycle.
    from . import utilities

    utilities.sync_registration(bool(self.enable_utilities))
    window_manager = getattr(context, "window_manager", None)
    if window_manager is None:
        return
    for window in window_manager.windows:
        screen = window.screen
        if screen is None:
            continue
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def addon_id() -> str:
    """Classic `behold` or Blender 4.2+ extension `bl_ext.<repo>.behold`."""
    pkg = __package__ or "behold"
    parts = pkg.split(".")
    if parts[0] == "bl_ext" and len(parts) >= 3:
        return ".".join(parts[:3])
    return parts[0]


def get_prefs(context: Context):
    addons = context.preferences.addons
    addon = addons.get(addon_id())
    if addon is None:
        addon = addons.get("behold")
    if addon is None:
        return None
    return addon.preferences


class BEHOLDAddonPreferences(AddonPreferences):
    bl_idname = addon_id()

    show_header_shortcuts: BoolProperty(
        name="3D View header shortcuts",
        description="Show BEHOLD pie + Import / Build / Still on the 3D Viewport header",
        default=True,
    )
    show_flow_strip: BoolProperty(
        name="Workflow strip",
        description="Show Import → Studio → Dress → Shoot on the BEHOLD sidebar",
        default=True,
    )
    enable_utilities: BoolProperty(
        name="Utilities panel",
        description=(
            "Show the Utilities N-panel (Danish wall, balcony mounts, "
            "eave / roof sections). "
            "Off by default — not part of Import → Studio → Lights → "
            "Materials → Cameras → Shoot"
        ),
        default=False,
        update=_on_enable_utilities,
    )
    check_for_updates: BoolProperty(
        name="Check for updates",
        description=(
            "Ask GitHub once a day if a newer BEHOLD release exists, and show "
            "a notice in the sidebar. Public API only — no token is sent"
        ),
        default=True,
    )
    update_last_check: StringProperty(
        name="Last update check",
        description="Date of the last GitHub check (BEHOLD manages this)",
        default="",
        options={"HIDDEN"},
    )
    update_latest_tag: StringProperty(
        name="Latest release tag",
        description="Newest stable tag seen on GitHub (BEHOLD manages this)",
        default="",
        options={"HIDDEN"},
    )
    update_latest_url: StringProperty(
        name="Latest release page",
        description="GitHub release page for the newest tag (BEHOLD manages this)",
        default="",
        options={"HIDDEN"},
    )
    update_latest_zip_url: StringProperty(
        name="Latest release zip",
        description="behold-*.zip download URL (BEHOLD manages this)",
        default="",
        options={"HIDDEN"},
    )
    update_last_error: StringProperty(
        name="Update check error",
        description="Last GitHub error, if any (BEHOLD manages this)",
        default="",
        options={"HIDDEN"},
    )
    update_error_kind: StringProperty(
        name="Update error kind",
        description="network / github / download / install / no_zip (BEHOLD manages this)",
        default="",
        options={"HIDDEN"},
    )
    update_checking: BoolProperty(
        name="Update check in progress",
        default=False,
        options={"HIDDEN"},
    )
    update_installing: BoolProperty(
        name="Update install in progress",
        default=False,
        options={"HIDDEN"},
    )

    def draw(self, context: Context) -> None:
        layout = self.layout
        _draw_branding(layout)
        _draw_links(layout)
        _draw_updates(layout, self)
        _draw_chrome_toggles(layout, self)
        _draw_scene_defaults(layout, context)


def _draw_branding(layout: UILayout) -> None:
    box = layout.box()
    draw_mark_label(box, PRODUCT_NAME)
    box.label(text=PRODUCT_CREDIT)
    box.label(text=PRODUCT_TAGLINE)


def _draw_links(layout: UILayout) -> None:
    row = layout.row(align=True)
    row.operator("wm.url_open", text="Docs", icon="HELP").url = DOCS_URL
    row.operator("wm.url_open", text="Releases", icon="URL").url = RELEASES_URL


def _draw_updates(layout: UILayout, prefs: AddonPreferences) -> None:
    box = layout.box()
    box.label(text="Updates", icon="FILE_REFRESH")
    box.label(text=f"Installed: BEHOLD {version_string(VERSION)}")
    box.prop(prefs, "check_for_updates")
    available = available_from_cache(
        getattr(prefs, "update_latest_tag", "") or "",
        installed=installed_version(),
        html_url=getattr(prefs, "update_latest_url", "") or "",
        zip_url=getattr(prefs, "update_latest_zip_url", "") or "",
    )
    error = getattr(prefs, "update_last_error", "") or ""
    copy = prefs_status_copy(
        checking=bool(getattr(prefs, "update_checking", False)),
        installing=bool(getattr(prefs, "update_installing", False)),
        last_iso=getattr(prefs, "update_last_check", "") or "",
        error=error,
        error_kind=getattr(prefs, "update_error_kind", "") or "",
        available=available,
        installed=installed_version(),
    )
    status = box.column(align=True)
    if copy.get("alert"):
        status.alert = True
        status.label(text=copy["line"], icon="ERROR")
    else:
        status.label(text=copy["line"])
    if copy["detail"]:
        status.label(text=copy["detail"])
    row = box.row(align=True)
    row.operator("behold.check_updates", icon="FILE_REFRESH")
    if available and available.get("zip_url"):
        row.operator("behold.install_update", text="Install", icon="IMPORT")
    row.operator("behold.open_release", text="Open release", icon="URL")


def _draw_chrome_toggles(layout: UILayout, prefs: AddonPreferences) -> None:
    box = layout.box()
    box.label(text="Chrome", icon="PREFERENCES")
    box.prop(prefs, "show_flow_strip")
    box.prop(prefs, "show_header_shortcuts")
    box.prop(prefs, "enable_utilities")


def _draw_scene_defaults(layout: UILayout, context: Context) -> None:
    settings = getattr(context.scene, "behold", None)
    if settings is None:
        return
    box = layout.box()
    box.label(text="This scene", icon="SCENE_DATA")
    box.prop(settings, "import_auto_studio")
    box.prop(settings, "import_auto_material_assist")
    box.prop(settings, "render_quality", text="Quality")


CLASSES = (BEHOLDAddonPreferences,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
