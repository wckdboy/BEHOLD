# SPDX-License-Identifier: GPL-3.0-or-later
"""Empty-state + icons for Lights — no Blender import."""

from dataclasses import dataclass

from ..common.deps import BUILD_STUDIO_OP
from ..common.messages import NO_LIGHTS_NEXT, NO_LIGHTS_TITLE

SECTION_ICONS = {
    "lights": "LIGHT_AREA",
}


@dataclass(frozen=True)
class EmptyState:
    title: str
    hint: str
    operator: str
    operator_text: str
    icon: str


EMPTY_LIGHTS = EmptyState(
    title=NO_LIGHTS_TITLE,
    hint=NO_LIGHTS_NEXT,
    operator=BUILD_STUDIO_OP,
    operator_text="Build Studio",
    icon="OUTLINER_OB_LIGHT",
)
