# SPDX-License-Identifier: GPL-3.0-or-later
"""Sanity checks that do not import bpy."""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

from tests.support import ROOT
ADDON = ROOT / "behold"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class AddonLayoutTests(unittest.TestCase):
    def test_versions_agree(self) -> None:
        manifest = _read(ADDON / "blender_manifest.toml")
        init = _read(ADDON / "__init__.py")
        match = re.search(r'^version\s*=\s*"([^"]+)"', manifest, re.M)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "0.18.0")
        self.assertIn('"version": (0, 18, 0)', init)
        self.assertIn('"blender": (4, 2, 0)', init)
        self.assertIn('blender_version_min = "4.2.0"', manifest)
        self.assertIn("AMIRITE.studio", init)
        self.assertIn("VERSION = (0, 18, 0)", _read(ADDON / "brand.py"))

    def test_stepper_url_documented(self) -> None:
        readme = _read(ROOT / "README.md")
        detect = _read(ADDON / "cad" / "detect.py")
        api = _read(ADDON / "cad" / "stepper_api.py")
        url = "https://github.com/Peak-Design/STEPper_NEXT"
        releases = f"{url}/releases"
        self.assertIn(url, readme)
        self.assertIn(releases, api)
        self.assertIn(releases, readme)
        self.assertIn("STEPPER_INSTALL_URL", detect)
        self.assertIn("import_scene.occ_import_step", api)
        self.assertIn("override_file", api)
        self.assertIn("Import Product", readme)
        self.assertIn("0.11.0", readme)
        self.assertIn("0.12.0", readme)
        self.assertIn("0.13.0", readme)
        self.assertIn("0.14.0", readme)
        self.assertIn("0.15.0", readme)
        self.assertIn("0.16.0", readme)
        self.assertIn("0.17.0", readme)
        self.assertIn("0.18.0", readme)
        self.assertIn("Bake HDRI", readme)
        self.assertIn("False Color", readme)
        self.assertIn("Shot Manager", readme)
        self.assertIn("Softbox", readme)
        self.assertIn("docs/brand/behold_logo.png", readme)
        self.assertIn("behold/icons/behold_icon.png", readme)
        self.assertIn("ROADMAP.md", readme)
        self.assertIn("HDRI", readme)
        self.assertIn("5.2", readme)
        self.assertIn("AMIRITE.studio", readme)
        self.assertIn("Lights", readme)
        self.assertIn("Cameras", readme)
        self.assertIn("Turntable", readme)
        self.assertIn("Materials", readme)
        self.assertIn("Lights → Materials → Cameras → Shoot", readme)
        self.assertIn("Shift+Alt+B", readme)
        self.assertIn("pie", readme.lower())
        self.assertIn("smoke_step_vertical.py", readme)
        self.assertIn("smoke-step", readme)
        self.assertIn("Check for updates", readme)
        self.assertIn("STEPper NEXT ready", readme)

    def test_python_sources_parse(self) -> None:
        files = (
            list(ADDON.rglob("*.py"))
            + list((ROOT / "tests").rglob("*.py"))
            + list((ROOT / "scripts").glob("*.py"))
        )
        self.assertGreater(len(files), 10)
        for path in files:
            source = _read(path)
            ast.parse(source, filename=str(path))

    def test_unit_tests_stay_offline(self) -> None:
        banned_roots = {"urllib", "http", "requests"}
        for path in (ROOT / "tests").rglob("*.py"):
            tree = ast.parse(_read(path), filename=str(path))
            for node in ast.walk(tree):
                names: list[str] = []
                if isinstance(node, ast.Import):
                    names.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names.append(node.module)
                for name in names:
                    root = name.split(".", 1)[0]
                    self.assertNotIn(
                        root,
                        banned_roots,
                        f"{path.name} imports {name}",
                    )

    def test_shot_manager_stays_the_014_shoot_card(self) -> None:
        """0.14.0 Shot Manager is on main; this cut must not grow a Shots panel."""
        self.assertTrue((ADDON / "shoot" / "shots.py").is_file())
        self.assertTrue((ADDON / "shoot" / "shots_apply.py").is_file())
        panels = _read(ADDON / "ui" / "panels.py")
        self.assertIn("draw_shots_compact", panels)
        self.assertNotIn("BEHOLD_PT_shots", panels)
        names = {path.name for path in ADDON.rglob("*.py")}
        self.assertNotIn("shot_manager.py", names)

    def test_import_product_operator_id(self) -> None:
        source = _read(ADDON / "product_import" / "operators.py")
        self.assertIn('bl_idname = "behold.import_product"', source)
        cad_ops = _read(ADDON / "cad" / "operators.py")
        self.assertIn('bl_idname = "behold.open_stepper_install"', cad_ops)


if __name__ == "__main__":
    unittest.main()
