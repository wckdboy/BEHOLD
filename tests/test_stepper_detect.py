# SPDX-License-Identifier: GPL-3.0-or-later
"""STEPper NEXT detect helpers and Import panel copy (no bpy)."""

from __future__ import annotations

import ast
import os
import unittest

from tests.support import ROOT, load_module

stepper_api = load_module("behold/cad/stepper_api.py", "behold_stepper_api")


class StepperModuleNameTests(unittest.TestCase):
    def test_extension_id_and_bl_ext_candidates(self) -> None:
        self.assertEqual(stepper_api.STEPPER_EXTENSION_ID, "stepper_next")
        self.assertEqual(
            stepper_api.STEPPER_OCC_IMPORT_OP, "import_scene.occ_import_step"
        )
        self.assertEqual(
            stepper_api.STEPPER_IMPORT_OPS, ("import_scene.occ_import_step",)
        )
        self.assertNotIn(stepper_api.STEPPER_BACKGROUND_OP, stepper_api.STEPPER_IMPORT_OPS)
        self.assertTrue(stepper_api.is_stepper_module_name("stepper_next"))
        self.assertTrue(
            stepper_api.is_stepper_module_name("bl_ext.user_default.stepper_next")
        )
        self.assertTrue(
            stepper_api.is_stepper_module_name("bl_ext.blender_org.stepper_next")
        )
        self.assertTrue(
            stepper_api.is_stepper_module_name("bl_ext.vscode_default.stepper_next")
        )
        self.assertTrue(stepper_api.is_stepper_module_name("STEPper_NEXT"))
        self.assertTrue(stepper_api.is_stepper_module_name("stepper"))
        self.assertFalse(stepper_api.is_stepper_module_name("blenderkit"))
        self.assertFalse(stepper_api.is_stepper_module_name("behold"))

    def test_pick_prefers_documented_candidates(self) -> None:
        names = (
            "behold",
            "bl_ext.user_default.something_else",
            "bl_ext.user_default.stepper_next",
            "stepper",
        )
        self.assertEqual(
            stepper_api.pick_stepper_module(names),
            "bl_ext.user_default.stepper_next",
        )
        self.assertEqual(
            stepper_api.pick_stepper_module(["io_scene_fbx", "stepper_next"]),
            "stepper_next",
        )
        self.assertIsNone(stepper_api.pick_stepper_module(["behold", "blenderkit"]))
        self.assertEqual(
            stepper_api.pick_stepper_module(["bl_ext.team_repo.stepper_next"]),
            "bl_ext.team_repo.stepper_next",
        )


class StepperKwargsTests(unittest.TestCase):
    def test_occ_import_kwargs_are_filepath_plus_override_file(self) -> None:
        kwargs = stepper_api.stepper_occ_import_kwargs("/tmp/housing.step")
        self.assertEqual(kwargs["override_file"], "housing.step")
        self.assertTrue(kwargs["filepath"].endswith("housing.step"))
        self.assertEqual(kwargs["directory"], os.path.dirname(kwargs["filepath"]))
        self.assertEqual(kwargs["quality_preset"], "BALANCED")
        self.assertNotIn("lin_deflection", kwargs)
        self.assertNotIn("ang_deflection", kwargs)
        self.assertEqual(stepper_api.STEPPER_QUALITY_PRESETS["BALANCED"][0], 0.0008)

    def test_unknown_rna_props_are_stripped(self) -> None:
        kwargs = stepper_api.stepper_occ_import_kwargs(
            "/tmp/housing.step",
            known_props=frozenset({"filepath", "override_file"}),
            quality_preset="BALANCED",
            lin_deflection_len=0.001,
        )
        self.assertEqual(
            set(kwargs),
            {"filepath", "override_file"},
        )
        self.assertEqual(kwargs["override_file"], "housing.step")

    def test_lin_deflection_len_only_when_requested_and_known(self) -> None:
        kwargs = stepper_api.stepper_occ_import_kwargs(
            "/tmp/housing.step",
            known_props=frozenset(
                {"filepath", "override_file", "directory", "lin_deflection_len"}
            ),
            quality_preset=None,
            lin_deflection_len=0.001,
        )
        self.assertEqual(kwargs["lin_deflection_len"], 0.001)
        self.assertNotIn("quality_preset", kwargs)
        self.assertNotIn("lin_deflection", kwargs)

    def test_attempts_always_include_override_file(self) -> None:
        attempts = stepper_api.stepper_occ_import_attempts("/data/part.stp")
        self.assertGreaterEqual(len(attempts), 2)
        for kwargs in attempts:
            self.assertEqual(kwargs["override_file"], "part.stp")
            self.assertIn("filepath", kwargs)
            self.assertNotIn("files", kwargs)


