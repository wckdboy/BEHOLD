# SPDX-License-Identifier: GPL-3.0-or-later
"""Product depth of field / focus pick — camera DoF RNA (no Blender import).

Photographer-class lite on the active BEHOLD camera: enable DoF, a product
f-stop, and focus distance from the product AABB or the selected surface.
Maps to Blender 5.2 ``Camera.dof`` (``use_dof`` / ``aperture_fstop`` /
``focus_distance``). Gobos / IES / logo are out of scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Never

from .camera_ids import bounds_center_size

FocusId = Literal["KEEP", "PRODUCT", "SELECTED"]
TargetId = Literal["NONE", "KEEP", "PRODUCT", "SELECTED"]

DEFAULT_FSTOP = 5.6
BLENDER_DEFAULT_FSTOP = 2.8
BLENDER_DEFAULT_FOCUS = 10.0
FSTOP_MIN = 1.0
FSTOP_MAX = 32.0
FOCUS_MIN = 0.001
FACTORY_EPS = 1e-3

NO_DOF_API = (
    "Depth of field needs camera DoF RNA — update to Blender 5.2, then enable DoF"
)
FOCUS_NO_PRODUCT = "No product to focus — select the mesh or Import Product"
FOCUS_NO_SELECTION = "No mesh selected — select the product or a surface"
DOF_FAILED = "Could not set depth of field — check the camera and try DoF again"
DOF_DISABLED = "DoF off — the still is sharp front to back"
UNKNOWN_FOCUS = "Unknown focus target — pick Focus on product or Focus on selected"


@dataclass(frozen=True)
class DofPlan:
    use_dof: bool
    fstop: float
    focus_distance: float
    clear_focus_object: bool
    autofocus: bool
    target: TargetId


def is_focus(value: str) -> bool:
    return value in ("KEEP", "PRODUCT", "SELECTED")


def normalize_focus(value: str, default: FocusId = "KEEP") -> FocusId:
    raw = (value or "").strip().upper()
    if raw == "PRODUCT":
        return "PRODUCT"
    if raw == "SELECTED":
        return "SELECTED"
    if raw in ("", "KEEP"):
        return "KEEP"
    if default == "PRODUCT":
        return "PRODUCT"
    if default == "SELECTED":
        return "SELECTED"
    return "KEEP"


def clamp_fstop(value: float) -> float:
    return max(FSTOP_MIN, min(FSTOP_MAX, float(value)))


def clamp_focus_distance(value: float) -> float:
    return max(FOCUS_MIN, float(value))


def is_factory_fstop(value: float) -> bool:
    return abs(float(value) - BLENDER_DEFAULT_FSTOP) < FACTORY_EPS


def is_factory_focus(value: float) -> bool:
    return abs(float(value) - BLENDER_DEFAULT_FOCUS) < FACTORY_EPS


def format_fstop(value: float) -> str:
    number = clamp_fstop(value)
    if abs(number - round(number)) < FACTORY_EPS:
        return str(int(round(number)))
    text = f"{number:.2f}".rstrip("0").rstrip(".")
    return text or "5.6"


def aabb_center(
    mins: tuple[float, float, float],
    maxs: tuple[float, float, float],
) -> tuple[float, float, float]:
    center, _size = bounds_center_size(mins, maxs)
    return center


def aabb_nearest_point(
    mins: tuple[float, float, float],
    maxs: tuple[float, float, float],
    point: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Closest point on the AABB to ``point`` — the facing surface."""
    return (
        min(max(point[0], mins[0]), maxs[0]),
        min(max(point[1], mins[1]), maxs[1]),
        min(max(point[2], mins[2]), maxs[2]),
    )


