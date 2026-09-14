# SPDX-License-Identifier: GPL-3.0-or-later
"""STEP fixture + Import Product dispatch (no Blender GUI)."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, UNIT_CUBE_STEP, load_module

formats = load_module("behold/product_import/formats.py", "behold_formats")
ocp_core = load_module("behold/cad/ocp_core.py", "behold_ocp_core")


class StepFixtureTests(unittest.TestCase):
    def test_fixture_exists_and_is_iso_10303(self) -> None:
        self.assertTrue(UNIT_CUBE_STEP.is_file(), UNIT_CUBE_STEP)
        text = UNIT_CUBE_STEP.read_text(encoding="ascii")
        self.assertTrue(text.startswith("ISO-10303-21;"))
        self.assertIn("END-ISO-10303-21;", text)
        self.assertIn("MANIFOLD_SOLID_BREP", text)
        self.assertIn("CLOSED_SHELL", text)
        self.assertIn("ADVANCED_FACE", text)
        self.assertGreaterEqual(text.count("CARTESIAN_POINT"), 8)
        self.assertIn("AUTOMOTIVE_DESIGN", text)
        readme = UNIT_CUBE_STEP.with_name("README.md").read_text(encoding="utf-8")
        self.assertIn("CC0", readme)
        self.assertIn("generate_unit_cube.py", readme)
        generator = load_module(
            "tests/fixtures/generate_unit_cube.py", "behold_unit_cube_gen"
        )
        self.assertEqual(text, generator.build_step())

    def test_fixture_routes_to_cad_not_mesh(self) -> None:
        path = str(UNIT_CUBE_STEP)
        self.assertEqual(formats.classify_product_file(path), "cad")
        self.assertEqual(formats.product_import_dispatch(path), "cad")
        self.assertEqual(formats.mesh_operator_candidates(path), ())
        self.assertNotEqual(formats.product_import_dispatch(path), "mesh")

        upper = str(UNIT_CUBE_STEP.with_suffix(".STEP"))
        self.assertEqual(formats.product_import_dispatch(upper), "cad")
        self.assertEqual(formats.product_import_dispatch("part.stp"), "cad")
        self.assertEqual(formats.product_import_dispatch("part.obj"), "mesh")

    def test_import_product_operator_uses_shared_dispatch(self) -> None:
        source = (ROOT / "behold" / "product_import" / "operators.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("product_import_dispatch", source)
        self.assertIn("def run_product_import", source)
        self.assertIn("cad_ops.import_cad_file", source)
        self.assertIn("native.import_mesh_file", source)
        tree = ast.parse(source)
        names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertIn("run_product_import", names)

    def test_ocp_tessellates_fixture_when_available(self) -> None:
        if not ocp_core.ocp_available():
            self.skipTest(
                "OCP unavailable — skipping tessellation. "
                "Import Product still classifies the fixture as CAD "
                "(see test_fixture_routes_to_cad_not_mesh)."
            )
        shape, error = ocp_core.read_cad_shape(str(UNIT_CUBE_STEP))
        self.assertIsNone(error, error)
        self.assertIsNotNone(shape)
        verts, faces = ocp_core.tessellate_shape(shape, deflection=0.2)
        self.assertGreater(len(verts), 0)
        self.assertGreater(len(faces), 0)


class SmokeScriptTests(unittest.TestCase):
    def test_smoke_script_is_documented_and_parses(self) -> None:
        script = ROOT / "scripts" / "smoke_step_vertical.py"
        self.assertTrue(script.is_file(), script)
        source = script.read_text(encoding="utf-8")
        ast.parse(source, filename=str(script))
        self.assertIn("run_product_import", source)
        self.assertIn("product_import_dispatch", source)
        self.assertIn("build_studio", source)
        self.assertIn("DRAFT", source)
        self.assertIn("no CAD backend", source)
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        self.assertIn("smoke-step", makefile)
        self.assertIn("smoke_step_vertical.py", makefile)


if __name__ == "__main__":
    unittest.main()
