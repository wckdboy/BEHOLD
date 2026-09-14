#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""STEP vertical smoke: Import Product → Build Studio → Draft still.

Run **inside Blender** when OCP or STEPper NEXT is present:

    blender --background --python scripts/smoke_step_vertical.py

Or: ``make smoke-step``

Exit codes:
  0  still written
  2  no CAD backend (OCP / STEPper)
  3  fixture did not dispatch to CAD, or import failed
  4  Build Studio failed
  5  render failed
  1  not running inside Blender / addon failed to register
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests" / "fixtures" / "unit_cube.step"

try:
    import bpy
except ImportError:
    sys.stderr.write(
        "This script must run inside Blender:\n"
        "  blender --background --python scripts/smoke_step_vertical.py\n"
        "  make smoke-step\n"
    )
    raise SystemExit(1)

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _die(code: int, message: str) -> None:
    sys.stderr.write(f"BEHOLD STEP smoke: {message}\n")
    raise SystemExit(code)


def _behold_ops_ready() -> bool:
    try:
        return getattr(bpy.ops.behold, "import_product", None) is not None
    except Exception:  # noqa: BLE001
        return False


def _register_behold() -> None:
    if _behold_ops_ready():
        return
    try:
        bpy.ops.preferences.addon_enable(module="behold")
    except Exception:  # noqa: BLE001
        pass
    if _behold_ops_ready():
        return
    import behold as behold_pkg

    behold_pkg.register()
    if not _behold_ops_ready():
        _die(1, "failed to register the BEHOLD add-on")


def _smoke_output_dir() -> Path:
    override = os.environ.get("BEHOLD_SMOKE_OUT", "").strip()
    if override:
        path = Path(override)
    else:
        path = REPO / "dist" / "smoke"
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> None:
    if not FIXTURE.is_file():
        _die(3, f"missing fixture: {FIXTURE}")

    _register_behold()

    from behold.cad import detect
    from behold.cad.stepper_api import missing_cad_backend_message
    from behold.product_import.formats import product_import_dispatch
    from behold.product_import.operators import run_product_import
    from behold.shoot import operators as shoot_ops

    route = product_import_dispatch(str(FIXTURE))
    if route != "cad":
        _die(3, f"fixture dispatched to {route!r}, expected 'cad'")

    status = detect.cad_status()
    if not status.get("can_import"):
        _die(2, missing_cad_backend_message())

    context = bpy.context
    result = run_product_import(
        context,
        str(FIXTURE),
        deflection=0.001,
        auto_studio=True,
        auto_material_assist=False,
    )
    if not result.get("ok"):
        _die(3, result.get("message") or "import failed")
    if result.get("route") != "cad":
        _die(3, f"run_product_import routed to {result.get('route')!r}, not cad")

    notes = result.get("notes") or []
    if "Studio built" not in notes:
        try:
            studio = bpy.ops.behold.build_studio()
        except Exception as exc:  # noqa: BLE001
            _die(4, f"Build Studio failed: {exc}")
        if "FINISHED" not in studio:
            _die(4, f"Build Studio did not finish ({studio})")

    settings = context.scene.behold
    settings.render_quality = "DRAFT"
    shoot_ops.apply_render_quality(context)

    out_dir = _smoke_output_dir()
    still = out_dir / "still.png"
    scene = context.scene
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 128
    scene.render.resolution_y = 128
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(still)

    if scene.camera is None:
        _die(4, "no camera after Build Studio")

    try:
        render = bpy.ops.render.render(write_still=True)
    except Exception as exc:  # noqa: BLE001
        _die(5, f"render failed: {exc}")
    if "FINISHED" not in render:
        _die(5, f"render did not finish ({render})")
    if not still.is_file() or still.stat().st_size < 32:
        _die(5, f"expected still at {still}")

    backend = status.get("backend")
    sys.stdout.write(
        f"BEHOLD STEP smoke OK — {FIXTURE.name} via {backend} → {still}\n"
    )


if __name__ == "__main__":
    main()
