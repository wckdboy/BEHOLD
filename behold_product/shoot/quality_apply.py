# SPDX-License-Identifier: GPL-3.0-or-later
"""Push Shoot quality onto the scene render engine (EEVEE Draft / Cycles Final)."""

from __future__ import annotations

from typing import Any, Iterable

import bpy
from bpy.types import Context, Scene

from . import quality as spec


def _result(ok: bool, message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "message": message}
    payload.update(extra)
    return payload


def available_engine_ids() -> frozenset[str]:
    rna = getattr(getattr(bpy.types, "RenderSettings", None), "bl_rna", None)
    if rna is None:
        return frozenset()
    properties = getattr(rna, "properties", None)
    if properties is None:
        return frozenset()
    item = properties.get("engine")
    if item is None:
        return frozenset()
    enum_items = getattr(item, "enum_items", None)
    if enum_items is None:
        return frozenset()
    return frozenset(entry.identifier for entry in enum_items)


def _set_attr(owner: object, name: str, value: object) -> bool:
    if owner is None or not hasattr(owner, name):
        return False
    try:
        setattr(owner, name, value)
    except (AttributeError, TypeError, ValueError):
        return False
    return True


def _set_engine(scene: Scene, engine_id: str) -> bool:
    render = getattr(scene, "render", None)
    if render is None:
        return False
    try:
        render.engine = engine_id
    except (AttributeError, TypeError, ValueError):
        return False
    return getattr(render, "engine", "") == engine_id


def _apply_cycles(scene: Scene, plan: spec.QualityPlan) -> bool:
    cycles = getattr(scene, "cycles", None)
    if cycles is None:
        return False
    if not _set_attr(cycles, "samples", plan.samples):
        return False
    _set_attr(cycles, "use_denoising", True)
    if hasattr(cycles, "denoiser"):
        try:
            cycles.denoiser = "OPENIMAGEDENOISE"
        except (AttributeError, TypeError, ValueError):
            pass
    return True


def _apply_eevee(scene: Scene, plan: spec.QualityPlan) -> bool:
    eevee = getattr(scene, "eevee", None)
    defaults = plan.eevee_defaults
    if eevee is None or defaults is None:
        return False
    wrote = False
    for name, value in defaults.rna_pairs():
        if _set_attr(eevee, name, value):
            wrote = True
    return wrote


def _try_engines(scene: Scene, engines: Iterable[str]) -> str | None:
    for engine_id in engines:
        if _set_engine(scene, engine_id):
            return engine_id
    return None


def apply_render_quality(context: Context) -> dict[str, Any]:
    """Switch Draft to EEVEE Next (or EEVEE) and Final/Product/Hero to Cycles."""
    scene = getattr(context, "scene", None)
    if scene is None or getattr(scene, "render", None) is None:
        return _result(False, spec.QUALITY_FAILED)
    settings = getattr(scene, "behold", None)
    quality = getattr(settings, "render_quality", spec.DEFAULT_QUALITY)
    plan = spec.plan_quality(
        str(quality or spec.DEFAULT_QUALITY),
        available_engine_ids(),
    )
    if isinstance(plan, str):
        return _result(False, plan)

    chosen = _try_engines(scene, plan.engines_to_try)
    applied = plan
    if chosen is None and plan.engine_kind == "EEVEE":
        applied = spec.cycles_fallback_plan(plan.quality)
        chosen = _try_engines(scene, applied.engines_to_try)
        if chosen is None:
            return _result(False, spec.NO_EEVEE, plan=applied)
    elif chosen is None:
        return _result(False, spec.NO_CYCLES, plan=plan)

    applied = spec.with_engine(applied, chosen)
    if applied.engine_kind == "EEVEE":
        _apply_eevee(scene, applied)
    elif applied.engine_kind == "CYCLES":
        if not _apply_cycles(scene, applied):
            return _result(False, spec.QUALITY_FAILED, plan=applied, engine=chosen)
    else:
        unreachable_kind = applied.engine_kind
        raise RuntimeError(f"unhandled engine kind: {unreachable_kind}")

    return _result(
        True,
        spec.apply_message(applied),
        plan=applied,
        samples=applied.samples,
        engine=chosen,
        engine_label=applied.engine_label,
        fallback=applied.fallback,
        quality=applied.quality,
    )


def on_quality_update(settings, context: Context) -> None:
    """RNA update: Draft / Final switches EEVEE vs Cycles live."""
    del settings
    if context is None or getattr(context, "scene", None) is None:
        return
    apply_render_quality(context)
