# SPDX-License-Identifier: GPL-3.0-or-later
"""Shoot quality → render engine plan (no Blender import).

Draft is the EEVEE (Next) quick look. Final / Product / Hero stay Cycles
client stills. Gobos / IES / logo are out of scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Never

QualityId = Literal["DRAFT", "FINAL", "PRODUCT", "HERO"]
EngineKind = Literal["EEVEE", "CYCLES"]

DEFAULT_QUALITY: QualityId = "DRAFT"

ENGINE_CYCLES = "CYCLES"
ENGINE_EEVEE_NEXT = "BLENDER_EEVEE_NEXT"
ENGINE_EEVEE = "BLENDER_EEVEE"

EEVEE_TRY_ORDER = (ENGINE_EEVEE_NEXT, ENGINE_EEVEE)
CYCLES_TRY_ORDER = (ENGINE_CYCLES,)

QUALITY_SAMPLES: dict[QualityId, int] = {
    "DRAFT": 32,
    "FINAL": 256,
    "PRODUCT": 128,
    "HERO": 512,
}

SHOOT_ENGINE_HINT = "Draft = EEVEE · Final = Cycles"

NO_EEVEE = (
    "EEVEE Next is not on this Blender — Draft is using Cycles. "
    "Update Blender, then Still"
)
NO_CYCLES = (
    "Cycles is not on this Blender — Final stills need Cycles. "
    "Enable Cycles, then Still"
)
QUALITY_FAILED = (
    "Could not apply that quality preset — check the render engine, then Apply Quality"
)
UNKNOWN_QUALITY = "Unknown quality — pick Draft or Final"


@dataclass(frozen=True)
class EeveeDefaults:
    """Cheap product look-dev: shadows + reflections, not a cinematic stack."""

    taa_render_samples: int = 32
    use_shadows: bool = True
    shadow_ray_count: int = 2
    shadow_step_count: int = 3
    use_raytracing: bool = True
    use_ssr: bool = True
    use_ssr_refraction: bool = True
    use_gtao: bool = True
    use_soft_shadows: bool = True

    def rna_pairs(self) -> tuple[tuple[str, object], ...]:
        return (
            ("taa_render_samples", self.taa_render_samples),
            ("use_shadows", self.use_shadows),
            ("shadow_ray_count", self.shadow_ray_count),
            ("shadow_step_count", self.shadow_step_count),
            ("use_raytracing", self.use_raytracing),
            ("use_ssr", self.use_ssr),
            ("use_ssr_refraction", self.use_ssr_refraction),
            ("use_gtao", self.use_gtao),
            ("use_soft_shadows", self.use_soft_shadows),
        )


@dataclass(frozen=True)
class QualityPlan:
    quality: QualityId
    engine_kind: EngineKind
    engine: str
    engine_label: str
    samples: int
    use_denoising: bool
    eevee_defaults: EeveeDefaults | None
    fallback: bool
    engines_to_try: tuple[str, ...]


def quality_enum_items() -> tuple[tuple[str, str, str], ...]:
    return (
        ("DRAFT", "Draft", "EEVEE Next look-dev (fast product preview)"),
        ("FINAL", "Final", "Cycles client still (256 samples)"),
        ("PRODUCT", "Product", "Cycles client-ready stills (128 samples)"),
        ("HERO", "Hero", "Cycles chrome / glass hero shots (512 samples)"),
    )


def is_quality(value: str) -> bool:
    return value in QUALITY_SAMPLES


def normalize_quality(
    value: str, default: QualityId = DEFAULT_QUALITY
) -> QualityId:
    raw = (value or "").strip().upper()
    if raw == "DRAFT":
        return "DRAFT"
    if raw == "FINAL":
        return "FINAL"
    if raw == "PRODUCT":
        return "PRODUCT"
    if raw == "HERO":
        return "HERO"
    if default == "DRAFT":
        return "DRAFT"
    if default == "FINAL":
        return "FINAL"
    if default == "PRODUCT":
        return "PRODUCT"
    if default == "HERO":
        return "HERO"
    unreachable: Never = default
    raise RuntimeError(f"unhandled quality default: {unreachable}")


def engine_kind_for(quality: QualityId) -> EngineKind:
    if quality == "DRAFT":
        return "EEVEE"
    if quality == "FINAL":
        return "CYCLES"
    if quality == "PRODUCT":
        return "CYCLES"
    if quality == "HERO":
        return "CYCLES"
    unreachable: Never = quality
    raise RuntimeError(f"unhandled quality: {unreachable}")


def samples_for(quality: QualityId) -> int:
    return QUALITY_SAMPLES[quality]


def quality_label(quality: QualityId) -> str:
    if quality == "DRAFT":
        return "Draft"
    if quality == "FINAL":
        return "Final"
    if quality == "PRODUCT":
        return "Product"
    if quality == "HERO":
        return "Hero"
    unreachable: Never = quality
    raise RuntimeError(f"unhandled quality: {unreachable}")


def engine_label_for(engine_id: str, *, kind: EngineKind) -> str:
    if kind == "EEVEE":
        if engine_id == ENGINE_EEVEE_NEXT:
            return "EEVEE Next"
        return "EEVEE Next"
    if kind == "CYCLES":
        return "Cycles"
    unreachable: Never = kind
    raise RuntimeError(f"unhandled engine kind: {unreachable}")


def engines_to_try(kind: EngineKind, available: Iterable[str]) -> tuple[str, ...]:
    if kind == "EEVEE":
        order = EEVEE_TRY_ORDER
    elif kind == "CYCLES":
        order = CYCLES_TRY_ORDER
    else:
        unreachable: Never = kind
        raise RuntimeError(f"unhandled engine kind: {unreachable}")
    known = {item for item in available}
    if not known:
        return order
    return tuple(engine for engine in order if engine in known)


def pick_engine(kind: EngineKind, available: Iterable[str]) -> str | None:
    tried = engines_to_try(kind, available)
    return tried[0] if tried else None


def product_eevee_defaults(*, samples: int) -> EeveeDefaults:
    return EeveeDefaults(taa_render_samples=int(samples))


def cycles_fallback_plan(quality: QualityId) -> QualityPlan:
    samples = samples_for(quality)
    return QualityPlan(
        quality=quality,
        engine_kind="CYCLES",
        engine=ENGINE_CYCLES,
        engine_label="Cycles",
        samples=samples,
        use_denoising=True,
        eevee_defaults=None,
        fallback=True,
        engines_to_try=CYCLES_TRY_ORDER,
    )


def _cycles_plan(quality: QualityId, engines: tuple[str, ...]) -> QualityPlan:
    samples = samples_for(quality)
    engine = engines[0]
    return QualityPlan(
        quality=quality,
        engine_kind="CYCLES",
        engine=engine,
        engine_label=engine_label_for(engine, kind="CYCLES"),
        samples=samples,
        use_denoising=True,
        eevee_defaults=None,
        fallback=False,
        engines_to_try=engines,
    )


def _eevee_plan(quality: QualityId, engines: tuple[str, ...]) -> QualityPlan:
    samples = samples_for(quality)
    engine = engines[0]
    return QualityPlan(
        quality=quality,
        engine_kind="EEVEE",
        engine=engine,
        engine_label=engine_label_for(engine, kind="EEVEE"),
        samples=samples,
        use_denoising=False,
        eevee_defaults=product_eevee_defaults(samples=samples),
        fallback=False,
        engines_to_try=engines,
    )


def plan_quality(
    quality: str,
    available: Iterable[str] = (),
) -> QualityPlan | str:
    raw = (quality or "").strip().upper()
    if raw and not is_quality(raw):
        return UNKNOWN_QUALITY
    qid = normalize_quality(raw or DEFAULT_QUALITY)
    kind = engine_kind_for(qid)
    tried = engines_to_try(kind, available)
    if kind == "EEVEE":
        if tried:
            return _eevee_plan(qid, tried)
        cycles_try = engines_to_try("CYCLES", available)
        if not cycles_try:
            return NO_CYCLES
        plan = cycles_fallback_plan(qid)
        return QualityPlan(
            quality=plan.quality,
            engine_kind=plan.engine_kind,
            engine=cycles_try[0],
            engine_label=plan.engine_label,
            samples=plan.samples,
            use_denoising=plan.use_denoising,
            eevee_defaults=None,
            fallback=True,
            engines_to_try=cycles_try,
        )
    if kind == "CYCLES":
        if not tried:
            return NO_CYCLES
        return _cycles_plan(qid, tried)
    unreachable: Never = kind
    raise RuntimeError(f"unhandled engine kind: {unreachable}")


def apply_message(plan: QualityPlan) -> str:
    if plan.fallback:
        return NO_EEVEE
    return (
        f"{quality_label(plan.quality)} quality — "
        f"{plan.engine_label}, {plan.samples} samples"
    )


def with_engine(plan: QualityPlan, engine_id: str) -> QualityPlan:
    return QualityPlan(
        quality=plan.quality,
        engine_kind=plan.engine_kind,
        engine=engine_id,
        engine_label=engine_label_for(engine_id, kind=plan.engine_kind),
        samples=plan.samples,
        use_denoising=plan.use_denoising,
        eevee_defaults=plan.eevee_defaults,
        fallback=plan.fallback,
        engines_to_try=plan.engines_to_try,
    )
