# SPDX-License-Identifier: GPL-3.0-or-later
"""Defeaturing lite — fillet / chamfer / hole suppress before tessellate.

No Blender. STEPper NEXT has no fillet / chamfer / hole RNA (verified against
Peak-Design/STEPper_NEXT ``import_ui.py`` 2.4+: quality, UV, materials,
hierarchy only). Cleanup therefore runs on the BEHOLD OCP path with
``BRepAlgoAPI_Defeaturing`` and/or ``ShapeUpgrade_RemoveInternalWires``.
Artist sizes are millimetres. File units come from the STEP length unit
(default millimetres). Not a CAD editor.
"""

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass
from typing import Literal, Never

FaceKind = Literal["plane", "cylinder", "torus", "sphere", "cone", "other"]
FeatureRole = Literal["fillet", "chamfer", "hole", "keep"]

DEFAULT_BLEND_MM = 2.0
DEFAULT_HOLE_MM = 3.0
MIN_SIZE_MM = 0.05
MAX_SIZE_MM = 50.0
DEFAULT_METERS_PER_FILE_UNIT = 0.001
FULL_REVOLUTION = 1.5 * math.pi
STRIP_ASPECT = 1.5
MAX_FACE_FRACTION_OF_DIAG = 0.2

DEFEATURE_NEEDS_OCP = (
    "Cleanup needs OCP (cadquery-ocp). STEPper NEXT tessellates only — "
    "install OCP or turn off Fillets / Chamfers / Holes, then Regenerate"
)
DEFEATURE_NO_FILLET_API = (
    "This OCP build cannot remove fillets or chamfers — "
    "turn off Fillets / Chamfers or update cadquery-ocp, then Regenerate"
)
DEFEATURE_NO_HOLE_API = (
    "This OCP build cannot suppress holes — "
    "turn off Holes or update cadquery-ocp, then Regenerate"
)
DEFEATURE_NO_SOLID = (
    "Cleanup needs a solid body — this file is a surface or shell, "
    "turn off Fillets / Chamfers / Holes, then Regenerate"
)
DEFEATURE_FAILED = (
    "Could not suppress those fillets / holes — try a smaller size, then Regenerate"
)
STEPPER_NO_DEFEATURE = DEFEATURE_NEEDS_OCP

_SI_LENGTH_RE = re.compile(
    r"SI_UNIT\(\s*(\.[A-Z]+\.|\$)\s*,\s*\.METRE\.\s*\)",
    re.IGNORECASE,
)
_PREFIX_METERS = {
    ".MILLI.": 0.001,
    ".CENTI.": 0.01,
    ".DECI.": 0.1,
    ".KILO.": 1000.0,
    "$": 1.0,
    ".NONE.": 1.0,
}


@dataclass(frozen=True)
class DefeaturingPlan:
    fillets: bool
    chamfers: bool
    holes: bool
    blend_mm: float
    hole_mm: float

    @property
    def active(self) -> bool:
        return self.fillets or self.chamfers or self.holes


@dataclass(frozen=True)
class FaceHint:
    kind: FaceKind
    radius: float = 0.0
    u_span: float = 0.0
    v_span: float = 0.0
    width: float = 0.0
    area: float = 0.0
    closed_u: bool = False


@dataclass(frozen=True)
class FeaturePick:
    index: int
    role: FeatureRole


@dataclass(frozen=True)
class CleanupStats:
    fillets: int = 0
    chamfers: int = 0
    holes: int = 0
    wires: int = 0

    @property
    def face_count(self) -> int:
        return self.fillets + self.chamfers + self.holes


def clamp_size_mm(value: float) -> float:
    return min(MAX_SIZE_MM, max(MIN_SIZE_MM, float(value)))


def plan_defeaturing(
    *,
    fillets: bool,
    chamfers: bool,
    holes: bool,
    blend_mm: float,
    hole_mm: float,
) -> DefeaturingPlan:
    return DefeaturingPlan(
        fillets=bool(fillets),
        chamfers=bool(chamfers),
        holes=bool(holes),
        blend_mm=clamp_size_mm(blend_mm),
        hole_mm=clamp_size_mm(hole_mm),
    )


def meters_per_file_unit_from_text(text: str) -> float | None:
    """STEP length unit in metres per file unit. None if the header is silent."""
    blob = text or ""
    if not blob:
        return None
    upper = blob.upper()
    if "LENGTH_UNIT" not in upper and "SI_UNIT" not in upper:
        return None
    matches = _SI_LENGTH_RE.findall(blob)
    if not matches:
        return None
    for raw in matches:
        key = raw.upper() if raw.startswith(".") else raw
        if key in _PREFIX_METERS:
            return _PREFIX_METERS[key]
        lowered = raw.upper()
        if lowered in _PREFIX_METERS:
            return _PREFIX_METERS[lowered]
    return None


def meters_per_file_unit(filepath: str) -> float:
    path = (filepath or "").strip()
    ext = os.path.splitext(path)[1].lower()
    if ext in {".step", ".stp"} and path and os.path.isfile(path):
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                snippet = handle.read(65536)
        except OSError:
            snippet = ""
        parsed = meters_per_file_unit_from_text(snippet)
        if parsed is not None:
            return parsed
    return DEFAULT_METERS_PER_FILE_UNIT


def mm_to_file_units(mm: float, meters_per_unit: float) -> float:
    scale = meters_per_unit if meters_per_unit > 0 else DEFAULT_METERS_PER_FILE_UNIT
    return (float(mm) / 1000.0) / scale


def hole_radius_file_units(plan: DefeaturingPlan, meters_per_unit: float) -> float:
    return mm_to_file_units(plan.hole_mm / 2.0, meters_per_unit)


