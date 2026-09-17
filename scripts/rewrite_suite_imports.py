#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Rewrite extracted suite modules to import from common / local packages."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def rel_common(addon_root: Path, file: Path) -> str:
    rel = file.parent.relative_to(addon_root)
    depth = 0 if str(rel) == "." else len(rel.parts)
    return "." * (depth + 1) + "common"


def patch(path: Path, mapping: list[tuple[str, str]]) -> bool:
    text = path.read_text(encoding="utf-8")
    original = text
    for old, new in mapping:
        text = text.replace(old, new)
    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def walk(addon: str) -> list[Path]:
    root = ROOT / addon
    return [
        path
        for path in root.rglob("*.py")
        if "common" not in path.parts
    ]


def main() -> None:
    changed: list[Path] = []

    for path in walk("behold_studio"):
        prefix = rel_common(ROOT / "behold_studio", path)
        mapping = [
            ("from ..ui.messages import", f"from {prefix}.messages import"),
            ("from ..cad.material_assist import is_behold_product", f"from {prefix}.ids import is_behold_product"),
            ("from .camera_ids import", f"from {prefix}.camera_ids import"),
            ("from . import camera_ids", f"from {prefix} import camera_ids"),
            ("from .tones import", f"from {prefix}.tones import"),
            ("from . import lights as light_lib", f"from {prefix} import geom as light_lib"),
            ("from . import cameras as camera_lib", f"from {prefix} import geom as camera_lib"),
            ("from ..materials.presets import EMPTY_NO_MESH", f"from {prefix}.messages import EMPTY_NO_MESH"),
            ("from ..shoot.quality_apply import apply_render_quality\n", ""),
            ("from ..shoot.resolution_apply import apply_resolution\n", ""),
            ("context.scene.behold", "context.scene.behold_studio"),
            ("scene.behold", "scene.behold_studio"),
        ]
        if patch(path, mapping):
            changed.append(path)

    for path in walk("behold_lighting"):
        prefix = rel_common(ROOT / "behold_lighting", path)
        mapping = [
            ("from ..ui.messages import", f"from {prefix}.messages import"),
            ("from ..cad.material_assist import is_behold_product", f"from {prefix}.ids import is_behold_product"),
            ("from .camera_ids import", f"from {prefix}.camera_ids import"),
            ("from .light_ids import", f"from {prefix}.light_ids import"),
            ("from . import light_ids", f"from {prefix} import light_ids"),
            ("from .tones import", f"from {prefix}.tones import"),
            ("from . import cameras as camera_lib", f"from {prefix} import geom as camera_lib"),
            ("from ..studio import lights as light_lib", "from .. import lights as light_lib"),
            ("context.scene.behold", "context.scene.behold_lighting"),
            ("scene.behold", "scene.behold_lighting"),
        ]
        if patch(path, mapping):
            changed.append(path)

    for path in walk("behold_product"):
        prefix = rel_common(ROOT / "behold_product", path)
        mapping = [
            ("from ..ui.messages import", f"from {prefix}.messages import"),
            ("from .camera_ids import", f"from {prefix}.camera_ids import"),
            ("from . import camera_ids", f"from {prefix} import camera_ids"),
            ("from ..studio.camera_ids import", f"from {prefix}.camera_ids import"),
            ("from ..studio import cameras as camera_lib", "from .. import cameras as camera_lib"),
            ("from ..studio import dof_apply", "from .. import dof_apply"),
            ("from ..studio.tones import", f"from {prefix}.tones import"),
            ("from ..draw_cache import", f"from {prefix}.draw_cache import"),
            ("from ..studio import lights as light_lib", f"from {prefix} import geom as light_lib"),
            ("from . import lights as light_lib", f"from {prefix} import geom as light_lib"),
            ("from ..cad.material_assist import is_behold_product", f"from {prefix}.ids import is_behold_product"),
            ("context.scene.behold", "context.scene.behold_product"),
            ("scene.behold", "scene.behold_product"),
        ]
        if patch(path, mapping):
            changed.append(path)

    for path in walk("behold_utilities"):
        mapping = [
            ("from ..cad.material_assist import is_behold_product", "from .common.ids import is_behold_product"),
            ("from ..studio.camera_ids import is_studio_mesh_name", "from .common.camera_ids import is_studio_mesh_name"),
            ("from ..preferences import get_prefs", "from .preferences import get_prefs"),
            ("context.scene.behold.utilities", "context.scene.behold_utilities"),
            ("scene.behold.utilities", "scene.behold_utilities"),
        ]
        if patch(path, mapping):
            changed.append(path)

    print(f"rewrote {len(changed)} files")
    for path in changed:
        print(" ", path.relative_to(ROOT))


if __name__ == "__main__":
    main()
