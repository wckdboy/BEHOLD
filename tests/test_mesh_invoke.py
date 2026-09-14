# SPDX-License-Identifier: GPL-3.0-or-later
"""Native mesh importer kwargs and failure messages (no bpy)."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_module

invoke = load_module("behold/product_import/invoke.py", "behold_mesh_invoke")
formats = load_module("behold/product_import/formats.py", "behold_formats")


class MeshKwargAttemptTests(unittest.TestCase):
    def test_attempts_cover_filepath_and_files_patterns(self) -> None:
        attempts = invoke.mesh_import_kwarg_attempts("/tmp/bottle.obj")
        keys = [frozenset(item) for item in attempts]
        self.assertIn(frozenset({"filepath"}), keys)
        self.assertIn(frozenset({"filepath", "directory", "files"}), keys)
        self.assertIn(frozenset({"filepath", "files"}), keys)
        self.assertIn(frozenset({"directory", "files"}), keys)
        for kwargs in attempts:
            if "files" in kwargs:
                self.assertEqual(kwargs["files"], [{"name": "bottle.obj"}])
            if "filepath" in kwargs:
                self.assertTrue(kwargs["filepath"].endswith("bottle.obj"))


class MeshFailureMessageTests(unittest.TestCase):
    def test_failure_includes_operator_and_reason(self) -> None:
        message = invoke.format_mesh_import_failure(
            "/tmp/rig.fbx",
            operator_id="import_scene.fbx",
            errors=["TypeError: unexpected keyword argument 'files'"],
        )
        self.assertIn("import_scene.fbx", message)
        self.assertIn("rig.fbx", message)
        self.assertIn("TypeError", message)

    def test_failure_without_errors_still_names_operator(self) -> None:
        message = invoke.format_mesh_import_failure(
            "print.stl", operator_id="wm.stl_import"
        )
        self.assertEqual(message, "wm.stl_import failed to import print.stl")

    def test_missing_operator_messages_are_actionable(self) -> None:
        three = invoke.format_no_mesh_operator_message(
            ".3mf", formats.mesh_operator_candidates("a.3mf")
        )
        self.assertIn("3MF", three)
        self.assertIn("wm.threemf_import", three)
        fbx = invoke.format_no_mesh_operator_message(
            ".fbx", formats.mesh_operator_candidates("a.fbx")
        )
        self.assertIn("FBX", fbx)
        self.assertIn("5.2", fbx)
        self.assertIn(
            "no mesh objects",
            invoke.format_empty_mesh_import_message("wm.obj_import"),
        )


class NativeWiringTests(unittest.TestCase):
    def test_native_reports_which_operator_failed(self) -> None:
        source = (ROOT / "behold" / "product_import" / "native.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("format_mesh_import_failure", source)
        self.assertIn("mesh_import_kwarg_attempts", source)
        self.assertIn("format_no_mesh_operator_message", source)
        self.assertIn("TypeError", source)
        tree = ast.parse(source)
        names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertIn("invoke_import_operator", names)
        self.assertIn("import_mesh_file", names)


if __name__ == "__main__":
    unittest.main()
