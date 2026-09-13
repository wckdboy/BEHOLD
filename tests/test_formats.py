# SPDX-License-Identifier: GPL-3.0-or-later
"""Format classification for Import Product (no Blender)."""

from __future__ import annotations

import unittest

from tests.support import load_module

formats = load_module("behold/product_import/formats.py", "behold_formats")


class ClassifyProductFileTests(unittest.TestCase):
    def test_cad_extensions(self) -> None:
        for path in (
            "/tmp/part.STEP",
            "housing.stp",
            "tool.iges",
            "body.IGS",
            "solid.brep",
            "x.brp",
        ):
            self.assertEqual(formats.classify_product_file(path), "cad", path)

    def test_mesh_extensions(self) -> None:
        for path in (
            "bottle.obj",
            "rig.fbx",
            "print.STL",
            "hero.glb",
            "hero.gltf",
            "printer.3mf",
        ):
            self.assertEqual(formats.classify_product_file(path), "mesh", path)

    def test_unknown_extension(self) -> None:
        self.assertEqual(formats.classify_product_file("notes.pdf"), "unknown")
        self.assertEqual(formats.classify_product_file("noext"), "unknown")

    def test_filter_glob_covers_mesh_and_cad(self) -> None:
        glob = formats.import_filter_glob()
        for ext in (".obj", ".fbx", ".stl", ".glb", ".gltf", ".3mf", ".step", ".iges"):
            self.assertIn(f"*{ext}", glob)

    def test_obj_prefers_wm_obj_import(self) -> None:
        self.assertEqual(formats.mesh_operator_candidates("a.obj")[0], "wm.obj_import")

    def test_stl_prefers_wm_stl_import(self) -> None:
        self.assertEqual(formats.mesh_operator_candidates("a.stl")[0], "wm.stl_import")

    def test_3mf_lists_native_and_addon_ops(self) -> None:
        candidates = formats.mesh_operator_candidates("a.3mf")
        self.assertIn("wm.threemf_import", candidates)
        self.assertIn("import_mesh.threemf", candidates)

    def test_cad_has_no_mesh_operators(self) -> None:
        self.assertEqual(formats.mesh_operator_candidates("a.step"), ())


if __name__ == "__main__":
    unittest.main()
