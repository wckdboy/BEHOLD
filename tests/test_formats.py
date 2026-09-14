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

    def test_product_import_dispatch_matches_classify(self) -> None:
        self.assertEqual(formats.product_import_dispatch("part.step"), "cad")
        self.assertEqual(formats.product_import_dispatch("part.obj"), "mesh")
        self.assertEqual(formats.product_import_dispatch("notes.pdf"), "unknown")

    def test_dispatch_covers_every_registered_extension(self) -> None:
        for ext in formats.CAD_EXTENSIONS:
            path = f"C:\\parts\\housing.v2{ext.upper()}"
            self.assertEqual(formats.product_import_dispatch(path), "cad", path)
            self.assertEqual(
                formats.product_import_dispatch(path),
                formats.classify_product_file(path),
                path,
            )
        for ext in formats.MESH_EXTENSIONS:
            path = f"/tmp/hero.final{ext}"
            self.assertEqual(formats.product_import_dispatch(path), "mesh", path)
            self.assertTrue(formats.mesh_operator_candidates(path), ext)

    def test_dispatch_unknown_and_empty_paths(self) -> None:
        self.assertEqual(formats.product_import_dispatch(""), "unknown")
        self.assertEqual(formats.product_import_dispatch("file"), "unknown")
        self.assertEqual(formats.product_import_dispatch("file.step.bak"), "unknown")
        self.assertEqual(formats.product_import_dispatch("file.STEP.backup"), "unknown")
        self.assertEqual(formats.extension_of(""), "")
        glob = formats.import_filter_glob()
        for ext in (".stp", ".igs", ".brep", ".brp", ".gltf"):
            self.assertIn(f"*{ext}", glob)


if __name__ == "__main__":
    unittest.main()
