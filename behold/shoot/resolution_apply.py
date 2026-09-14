# SPDX-License-Identifier: GPL-3.0-or-later
"""Push catalog Size presets onto scene.render (resolution + pixel aspect)."""

from __future__ import annotations

from typing import Any

from bpy.types import Context, Scene

from . import resolution as spec


def _result(ok: bool, message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "message": message}
    payload.update(extra)
    return payload


def _set_attr(owner: object, name: str, value: object) -> bool:
    if owner is None or not hasattr(owner, name):
        return False
    try:
        setattr(owner, name, value)
    except (AttributeError, TypeError, ValueError):
        return False
    return True


def _write_plan(scene: Scene, plan: spec.ResolutionPlan) -> bool:
    render = getattr(scene, "render", None)
    if render is None:
        return False
    wrote = False
    for name, value in plan.rna_pairs():
        if _set_attr(render, name, value):
            wrote = True
    if not wrote:
        return False
    return (
        int(getattr(render, "resolution_x", 0) or 0) == plan.resolution_x
        and int(getattr(render, "resolution_y", 0) or 0) == plan.resolution_y
    )


def apply_resolution(context: Context) -> dict[str, Any]:
    """Write aspect × size onto ``scene.render`` (square pixels, 100%)."""
    scene = getattr(context, "scene", None)
    if scene is None or getattr(scene, "render", None) is None:
        return _result(False, spec.NO_RENDER_SETTINGS)
    settings = getattr(scene, "behold", None)
    aspect = getattr(settings, "resolution_aspect", spec.DEFAULT_ASPECT)
    size = getattr(settings, "resolution_size", spec.DEFAULT_SIZE)
    plan = spec.plan_resolution(
        str(aspect or spec.DEFAULT_ASPECT),
        str(size or spec.DEFAULT_SIZE),
    )
    if isinstance(plan, str):
        return _result(False, plan)
    if not _write_plan(scene, plan):
        return _result(False, spec.RESOLUTION_FAILED, plan=plan)
    return _result(
        True,
        spec.apply_message(plan),
        plan=plan,
        resolution_x=plan.resolution_x,
        resolution_y=plan.resolution_y,
        aspect=plan.aspect,
        size=plan.size,
    )


def on_resolution_update(settings, context: Context) -> None:
    """RNA update: aspect / size writes Output Properties live."""
    del settings
    if context is None or getattr(context, "scene", None) is None:
        return
    apply_resolution(context)
