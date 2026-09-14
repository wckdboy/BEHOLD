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
        self.assertEqual(match.group(1), "0.5.0")
        self.assertIn('"version": (0, 5, 0)', init)
        self.assertIn('"blender": (4, 2, 0)', init)
        self.assertIn('blender_version_min = "4.2.0"', manifest)
        self.assertIn("AMIRITE.studio", init)

    def test_stepper_url_documented(self) -> None:
        readme = _read(ROOT / "README.md")
        detect = _read(ADDON / "cad" / "detect.py")
        url = "https://github.com/Peak-Design/STEPper_NEXT"
        self.assertIn(url, readme)
        self.assertIn(url, detect)
        self.assertIn("Import Product", readme)
        self.assertIn("0.5.0", readme)
        self.assertIn("5.2", readme)
        self.assertIn("AMIRITE.studio", readme)
        self.assertIn("Lights", readme)
        self.assertIn("Cameras", readme)

    def test_python_sources_parse(self) -> None:
        files = list(ADDON.rglob("*.py")) + list((ROOT / "tests").glob("*.py"))
        self.assertGreater(len(files), 10)
        for path in files:
            source = _read(path)
            ast.parse(source, filename=str(path))

    def test_import_product_operator_id(self) -> None:
        source = _read(ADDON / "product_import" / "operators.py")
        self.assertIn('bl_idname = "behold.import_product"', source)


if __name__ == "__main__":
    unittest.main()
