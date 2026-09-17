# SPDX-License-Identifier: GPL-3.0-or-later
"""Physical exposure plan — EV / Kelvin WB / false color (no Blender import).

Maps Shoot Look props onto Color Management. Blender 5.2 uses
``view_settings.exposure``, ``use_white_balance`` + ``white_balance_temperature``
(Kelvin), and the AgX **False Color** view transform. Older builds may only
have a relative ``temperature`` offset from D65.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

D65_KELVIN = 6500.0
EV_MIN = -6.0
EV_MAX = 6.0
KELVIN_MIN = 2000.0
KELVIN_MAX = 10000.0
# ColorManagedViewSettings.white_balance_temperature in Blender 5.2.
BLENDER_KELVIN_MIN = 1800.0
BLENDER_KELVIN_MAX = 100000.0
DEFAULT_VIEW_TRANSFORM = "AgX"
FALSE_COLOR_TRANSFORM = "False Color"
FALSE_COLOR_CANDIDATES = (
    "False Color",
    "False Colour",
    "AgX False Color Rec.709",
    "AgX False Color",
)

EXPOSURE_APPLIED = "Exposure applied — Color Management has EV and white balance"
FALSE_COLOR_ON = "False Color on — meter hot/cold, then toggle off for AgX"
FALSE_COLOR_OFF = "False Color off — restored the previous view look"
FALSE_COLOR_UNAVAILABLE = (
    "False Color is not on this Color Management config — keep AgX and use EV"
)
NO_VIEW_SETTINGS = "No Color Management view on this scene — pick a scene and try again"

WB_API_WHITE_BALANCE = "white_balance_temperature"
WB_API_TEMPERATURE = "temperature"
WB_API_NONE = "none"


@dataclass(frozen=True)
class ExposurePlan:
    exposure: float
    kelvin: float
    temperature_offset: float
    false_color: bool
    view_transform: str
    restore_transform: str
    use_white_balance: bool
    restored: bool


def clamp_ev(ev: float) -> float:
    return max(EV_MIN, min(EV_MAX, float(ev)))


def clamp_kelvin(kelvin: float) -> float:
    return max(KELVIN_MIN, min(KELVIN_MAX, float(kelvin)))


def clamp_blender_kelvin(kelvin: float) -> float:
    return max(BLENDER_KELVIN_MIN, min(BLENDER_KELVIN_MAX, float(kelvin)))


def kelvin_to_temperature_offset(kelvin: float) -> float:
    """Legacy ``view_settings.temperature``: thousands of Kelvin off D65."""
    return (clamp_kelvin(kelvin) - D65_KELVIN) / 1000.0


def temperature_offset_to_kelvin(offset: float) -> float:
    return clamp_kelvin(float(offset) * 1000.0 + D65_KELVIN)


def is_false_color_transform(name: str) -> bool:
    text = (name or "").strip().lower()
    if not text:
        return False
    return "false color" in text or "false colour" in text


def pick_false_color_transform(available: Sequence[str] | None) -> str:
    if not available:
        return FALSE_COLOR_TRANSFORM
    names = tuple(available)
    for candidate in FALSE_COLOR_CANDIDATES:
        if candidate in names:
            return candidate
    for item in names:
        if is_false_color_transform(item):
            return item
    return FALSE_COLOR_TRANSFORM


def sanitize_restore_transform(name: str) -> str:
    cleaned = (name or "").strip()
    if not cleaned or is_false_color_transform(cleaned):
        return DEFAULT_VIEW_TRANSFORM
    return cleaned


def plan_view_transform(
    *,
    false_color: bool,
    current_view_transform: str = "",
    saved_view_transform: str = DEFAULT_VIEW_TRANSFORM,
    available_transforms: Sequence[str] | None = None,
) -> tuple[str, str, bool]:
    """Return (target transform, transform to remember, restored-from-false-color)."""
    saved = sanitize_restore_transform(saved_view_transform)
    current = (current_view_transform or "").strip() or DEFAULT_VIEW_TRANSFORM
    if false_color:
        target = pick_false_color_transform(available_transforms)
        remember = current if not is_false_color_transform(current) else saved
        return target, remember, False
    if is_false_color_transform(current):
        return saved, saved, True
    remember = current if not is_false_color_transform(current) else saved
    return current, remember, False


def plan_exposure(
    *,
    exposure_ev: float,
    white_balance_kelvin: float,
    false_color: bool,
    current_view_transform: str = "",
    saved_view_transform: str = DEFAULT_VIEW_TRANSFORM,
    available_transforms: Sequence[str] | None = None,
) -> ExposurePlan:
    kelvin = clamp_kelvin(white_balance_kelvin)
    view_transform, restore, restored = plan_view_transform(
        false_color=bool(false_color),
        current_view_transform=current_view_transform,
        saved_view_transform=saved_view_transform,
        available_transforms=available_transforms,
    )
    return ExposurePlan(
        exposure=clamp_ev(exposure_ev),
        kelvin=kelvin,
        temperature_offset=kelvin_to_temperature_offset(kelvin),
        false_color=bool(false_color),
        view_transform=view_transform,
        restore_transform=restore,
        use_white_balance=True,
        restored=restored,
    )


def apply_message(
    plan: ExposurePlan,
    *,
    view_transform_ok: bool = True,
    has_view: bool = True,
) -> str:
    if not has_view:
        return NO_VIEW_SETTINGS
    if plan.false_color:
        if view_transform_ok:
            return FALSE_COLOR_ON
        return FALSE_COLOR_UNAVAILABLE
    if plan.restored:
        return FALSE_COLOR_OFF
    return EXPOSURE_APPLIED


def prefer_white_balance_api(attrs: Iterable[str]) -> str:
    names = set(attrs)
    if "white_balance_temperature" in names:
        return WB_API_WHITE_BALANCE
    if "temperature" in names:
        return WB_API_TEMPERATURE
    return WB_API_NONE