class ImportPanelCopyTests(unittest.TestCase):
    def test_status_strings_per_backend(self) -> None:
        stepper = stepper_api.import_panel_copy("STEPPER")
        self.assertEqual(stepper["line"], "STEPper NEXT ready")
        self.assertFalse(stepper["show_install"])
        disabled = stepper_api.import_panel_copy("STEPPER", stepper_needs_enable=True)
        self.assertEqual(disabled["line"], "STEPper NEXT ready")
        self.assertIn("enable", disabled["detail"].lower())
        ocp = stepper_api.import_panel_copy("OCP")
        self.assertEqual(ocp["line"], "OCP fallback")
        self.assertTrue(ocp["show_install"])
        self.assertEqual(ocp["install_label"], "Install STEPper NEXT")
        none = stepper_api.import_panel_copy("NONE")
        self.assertEqual(none["line"], "Install STEPper NEXT")
        self.assertTrue(none["show_install"])
        self.assertIn("5.1", none["detail"] + ocp["detail"])

    def test_loud_failure_messages_point_at_releases(self) -> None:
        url = stepper_api.STEPPER_INSTALL_URL
        self.assertTrue(url.endswith("/releases"))
        missing = stepper_api.missing_cad_backend_message()
        self.assertIn("No CAD backend", missing)
        self.assertIn(url, missing)
        self.assertIn("OBJ", missing)
        enable = stepper_api.stepper_enable_failed_message(
            "bl_ext.user_default.stepper_next", "access denied"
        )
        self.assertIn("bl_ext.user_default.stepper_next", enable)
        self.assertIn("access denied", enable)
        self.assertIn(url, enable)
        failed = stepper_api.stepper_operator_failed_message("TypeError: extra")
        self.assertIn("TypeError: extra", failed)
        self.assertIn(url, failed)
        self.assertIn("no mesh", stepper_api.stepper_no_mesh_message().lower())


class StepperWiringTests(unittest.TestCase):
    def test_operators_call_occ_import_step_not_invoke(self) -> None:
        source = (ROOT / "behold" / "cad" / "operators.py").read_text(encoding="utf-8")
        self.assertIn("invoke_stepper_occ_import", source)
        self.assertIn("STEPPER_OCC_IMPORT_OP", source)
        self.assertIn("override_file", source)
        self.assertIn("behold.open_stepper_install", source)
        self.assertNotIn("INVOKE_DEFAULT", source)
        self.assertNotIn("stepper.background_import", source)
        self.assertNotIn('op("INVOKE_DEFAULT")', source)
        tree = ast.parse(source)
        names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertIn("invoke_stepper_occ_import", names)
        self.assertIn("import_cad_file", names)
        self.assertIn("regenerate_cad_file", names)
        self.assertIn("behold.regenerate_cad", source)

    def test_detect_reexports_constants(self) -> None:
        source = (ROOT / "behold" / "cad" / "detect.py").read_text(encoding="utf-8")
        self.assertIn("STEPPER_INSTALL_URL", source)
        self.assertIn("cad_status_for_draw", source)
        self.assertIn("invalidate_cad_status_cache", source)
        self.assertIn("installed_addon_module_names", source)
        self.assertIn("bl_ext", source)


if __name__ == "__main__":
    unittest.main()
