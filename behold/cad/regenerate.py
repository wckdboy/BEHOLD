# SPDX-License-Identifier: GPL-3.0-or-later
"""Live tessellation regenerate — quality / deflection without re-picking CAD.

No Blender import. STEPper NEXT quality names match ``import_ui.QUALITY_PRESETS``
(physical meters). OCP uses the same linear / angular pair. Gobos, IES,
logo, defeaturing, and per-body auto-dress stay out of scope.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Never

from .stepper_api import (
    CadBackend,
    STEPPER_QUALITY_IDS,
    STEPPER_QUALITY_PRESETS,
    missing_cad_backend_message,
)

CAD_EXTENSIONS = frozenset({".step", ".stp", ".iges", ".igs", ".brep", ".brp"})

QualityId = Literal["DRAFT", "BALANCED", "FINE", "ULTRA", "CUSTOM"]
SourceKind = Literal["empty", "unsupported", "missing", "ok"]
StrategyId = Literal["ocp_inplace", "stepper_reimport", "none"]

DEFAULT_QUALITY: QualityId = "BALANCED"
DEFAULT_DEFLECTION = STEPPER_QUALITY_PRESETS["BALANCED"][0]
DEFAULT_ANGULAR = STEPPER_QUALITY_PRESETS["BALANCED"][1]
CUSTOM_ANGULAR = 0.5
MIN_DEFLECTION = 0.00001
MAX_DEFLECTION = 0.05

CAD_SOURCE_KEY = "BEHOLD_cad_source"
CAD_BACKEND_KEY = "BEHOLD_cad_backend"
CAD_QUALITY_KEY = "BEHOLD_cad_quality"
CAD_DEFLECTION_KEY = "BEHOLD_cad_deflection"

NO_CAD_SOURCE = (
    "No CAD source cached — Import Product with a STEP, IGES, or BREP file, "
    "then Regenerate"
)
UNKNOWN_CAD_QUALITY = (
    "Unknown tessellation quality — pick Draft, Balanced, Fine, Ultra, or Custom"
)
REGENERATE_EMPTY = (
    "Tessellation produced no triangles — try a finer quality, then Regenerate"
)
REGENERATE_FAILED = (
    "Could not retessellate that CAD — check the file, then Regenerate"
)
NO_CAD_BACKEND = missing_cad_backend_message()


@dataclass(frozen=True)
class CadCache:
    filepath: str
    backend: str
    quality: str
    deflection: float


@dataclass(frozen=True)
class SourceProblem:
    kind: SourceKind
    detail: str = ""


@dataclass(frozen=True)
class TessellationPlan:
    quality: QualityId
    deflection: float
    angular: float
    stepper_quality: str | None
    stepper_lin_deflection_len: float | None


@dataclass(frozen=True)
class ObjectSnapshot:
    name: str
    matrix: tuple[float, ...]
    material_names: tuple[str, ...]


def quality_enum_items() -> tuple[tuple[str, str, str], ...]:
    return (
        ("DRAFT", "Draft", "Fast preview (2 mm linear deflection)"),
        ("BALANCED", "Balanced", "Default product mesh (0.8 mm)"),
        ("FINE", "Fine", "High quality (0.2 mm)"),
        ("ULTRA", "Ultra", "Maximum quality (0.05 mm)"),
        ("CUSTOM", "Custom", "Set linear deflection on the slider"),
    )


def is_quality(value: str) -> bool:
    return value in STEPPER_QUALITY_IDS


def quality_label(quality: QualityId) -> str:
    if quality == "DRAFT":
        return "Draft"
    if quality == "BALANCED":
        return "Balanced"
    if quality == "FINE":
        return "Fine"
    if quality == "ULTRA":
        return "Ultra"
    if quality == "CUSTOM":
        return "Custom"
    unreachable: Never = quality
    raise RuntimeError(f"unhandled tessellation quality: {unreachable}")


def unknown_quality_message(quality_id: str) -> str:
    shown = (quality_id or "").strip()
    if not shown:
        return UNKNOWN_CAD_QUALITY
    return (
        f"Unknown tessellation quality “{shown}” — "
        "pick Draft, Balanced, Fine, Ultra, or Custom"
    )


def clamp_deflection(value: float) -> float:
    return min(MAX_DEFLECTION, max(MIN_DEFLECTION, float(value)))


def preset_pair(quality: QualityId) -> tuple[float, float]:
    if quality == "CUSTOM":
        return DEFAULT_DEFLECTION, CUSTOM_ANGULAR
    if quality == "DRAFT":
        return STEPPER_QUALITY_PRESETS["DRAFT"]
    if quality == "BALANCED":
        return STEPPER_QUALITY_PRESETS["BALANCED"]
    if quality == "FINE":
        return STEPPER_QUALITY_PRESETS["FINE"]
    if quality == "ULTRA":
        return STEPPER_QUALITY_PRESETS["ULTRA"]
    unreachable: Never = quality
    raise RuntimeError(f"unhandled tessellation quality: {unreachable}")


def plan_tessellation(quality: str, deflection: float) -> TessellationPlan | str:
    raw = (quality or "").strip().upper()
    if raw and not is_quality(raw):
        return unknown_quality_message(quality)
    if not raw:
        raw = DEFAULT_QUALITY
    qid: QualityId
    if raw == "DRAFT":
        qid = "DRAFT"
    elif raw == "BALANCED":
        qid = "BALANCED"
    elif raw == "FINE":
        qid = "FINE"
    elif raw == "ULTRA":
        qid = "ULTRA"
    elif raw == "CUSTOM":
        qid = "CUSTOM"
    else:
        return unknown_quality_message(quality)

    if qid == "CUSTOM":
        lin = clamp_deflection(deflection)
        return TessellationPlan(
            quality=qid,
            deflection=lin,
            angular=CUSTOM_ANGULAR,
            stepper_quality="CUSTOM",
            stepper_lin_deflection_len=lin,
        )
    lin, ang = preset_pair(qid)
    return TessellationPlan(
        quality=qid,
        deflection=lin,
        angular=ang,
        stepper_quality=qid,
        stepper_lin_deflection_len=None,
    )


def pick_regenerate_backend(
    cached_backend: str,
    current_backend: CadBackend,
) -> CadBackend:
    """Prefer STEPper NEXT when installed; OCP if that is the live fallback.

    Cached backend is the last import path (STEPPER vs OCP). STEPper wins
    whenever it is available, including products that first came in via OCP.
    OCP is used when STEPper is missing — including when that is what imported.
    """
    del cached_backend
    if current_backend == "STEPPER":
        return "STEPPER"
    if current_backend == "OCP":
        return "OCP"
    if current_backend == "NONE":
        return "NONE"
    unreachable: Never = current_backend
    raise RuntimeError(f"unhandled CAD backend: {unreachable}")


def regenerate_strategy(backend: CadBackend) -> StrategyId:
    if backend == "STEPPER":
        return "stepper_reimport"
    if backend == "OCP":
        return "ocp_inplace"
    if backend == "NONE":
        return "none"
    unreachable: Never = backend
    raise RuntimeError(f"unhandled CAD backend: {unreachable}")


def classify_cad_source(filepath: str) -> SourceProblem | None:
    path = (filepath or "").strip()
    if not path:
        return SourceProblem("empty")
    ext = os.path.splitext(path)[1].lower()
    if ext not in CAD_EXTENSIONS:
        shown = ext or "this file"
        return SourceProblem("unsupported", shown)
    abs_path = os.path.abspath(path)
    if not os.path.isfile(abs_path):
        return SourceProblem("missing", os.path.basename(path) or path)
    return None


def cad_source_problem_message(problem: SourceProblem) -> str:
    if problem.kind == "empty":
        return NO_CAD_SOURCE
    if problem.kind == "unsupported":
        shown = problem.detail or "this file"
        return (
            f"Cached source is not CAD ({shown}) — "
            "Import Product with STEP, IGES, or BREP, then Regenerate"
        )
    if problem.kind == "missing":
        name = problem.detail or "that file"
        return (
            f"CAD file not found: {name} — "
            "restore the file or Import Product again, then Regenerate"
        )
    if problem.kind == "ok":
        return ""
    unreachable: Never = problem.kind
    raise RuntimeError(f"unhandled CAD source kind: {unreachable}")


def resolve_cad_cache(
    *,
    scene_filepath: str,
    scene_backend: str,
    scene_quality: str,
    scene_deflection: float,
    object_sources: tuple[tuple[str, str], ...] = (),
) -> CadCache | None:
    """Scene cache first, then the first tagged product CAD path."""
    path = (scene_filepath or "").strip()
    backend = (scene_backend or "").strip()
    if not path:
        for obj_path, obj_backend in object_sources:
            candidate = (obj_path or "").strip()
            if candidate:
                path = candidate
                backend = (obj_backend or backend).strip()
                break
    if not path:
        return None
    quality = (scene_quality or "").strip().upper() or DEFAULT_QUALITY
    return CadCache(
        filepath=path,
        backend=backend,
        quality=quality,
        deflection=float(scene_deflection or DEFAULT_DEFLECTION),
    )


def cache_record(
    filepath: str,
    backend: str,
    *,
    quality: str = "CUSTOM",
    deflection: float = DEFAULT_DEFLECTION,
) -> CadCache:
    return CadCache(
        filepath=filepath,
        backend=backend,
        quality=quality,
        deflection=clamp_deflection(deflection),
    )


def blender_stem(name: str) -> str:
    if len(name) > 4 and name[-4] == "." and name[-3:].isdigit():
        return name[:-4]
    return name


def match_snapshots(
    old_names: tuple[str, ...],
    new_names: tuple[str, ...],
) -> dict[str, str]:
    """Map new object name → previous name (materials / transforms)."""
    mapping: dict[str, str] = {}
    remaining_old = list(old_names)
    remaining_new = list(new_names)

    for new in list(remaining_new):
        if new in remaining_old:
            mapping[new] = new
            remaining_old.remove(new)
            remaining_new.remove(new)

    old_by_stem: dict[str, list[str]] = {}
    for old in remaining_old:
        old_by_stem.setdefault(blender_stem(old), []).append(old)

    for new in list(remaining_new):
        stem = blender_stem(new)
        candidates = old_by_stem.get(stem, [])
        if len(candidates) != 1:
            continue
        old = candidates[0]
        mapping[new] = old
        remaining_old.remove(old)
        remaining_new.remove(new)
        old_by_stem[stem].remove(old)

    if len(remaining_old) == 1 and len(remaining_new) == 1:
        mapping[remaining_new[0]] = remaining_old[0]

    return mapping


def stepper_kwargs_plan(
    plan: TessellationPlan,
    known_props: frozenset[str] | None,
) -> tuple[str | None, float | None]:
    """quality_preset + optional lin_deflection_len, never invented RNA."""
    quality = plan.stepper_quality
    lin = plan.stepper_lin_deflection_len
    if known_props is None:
        return quality, lin
    if "quality_preset" not in known_props:
        quality = None
        lin = plan.deflection
        if "lin_deflection_len" not in known_props:
            lin = None
        return quality, lin
    if quality == "CUSTOM":
        if "lin_deflection_len" not in known_props:
            lin = None
        return quality, lin
    return quality, None


def regenerated_message(
    filepath: str,
    *,
    backend: str,
    quality: QualityId,
    object_count: int,
) -> str:
    name = os.path.basename(filepath) or filepath or "CAD"
    via = "STEPper NEXT" if backend == "STEPPER" else "OCP"
    count = f"{object_count} mesh" if object_count == 1 else f"{object_count} meshes"
    return (
        f"Retessellated {name} via {via} ({quality_label(quality)}, {count})"
    )


def cached_label(filepath: str) -> str:
    name = os.path.basename((filepath or "").strip())
    if not name:
        return "No CAD cached — Import Product first"
    return f"Last CAD: {name}"
