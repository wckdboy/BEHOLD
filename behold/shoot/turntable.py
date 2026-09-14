# SPDX-License-Identifier: GPL-3.0-or-later
"""Turntable timing, loop plan, and empty-state copy — no Blender import."""

from __future__ import annotations

import math
from typing import NamedTuple, Optional

PIVOT_NAME = "BEHOLD_TurntablePivot"
PROP_CAMERA = "BEHOLD_turntable_camera"
PROP_FRAME_START = "BEHOLD_turntable_prev_start"
PROP_FRAME_END = "BEHOLD_turntable_prev_end"
PROP_BAKED = "BEHOLD_turntable_baked"

DEFAULT_DURATION_S = 6.0
DEFAULT_FPS = 24.0
DEFAULT_FRAMES = 144  # 6 s × 24 fps — documented product default
DEFAULT_ANGLE_RAD = math.tau
MIN_FRAMES = 2

INTERP_LINEAR = "LINEAR"
INTERP_EASE = "EASE"

EMPTY_NO_CAMERA = "No camera — Build Studio or Add Camera"
EMPTY_NO_PRODUCT = "No product — Import or Build Studio"


class TurntablePlan(NamedTuple):
    seconds: float
    fps: float
    frames: int
    frame_start: int
    frame_end: int
    key_start: int
    key_end: int
    angle_start: float
    angle_end: float
    interpolation: str
    loop_friendly: bool


def effective_fps(fps: float, fps_base: float = 1.0) -> float:
    return float(fps) / max(float(fps_base), 1e-9)


def frames_from_duration(seconds: float, fps: float) -> int:
    count = int(round(float(seconds) * float(fps)))
    return max(MIN_FRAMES, count)


def duration_from_frames(frames: int, fps: float) -> float:
    return float(frames) / max(float(fps), 1e-9)


def fcurve_interpolation(mode: str) -> str:
    if mode == INTERP_EASE:
        return "BEZIER"
    return "LINEAR"


def is_loop_friendly(mode: str) -> bool:
    return mode != INTERP_EASE


def empty_state(*, has_camera: bool, has_product: bool) -> Optional[str]:
    if not has_camera:
        return EMPTY_NO_CAMERA
    if not has_product:
        return EMPTY_NO_PRODUCT
    return None


def plan_turntable(
    *,
    seconds: float = DEFAULT_DURATION_S,
    fps: float = DEFAULT_FPS,
    interpolation: str = INTERP_LINEAR,
    start_frame: int = 1,
) -> TurntablePlan:
    """Build a 360° orbit plan.

    Linear is loop-friendly: 360° is keyed one frame past the last rendered
    frame so Play looping does not hold a duplicate start pose. Ease is a
    one-shot spin (0° on the first frame, 360° on the last).
    """
    rate = max(float(fps), 1e-9)
    duration = max(float(seconds), duration_from_frames(MIN_FRAMES, rate))
    frames = frames_from_duration(duration, rate)
    interpolation_key = INTERP_EASE if interpolation == INTERP_EASE else INTERP_LINEAR
    loop = is_loop_friendly(interpolation_key)
    frame_start = int(start_frame)
    frame_end = frame_start + frames - 1
    key_end = frame_end + 1 if loop else frame_end
    return TurntablePlan(
        seconds=duration_from_frames(frames, rate),
        fps=rate,
        frames=frames,
        frame_start=frame_start,
        frame_end=frame_end,
        key_start=frame_start,
        key_end=key_end,
        angle_start=0.0,
        angle_end=DEFAULT_ANGLE_RAD,
        interpolation=fcurve_interpolation(interpolation_key),
        loop_friendly=loop,
    )
