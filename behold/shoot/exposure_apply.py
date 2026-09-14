# SPDX-License-Identifier: GPL-3.0-or-later
"""Push Shoot Look props onto scene Color Management (viewport + render)."""

from __future__ import annotations

from typing import Any

from bpy.types import Context

from . import exposure as exposure_lib


def list_view_transforms(view) -> tuple[str, ...]:
    prop = getattr(getattr(view, "bl_rna", None), "properties", None)
    if prop is None:
        return ()
    item = prop.get("view_transform")
    if item is None:
        return ()
    enum_items = getattr(item, "enum_items", None)
    if enum_items is None:
        return ()
    return tuple(entry.identifier for entry in enum_items)


def write_white_balance(view, plan: exposure_lib.ExposurePlan) -> str:
    api = exposure_lib.prefer_white_balance_api(dir(view))
    kelvin = exposure_lib.clamp_blender_kelvin(plan.kelvin)
    if api == exposure_lib.WB_API_WHITE_BALANCE:
        if hasattr(view, "use_white_balance"):
            view.use_white_balance = True
        view.white_balance_temperature = kelvin
        return api
    if api == exposure_lib.WB_API_TEMPERATURE:
        view.temperature = plan.temperature_offset
        return api
    return exposure_lib.WB_API_NONE


def write_view_transform(view, name: str) -> bool:
    current = getattr(view, "view_transform", "") or ""
    if current == name:
        return True
    try:
        view.view_transform = name
    except (TypeError, ValueError):
        return False
    return (getattr(view, "view_transform", "") or "") == name


def apply_exposure(context: Context) -> dict[str, Any]:
    """Write EV / WB / false color to ``scene.view_settings`` (view and render)."""
    scene = getattr(context, "scene", None)
    if scene is None:
        plan = exposure_lib.plan_exposure(
            exposure_ev=0.0,
            white_balance_kelvin=exposure_lib.D65_KELVIN,
            false_color=False,
        )
        return {
            "ok": False,
            "message": exposure_lib.NO_VIEW_SETTINGS,
            "plan": plan,
        }
    settings = scene.behold
    view = getattr(scene, "view_settings", None)
    if view is None:
        plan = exposure_lib.plan_exposure(
            exposure_ev=getattr(settings, "exposure_ev", 0.0),
            white_balance_kelvin=getattr(
                settings, "white_balance_kelvin", exposure_lib.D65_KELVIN
            ),
            false_color=bool(getattr(settings, "false_color", False)),
        )
        return {
            "ok": False,
            "message": exposure_lib.NO_VIEW_SETTINGS,
            "plan": plan,
        }

    current = getattr(view, "view_transform", "") or ""
    saved = getattr(settings, "view_transform_restore", "") or (
        exposure_lib.DEFAULT_VIEW_TRANSFORM
    )
    plan = exposure_lib.plan_exposure(
        exposure_ev=settings.exposure_ev,
        white_balance_kelvin=settings.white_balance_kelvin,
        false_color=bool(settings.false_color),
        current_view_transform=current,
        saved_view_transform=saved,
        available_transforms=list_view_transforms(view),
    )
    settings.view_transform_restore = plan.restore_transform
    view.exposure = plan.exposure
    write_white_balance(view, plan)
    transform_ok = write_view_transform(view, plan.view_transform)
    ok = transform_ok or not plan.false_color
    message = exposure_lib.apply_message(
        plan,
        view_transform_ok=transform_ok,
        has_view=True,
    )
    return {
        "ok": ok,
        "message": message,
        "plan": plan,
        "view_transform_ok": transform_ok,
    }


def on_exposure_update(settings, context: Context) -> None:
    """RNA update: dragging EV / WB / False Color pushes Color Management live."""
    del settings
    if context is None or getattr(context, "scene", None) is None:
        return
    apply_exposure(context)