def vector_distance(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> float:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    dz = b[2] - a[2]
    return (dx * dx + dy * dy + dz * dz) ** 0.5


def focus_distance(
    camera: tuple[float, float, float],
    target: tuple[float, float, float],
) -> float:
    return clamp_focus_distance(vector_distance(camera, target))


def product_focus_point(
    mins: tuple[float, float, float],
    maxs: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Catalog plane through the product volume."""
    return aabb_center(mins, maxs)


def selected_focus_point(
    mins: tuple[float, float, float],
    maxs: tuple[float, float, float],
    camera: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Facing surface of the selection; fall back to center if the camera is inside."""
    nearest = aabb_nearest_point(mins, maxs, camera)
    if vector_distance(camera, nearest) < FOCUS_MIN:
        return aabb_center(mins, maxs)
    return nearest


def resolve_product_fstop(
    current: float,
    *,
    enabling: bool,
    requested: float | None = None,
) -> float:
    if requested is not None:
        return clamp_fstop(requested)
    if enabling and is_factory_fstop(current):
        return DEFAULT_FSTOP
    return clamp_fstop(current)


def capability_problem(
    *,
    has_dof: bool,
    has_use_dof: bool,
    has_fstop: bool,
    has_focus_distance: bool,
) -> str | None:
    if has_dof and has_use_dof and has_fstop and has_focus_distance:
        return None
    return NO_DOF_API


def plan_focus_distance(
    *,
    focus: FocusId,
    camera: tuple[float, float, float],
    product_bounds: tuple[tuple[float, float, float], tuple[float, float, float]]
    | None,
    selected_bounds: tuple[tuple[float, float, float], tuple[float, float, float]]
    | None,
    current_distance: float,
    use_dof: bool,
) -> tuple[float, TargetId, bool, str | None]:
    """Return (distance, target, autofocus, error)."""
    if focus == "PRODUCT":
        if product_bounds is None:
            return current_distance, "NONE", False, FOCUS_NO_PRODUCT
        mins, maxs = product_bounds
        return (
            focus_distance(camera, product_focus_point(mins, maxs)),
            "PRODUCT",
            True,
            None,
        )
    if focus == "SELECTED":
        if selected_bounds is None:
            return current_distance, "NONE", False, FOCUS_NO_SELECTION
        mins, maxs = selected_bounds
        return (
            focus_distance(camera, selected_focus_point(mins, maxs, camera)),
            "SELECTED",
            True,
            None,
        )
    if focus == "KEEP":
        if (
            use_dof
            and is_factory_focus(current_distance)
            and product_bounds is not None
        ):
            mins, maxs = product_bounds
            return (
                focus_distance(camera, product_focus_point(mins, maxs)),
                "PRODUCT",
                True,
                None,
            )
        return clamp_focus_distance(current_distance), "KEEP", False, None
    unreachable: Never = focus
    raise RuntimeError(f"unhandled focus target: {unreachable}")


def plan_dof(
    *,
    use_dof: bool,
    fstop: float | None,
    current_fstop: float,
    current_focus_distance: float,
    camera: tuple[float, float, float],
    product_bounds: tuple[tuple[float, float, float], tuple[float, float, float]]
    | None,
    selected_bounds: tuple[tuple[float, float, float], tuple[float, float, float]]
    | None,
    focus: str = "KEEP",
    enabling: bool = False,
) -> DofPlan | str:
    if not is_focus(focus):
        raw = (focus or "").strip()
        if raw:
            return UNKNOWN_FOCUS
        focus_id: FocusId = "KEEP"
    else:
        if focus == "PRODUCT":
            focus_id = "PRODUCT"
        elif focus == "SELECTED":
            focus_id = "SELECTED"
        else:
            focus_id = "KEEP"

    turning_on = bool(use_dof) and (enabling or focus_id != "KEEP")
    resolved_fstop = resolve_product_fstop(
        current_fstop,
        enabling=turning_on or (bool(use_dof) and enabling),
        requested=fstop,
    )
    distance, target, autofocus, error = plan_focus_distance(
        focus=focus_id,
        camera=camera,
        product_bounds=product_bounds,
        selected_bounds=selected_bounds,
        current_distance=current_focus_distance,
        use_dof=bool(use_dof),
    )
    if error is not None:
        return error
    return DofPlan(
        use_dof=bool(use_dof),
        fstop=resolved_fstop,
        focus_distance=distance,
        clear_focus_object=autofocus,
        autofocus=autofocus,
        target=target,
    )


def apply_message(plan: DofPlan) -> str:
    if not plan.use_dof:
        return DOF_DISABLED
    shown = format_fstop(plan.fstop)
    distance = plan.focus_distance
    if plan.target == "PRODUCT":
        return f"Focus on product — {distance:.2f} m at f/{shown}"
    if plan.target == "SELECTED":
        return f"Focus on selected — {distance:.2f} m at f/{shown}"
    if plan.target == "KEEP":
        return f"DoF on — f/{shown} at {distance:.2f} m"
    if plan.target == "NONE":
        return f"DoF on — f/{shown} at {distance:.2f} m"
    unreachable: Never = plan.target
    raise RuntimeError(f"unhandled DoF target: {unreachable}")
