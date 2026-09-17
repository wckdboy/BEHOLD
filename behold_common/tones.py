# SPDX-License-Identifier: GPL-3.0-or-later
"""First-ship backdrop tones and Kelvin color (no Blender import)."""

from __future__ import annotations

import math

BACKDROP_TONES: dict[str, tuple[float, float, float, float]] = {
    "WHITE": (0.94, 0.94, 0.96, 1.0),
    "GREY": (0.48, 0.48, 0.50, 1.0),
    "BLACK": (0.04, 0.04, 0.045, 1.0),
}


def backdrop_tone_rgba(settings: object) -> tuple[float, float, float, float]:
    tone = getattr(settings, "studio_backdrop_tone", "WHITE")
    return BACKDROP_TONES.get(tone, BACKDROP_TONES["WHITE"])


def kelvin_to_rgb(kelvin: float) -> tuple[float, float, float]:
    temp = max(1000.0, min(40000.0, kelvin)) / 100.0
    if temp <= 66.0:
        r = 1.0
        g = max(0.0, min(1.0, 0.3900815787690196 * math.log(temp) - 0.6318414437886275))
    else:
        r = max(0.0, min(1.0, 1.292936186062745 * ((temp - 60.0) ** -0.1332047592)))
        g = max(0.0, min(1.0, 1.129890860895294 * ((temp - 60.0) ** -0.0755148492)))
    if temp >= 66.0:
        b = 1.0
    elif temp <= 19.0:
        b = 0.0
    else:
        b = max(0.0, min(1.0, 0.543206789110196 * math.log(temp - 10.0) - 1.19625408914))
    return (r, g, b)
