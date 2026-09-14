# SPDX-License-Identifier: GPL-3.0-or-later
"""Workflow strip, empty-state copy, and chrome constants — no Blender import."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Mapping, Never

from ..brand import (
    HEADER_DRAW_FUNC,
    HERO_ICON,
    PIE_HOTKEY_LABEL,
    PIE_KEY,
    PIE_MENU_ID,
)

# Re-exported so chrome tests can load one bpy-free module.
CHROME_IDS = {
    "header_draw": HEADER_DRAW_FUNC,
    "hero_icon": HERO_ICON,
    "pie_hotkey": PIE_HOTKEY_LABEL,
    "pie_key": PIE_KEY,
    "pie_menu_id": PIE_MENU_ID,
}
from ..materials.presets import (
    EMPTY_NO_MESH,
    EMPTY_NO_MESH_HINT,
    PRESETS,
    material_name_for,
)
from ..studio.camera_ids import is_studio_mesh_name

FlowStepId = Literal["import", "studio", "dress", "shoot"]

SECTION_ICONS: dict[str, str] = {
    "import": "IMPORT",
    "studio": "OUTLINER_OB_LIGHT",
    "shoot": "RENDER_STILL",
    "lights": "LIGHT_AREA",
    "cameras": "CAMERA_DATA",
    "materials": "MATERIAL",
    "advanced": "PREFERENCES",
}

LOOK_MATERIAL_NAMES = frozenset(material_name_for(key) for key in PRESETS)


@dataclass(frozen=True)
class FlowStep:
    id: FlowStepId
    label: str
    icon: str


@dataclass(frozen=True)
class FlowCta:
    operator: str
    label: str
    icon: str


@dataclass(frozen=True)
class EmptyState:
    title: str
    hint: str
    operator: str
    operator_text: str
    icon: str


FLOW_STEPS: tuple[FlowStep, ...] = (
    FlowStep("import", "Import", "IMPORT"),
    FlowStep("studio", "Studio", "OUTLINER_OB_LIGHT"),
    FlowStep("dress", "Dress", "MATERIAL"),
    FlowStep("shoot", "Shoot", "RENDER_STILL"),
)

# Child panels under BEHOLD_PT_main, top-to-bottom. Lights / Cameras are
# inventory on the shoot path; Dress in the strip is the Materials panel.
PANEL_BL_IDNAMES: tuple[str, ...] = (
    "BEHOLD_PT_import",
    "BEHOLD_PT_studio",
    "BEHOLD_PT_lights",
    "BEHOLD_PT_materials",
    "BEHOLD_PT_cameras",
    "BEHOLD_PT_shoot",
    "BEHOLD_PT_advanced",
)

EMPTY_LIGHTS = EmptyState(
    title="No BEHOLD lights yet",
    hint="Build Studio to seed Key, Fill, and Rim",
    operator="behold.build_studio",
    operator_text="Build Studio",
    icon="OUTLINER_OB_LIGHT",
)

EMPTY_CAMERAS = EmptyState(
    title="No BEHOLD cameras yet",
    hint="Build Studio to add a framed product camera",
    operator="behold.build_studio",
    operator_text="Build Studio",
    icon="OUTLINER_OB_LIGHT",
)

EMPTY_MATERIALS = EmptyState(
    title=EMPTY_NO_MESH,
    hint=EMPTY_NO_MESH_HINT,
    operator="behold.import_product",
    operator_text="Import Product",
    icon="IMPORT",
)


def flow_completed(
    *,
    has_product: bool,
    has_studio: bool,
    has_look: bool,
    has_camera: bool,
) -> dict[FlowStepId, bool]:
    """Which Import → Studio → Dress → Shoot steps are done."""
    return {
        "import": has_product,
        "studio": has_studio,
        "dress": has_look,
        "shoot": has_camera,
    }


def next_step(completed: Mapping[str, bool]) -> FlowStepId | None:
    """First incomplete step, or None when the strip is fully checked."""
    for step in FLOW_STEPS:
        if not completed.get(step.id, False):
            return step.id
    return None


def cta_for_step(step_id: FlowStepId) -> FlowCta:
    if step_id == "import":
        return FlowCta("behold.import_product", "Import", "IMPORT")
    if step_id == "studio":
        return FlowCta("behold.build_studio", "Build Studio", "OUTLINER_OB_LIGHT")
    if step_id == "dress":
        return FlowCta("behold.cad_material_assist", "Dress", "MATERIAL")
    if step_id == "shoot":
        return FlowCta("behold.render_still", "Still", "RENDER_STILL")
    unreachable: Never = step_id
    raise RuntimeError(f"unhandled flow step: {unreachable}")


def is_look_material_name(name: str) -> bool:
    return name.split(".", 1)[0] in LOOK_MATERIAL_NAMES


def product_present(*, mesh_names: Iterable[str], tagged_product: bool) -> bool:
    if tagged_product:
        return True
    return any(not is_studio_mesh_name(name) for name in mesh_names)


def studio_present(*, mesh_names: Iterable[str], has_behold_light: bool) -> bool:
    if has_behold_light:
        return True
    return any(is_studio_mesh_name(name) for name in mesh_names)