def blend_file_units(plan: DefeaturingPlan, meters_per_unit: float) -> float:
    return mm_to_file_units(plan.blend_mm, meters_per_unit)


def hole_area_file_units(plan: DefeaturingPlan, meters_per_unit: float) -> float:
    radius = hole_radius_file_units(plan, meters_per_unit)
    return math.pi * radius * radius


def is_full_revolution(hint: FaceHint) -> bool:
    return hint.closed_u or hint.u_span >= FULL_REVOLUTION


def is_hole_cylinder(hint: FaceHint, hole_radius: float) -> bool:
    if hint.kind != "cylinder":
        return False
    if hint.radius <= 0 or hint.radius > hole_radius + 1e-9:
        return False
    return is_full_revolution(hint)


def is_fillet_face(hint: FaceHint, blend: float) -> bool:
    if blend <= 0:
        return False
    if hint.kind == "cylinder":
        if is_full_revolution(hint):
            return False
        return 0 < hint.radius <= blend + 1e-9
    if hint.kind == "torus":
        return 0 < hint.radius <= blend + 1e-9
    if hint.kind == "sphere":
        return 0 < hint.radius <= blend + 1e-9
    if hint.kind == "plane":
        return False
    if hint.kind == "cone":
        return False
    if hint.kind == "other":
        return False
    unreachable: Never = hint.kind
    raise RuntimeError(f"unhandled face kind: {unreachable}")


def is_chamfer_face(hint: FaceHint, blend: float, bbox_diag: float) -> bool:
    if hint.kind != "plane" or blend <= 0:
        return False
    width = hint.width if hint.width > 0 else min(hint.u_span, hint.v_span)
    if width <= 0 or width > blend + 1e-9:
        return False
    if bbox_diag > 0 and width > MAX_FACE_FRACTION_OF_DIAG * bbox_diag:
        return False
    long_span = max(hint.u_span, hint.v_span, width)
    if long_span < STRIP_ASPECT * width:
        return False
    return True


def feature_role(
    hint: FaceHint,
    plan: DefeaturingPlan,
    *,
    blend: float,
    hole_radius: float,
    bbox_diag: float,
) -> FeatureRole:
    if plan.holes and is_hole_cylinder(hint, hole_radius):
        return "hole"
    if plan.fillets and is_fillet_face(hint, blend):
        return "fillet"
    if plan.chamfers and is_chamfer_face(hint, blend, bbox_diag):
        return "chamfer"
    return "keep"


def select_feature_faces(
    hints: tuple[FaceHint, ...],
    plan: DefeaturingPlan,
    *,
    meters_per_unit: float,
    bbox_diag: float,
) -> tuple[FeaturePick, ...]:
    if not plan.active:
        return ()
    blend = blend_file_units(plan, meters_per_unit)
    hole_radius = hole_radius_file_units(plan, meters_per_unit)
    picks: list[FeaturePick] = []
    for index, hint in enumerate(hints):
        role = feature_role(
            hint,
            plan,
            blend=blend,
            hole_radius=hole_radius,
            bbox_diag=bbox_diag,
        )
        if role == "keep":
            continue
        picks.append(FeaturePick(index=index, role=role))
    return tuple(picks)


def count_roles(picks: tuple[FeaturePick, ...]) -> CleanupStats:
    fillets = sum(1 for pick in picks if pick.role == "fillet")
    chamfers = sum(1 for pick in picks if pick.role == "chamfer")
    holes = sum(1 for pick in picks if pick.role == "hole")
    return CleanupStats(fillets=fillets, chamfers=chamfers, holes=holes)


def cleanup_blockers(
    plan: DefeaturingPlan,
    *,
    ocp_available: bool,
    has_defeaturing: bool,
    has_remove_wires: bool,
) -> str | None:
    if not plan.active:
        return None
    if not ocp_available:
        return DEFEATURE_NEEDS_OCP
    if (plan.fillets or plan.chamfers) and not has_defeaturing:
        return DEFEATURE_NO_FILLET_API
    if plan.holes and not has_defeaturing and not has_remove_wires:
        return DEFEATURE_NO_HOLE_API
    return None


def cleanup_caption(plan: DefeaturingPlan) -> str:
    if not plan.active:
        return ""
    parts: list[str] = []
    if plan.fillets:
        parts.append(f"fillets ≤ {plan.blend_mm:g} mm")
    if plan.chamfers:
        parts.append(f"chamfers ≤ {plan.blend_mm:g} mm")
    if plan.holes:
        parts.append(f"holes Ø ≤ {plan.hole_mm:g} mm")
    return ", ".join(parts)


def cleanup_applied_caption(plan: DefeaturingPlan, stats: CleanupStats) -> str:
    if not plan.active:
        return ""
    sizes = cleanup_caption(plan)
    if stats.face_count == 0 and stats.wires == 0:
        return f"{sizes}; none matched"
    bits: list[str] = []
    if plan.fillets:
        bits.append(f"{stats.fillets} fillet" if stats.fillets == 1 else f"{stats.fillets} fillets")
    if plan.chamfers:
        bits.append(
            f"{stats.chamfers} chamfer" if stats.chamfers == 1 else f"{stats.chamfers} chamfers"
        )
    if plan.holes:
        hole_n = stats.holes + stats.wires
        bits.append(f"{hole_n} hole" if hole_n == 1 else f"{hole_n} holes")
    detail = ", ".join(bits)
    if detail:
        return f"{sizes}; removed {detail}"
    return f"{sizes}; none matched"


def stepper_supports_defeaturing() -> bool:
    """STEPper NEXT has no fillet / chamfer / hole import RNA."""
    return False
