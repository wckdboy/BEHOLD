# SPDX-License-Identifier: GPL-3.0-or-later
"""First-ship backdrop tones (no Blender import)."""

from __future__ import annotations

BACKDROP_TONES: dict[str, tuple[float, float, float, float]] = {
    "WHITE": (0.94, 0.94, 0.96, 1.0),
    "GREY": (0.48, 0.48, 0.50, 1.0),
    "BLACK": (0.04, 0.04, 0.045, 1.0),
}


def backdrop_tone_rgba(settings: object) -> tuple[float, float, float, float]:
    tone = getattr(settings, "studio_backdrop_tone", "WHITE")
    return BACKDROP_TONES.get(tone, BACKDROP_TONES["WHITE"])
