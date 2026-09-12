# SPDX-License-Identifier: GPL-3.0-or-later
"""Soft-dependency bridge to BlenderKit / Blendkit (login-ready from day one)."""

from __future__ import annotations

import bpy
from bpy.types import Context, Operator


BLENDERKIT_MODULE_CANDIDATES = (
    "blenderkit",
    "bl_ext.blender_org.blenderkit",
    "bl_ext.user_default.blenderkit",
)


def find_blenderkit_module() -> str | None:
    for name in BLENDERKIT_MODULE_CANDIDATES:
        if name in bpy.context.preferences.addons.keys():
            return name
    # Also accept partially matching enabled add-on module names.
    for name in bpy.context.preferences.addons.keys():
        if "blenderkit" in name.lower() or "blendkit" in name.lower():
            return name
    return None


def blenderkit_status() -> dict:
    module = find_blenderkit_module()
    if module is None:
        return {
            "installed": False,
            "logged_in": False,
            "label": "BlenderKit not enabled",
            "detail": "Install/enable BlenderKit (Blendkit) to search and apply materials.",
            "module": None,
        }

    logged_in = False
    detail = "Enabled — sign in to download Full-plan materials and keep bookmarks."
    try:
        addon = bpy.context.preferences.addons.get(module)
        prefs = getattr(addon, "preferences", None) if addon else None
        # BlenderKit has used api_key / login state on preferences across versions.
        api_key = ""
        if prefs is not None:
            api_key = getattr(prefs, "api_key", "") or getattr(prefs, "api_key_upload", "")
            logged_in = bool(api_key) or bool(getattr(prefs, "login_attempt", False) is False and getattr(prefs, "api_key", ""))
            # Prefer explicit login flags when present.
            for flag in ("is_logged_in", "logged_in", "user_logged"):
                if hasattr(prefs, flag):
                    logged_in = bool(getattr(prefs, flag))
                    break
            if api_key:
                logged_in = True
        if logged_in:
            detail = "Signed in — search and apply materials to the selection."
        else:
            detail = "Enabled but not signed in — log in for full library access."
    except Exception:  # noqa: BLE001 - bridge must never crash the host UI
        detail = "Enabled — open BlenderKit to manage login."

    return {
        "installed": True,
        "logged_in": logged_in,
        "label": "Signed in" if logged_in else "Login required",
        "detail": detail,
        "module": module,
    }


def _invoke_optional(op_id: str) -> bool:
    """Call a BlenderKit operator if it exists. Returns True if invoked."""
    try:
        path, name = op_id.split(".", 1)
        category = getattr(bpy.ops, path, None)
        if category is None:
            return False
        op = getattr(category, name, None)
        if op is None:
            return False
        result = op()
        return "FINISHED" in result or "RUNNING_MODAL" in result or "CANCELLED" in result
    except Exception:  # noqa: BLE001
        return False


class BEHOLD_OT_blenderkit_login(Operator):
    bl_idname = "behold.blenderkit_login"
    bl_label = "Log In to BlenderKit"
    bl_description = "Open BlenderKit login so BEHOLD can use your account from day one"

    def execute(self, context: Context):
        status = blenderkit_status()
        if not status["installed"]:
            self.report(
                {"ERROR"},
                "Enable BlenderKit first (Preferences → Get Extensions → BlenderKit)",
            )
            return {"CANCELLED"}

        # Try known login operators across BlenderKit versions.
        for op_id in (
            "wm.blenderkit_login",
            "blenderkit.login",
            "view3d.blenderkit_login",
        ):
            if _invoke_optional(op_id):
                self.report({"INFO"}, "Opened BlenderKit login")
                return {"FINISHED"}

        # Fallback: open preferences filtered to the add-on.
        try:
            bpy.ops.preferences.addon_show(module=status["module"])
            self.report({"INFO"}, "Opened BlenderKit preferences — sign in there")
            return {"FINISHED"}
        except Exception:  # noqa: BLE001
            self.report(
                {"WARNING"},
                "Could not open login UI — use the BlenderKit panel (N → BlenderKit)",
            )
            return {"CANCELLED"}


class BEHOLD_OT_blenderkit_search(Operator):
    bl_idname = "behold.blenderkit_search"
    bl_label = "Search BlenderKit Materials"
    bl_description = "Run a BlenderKit material search with the BEHOLD query"

    def execute(self, context: Context):
        status = blenderkit_status()
        if not status["installed"]:
            self.report({"ERROR"}, "BlenderKit is not enabled")
            return {"CANCELLED"}

        query = context.scene.behold.blenderkit_query.strip() or "metal"
        # Prefer setting BlenderKit UI search props when present, then invoke search.
        try:
            ui_props = getattr(context.window_manager, "blenderkitUI", None)
            if ui_props is not None and hasattr(ui_props, "search_keywords"):
                ui_props.asset_type = "MATERIAL"
                ui_props.search_keywords = query
        except Exception:  # noqa: BLE001
            pass

        for op_id in (
            "view3d.blenderkit_search",
            "blenderkit.search",
            "wm.blenderkit_search",
        ):
            if _invoke_optional(op_id):
                self.report({"INFO"}, f"Searching BlenderKit for “{query}”")
                return {"FINISHED"}

        self.report(
            {"WARNING"},
            f"Query set to “{query}” — open the BlenderKit asset bar to browse results",
        )
        return {"FINISHED"}


class BEHOLD_OT_blenderkit_apply(Operator):
    bl_idname = "behold.blenderkit_apply"
    bl_label = "Apply Active BlenderKit Material"
    bl_description = "Apply the active BlenderKit material download to the selection"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: Context):
        status = blenderkit_status()
        if not status["installed"]:
            self.report({"ERROR"}, "BlenderKit is not enabled")
            return {"CANCELLED"}
        if not context.selected_objects:
            self.report({"ERROR"}, "Select at least one object")
            return {"CANCELLED"}

        for op_id in (
            "object.blenderkit_download",
            "view3d.blenderkit_download",
            "blenderkit.import_material",
        ):
            if _invoke_optional(op_id):
                self.report({"INFO"}, "Requested BlenderKit material apply")
                return {"FINISHED"}

        self.report(
            {"WARNING"},
            "Select a material in the BlenderKit bar, then drag it onto the selection",
        )
        return {"CANCELLED"}


CLASSES = (
    BEHOLD_OT_blenderkit_login,
    BEHOLD_OT_blenderkit_search,
    BEHOLD_OT_blenderkit_apply,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
