# SPDX-License-Identifier: GPL-3.0-or-later
"""Shared operator / empty-state copy — no Blender import."""

from __future__ import annotations

import unittest

from tests.support import ROOT, load_addon_module, load_module

messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")
flow = load_addon_module("behold/ui/flow.py", "behold.ui.flow")
presets = load_module("behold/materials/presets.py", "behold_presets_messages")
turntable = load_module("behold/shoot/turntable.py", "behold_turntable_messages")
invoke = load_module("behold/product_import/invoke.py", "behold_mesh_invoke_messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


class MessageConstantTests(unittest.TestCase):
    def test_empty_state_copy_is_sentence_plus_next_step(self) -> None:
        self.assertEqual(
            messages.NO_MESH_SELECTED,
            "No mesh selected — select the product or Import Product",
        )
        self.assertEqual(messages.NO_MESH_SELECTED, presets.EMPTY_NO_MESH)
        self.assertIn("Import Product", messages.NO_MESH_HINT)
        self.assertEqual(
            messages.NO_LIGHTS,
            messages.em_dash_join(messages.NO_LIGHTS_TITLE, messages.NO_LIGHTS_NEXT),
        )
        self.assertEqual(
            messages.NO_CAMERAS,
            messages.em_dash_join(messages.NO_CAMERAS_TITLE, messages.NO_CAMERAS_NEXT),
        )
        self.assertEqual(messages.NO_CAMERA, turntable.EMPTY_NO_CAMERA)
        self.assertIn("Color Management", messages.EXPOSURE_APPLIED)
        self.assertIn("False Color", messages.FALSE_COLOR_ON)
        self.assertIn("restored", messages.FALSE_COLOR_OFF)
        self.assertEqual(messages.NO_PRODUCT, turntable.EMPTY_NO_PRODUCT)
        self.assertIn("Build Studio", messages.NO_CAMERA)
        self.assertIn("Add Camera", messages.NO_CAMERA)
        self.assertIn("Import Product", messages.NO_PRODUCT)
        self.assertIn("Setup on Shoot", messages.TURNTABLE_NO_SETUP)

    def test_import_helpers_match_invoke(self) -> None:
        self.assertEqual(
            messages.file_not_found_message("/tmp/housing.step"),
            invoke.format_file_not_found_message("/tmp/housing.step"),
        )
        self.assertIn("housing.step", messages.file_not_found_message("/tmp/housing.step"))
        self.assertIn("existing product file", messages.file_not_found_message("x"))
        self.assertEqual(
            messages.unsupported_file_message(".xyz"),
            invoke.format_unsupported_file_message(".xyz"),
        )
        self.assertIn("OBJ", messages.unsupported_file_message(".xyz"))
        self.assertIn("STEP", messages.unsupported_file_message(""))

    def test_named_missing_helpers(self) -> None:
        self.assertIn("Key", messages.light_not_found("Key"))
        self.assertIn("Build Studio or Add Light", messages.light_not_found("Key"))
        self.assertIn("Hero", messages.camera_not_found("Hero"))
        self.assertIn("Add Camera", messages.camera_not_found("Hero"))
        self.assertIn("Bookmark", messages.bookmark_camera_missing("Cam"))
        self.assertEqual(
            messages.unknown_light_preset_message(""),
            messages.UNKNOWN_LIGHT_PRESET,
        )
        self.assertIn("Gobo", messages.unknown_light_preset_message("Gobo"))
        self.assertIn("Softbox", messages.unknown_light_preset_message("Gobo"))

    def test_empty_state_reports_warning_hard_fails_error(self) -> None:
        self.assertEqual(messages.report_type(messages.NO_MESH_SELECTED), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_CAMERA), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_LIGHTS), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_FILE_SELECTED), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_HDRI_FILE), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_WORLD), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_BAKE_PATH), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_LIGHTS_TO_BAKE), "WARNING")
        self.assertEqual(messages.report_type(messages.TURNTABLE_NO_SETUP), "WARNING")
        self.assertEqual(messages.report_type(messages.BATCH_NO_MESH), "WARNING")
        self.assertEqual(messages.report_type(messages.BATCH_NOTHING), "WARNING")
        self.assertEqual(messages.report_type(messages.UPDATE_CHECK_OFFLINE), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_COMPOSITOR), "WARNING")
        self.assertEqual(messages.report_type(messages.LOOK_COMPOSITOR_BUSY), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_LINKING_API), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_LINKING_ENGINE), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_SHADOW_API), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_SELECTION), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_PRODUCT_TO_SOLO), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_DOF_API), "WARNING")
        self.assertEqual(messages.report_type(messages.FOCUS_NO_PRODUCT), "WARNING")
        self.assertEqual(messages.report_type(messages.FOCUS_NO_SELECTION), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_EEVEE), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_CYCLES), "WARNING")
        self.assertEqual(messages.report_type(messages.UNKNOWN_QUALITY), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_RENDER_SETTINGS), "WARNING")
        self.assertEqual(messages.report_type(messages.UNKNOWN_ASPECT), "WARNING")
        self.assertEqual(messages.report_type(messages.UNKNOWN_SIZE), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_CATCHER_API), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_STUDIO), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_PRODUCT_FOR_CATCHER), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_GOBO_TYPE), "WARNING")
        self.assertEqual(messages.report_type(messages.UNKNOWN_GOBO), "ERROR")
        self.assertEqual(messages.report_type(messages.GOBO_NODES_FAILED), "ERROR")
        self.assertEqual(messages.report_type(messages.UNKNOWN_BACKDROP), "WARNING")
        self.assertEqual(messages.report_type(messages.LINKING_FAILED), "ERROR")
        self.assertEqual(messages.report_type(messages.DOF_FAILED), "ERROR")
        self.assertEqual(messages.report_type(messages.QUALITY_FAILED), "ERROR")
        self.assertEqual(messages.report_type(messages.RESOLUTION_FAILED), "ERROR")
        self.assertEqual(messages.report_type(messages.CATCHER_FAILED), "ERROR")
        self.assertEqual(messages.report_set(messages.NO_MESH_SELECTED), {"WARNING"})
        self.assertEqual(
            messages.report_type(messages.file_not_found_message("/tmp/gone.step")),
            "WARNING",
        )
        self.assertEqual(
            messages.report_type(messages.unsupported_file_message(".xyz")),
            "WARNING",
        )
        self.assertEqual(
            messages.report_type(messages.light_not_found("Key")),
            "ERROR",
        )
        self.assertEqual(messages.report_type(messages.UNKNOWN_LIGHT_PRESET), "ERROR")
        self.assertEqual(messages.report_type(messages.UNKNOWN_LOOK_PRESET), "ERROR")
        self.assertEqual(messages.report_type(messages.LOOK_NODES_FAILED), "ERROR")
        self.assertEqual(
            messages.report_type("STEPper NEXT import failed: boom"),
            "ERROR",
        )
        self.assertEqual(messages.warning_set(), {"WARNING"})
        self.assertEqual(messages.error_set(), {"ERROR"})

    def test_panel_empty_states_share_operator_copy(self) -> None:
        self.assertEqual(flow.EMPTY_LIGHTS.title, messages.NO_LIGHTS_TITLE)
        self.assertEqual(flow.EMPTY_LIGHTS.hint, messages.NO_LIGHTS_NEXT)
        self.assertEqual(flow.EMPTY_CAMERAS.title, messages.NO_CAMERAS_TITLE)
        self.assertEqual(flow.EMPTY_CAMERAS.hint, messages.NO_CAMERAS_NEXT)
        self.assertEqual(flow.EMPTY_MATERIALS.title, messages.NO_MESH_SELECTED)
        self.assertEqual(flow.EMPTY_MATERIALS.hint, messages.NO_MESH_HINT)
        self.assertEqual(flow.EMPTY_SHOTS.title, messages.NO_SHOTS_TITLE)
        self.assertEqual(flow.EMPTY_SHOTS.hint, messages.NO_SHOTS_NEXT)
        self.assertEqual(flow.EMPTY_SHOTS.operator, "behold.add_shot")


class OperatorWiringTests(unittest.TestCase):
    def test_primary_operators_import_shared_copy(self) -> None:
        studio = _read("behold/studio/operators.py")
        shoot = _read("behold/shoot/operators.py")
        lights = _read("behold/light_draw/operators.py")
        materials = _read("behold/materials/local_rack.py")
        product = _read("behold/product_import/operators.py")
        cad = _read("behold/cad/operators.py")
        setup = _read("behold/studio/setup.py")
        self.assertIn("NO_MESH_SELECTED", studio)
        self.assertIn("BUILD_NEEDS_MESH", studio)
        self.assertIn("behold.load_hdri", studio)
        self.assertIn("behold.reset_world", studio)
        self.assertIn("behold.bake_hdri", studio)
        self.assertIn("behold.apply_catcher", studio)
        self.assertIn("behold.apply_light_preset", studio)
        self.assertIn("behold.apply_gobo", studio)
        self.assertIn("behold.load_ies", studio)
        self.assertIn("behold.clear_ies", studio)
        self.assertIn("behold.apply_ies", studio)
        self.assertIn("behold.link_selected", studio)
        self.assertIn("behold.exclude_selected", studio)
        self.assertIn("behold.unlink_selected", studio)
        self.assertIn("behold.solo_product_link", studio)
        self.assertIn("EMPTY_NO_MESH", setup)
        self.assertIn("BUILD_NEEDS_MESH = EMPTY_NO_MESH", setup)
        self.assertIn("report_set", studio)
        self.assertIn("NO_CAMERA", shoot)
        self.assertIn("FRAME_NO_PRODUCT", shoot)
        self.assertIn("TURNTABLE_NO_SETUP", shoot)
        self.assertIn("behold.add_shot", shoot)
        self.assertIn("behold.apply_shot", shoot)
        self.assertIn("behold.apply_exposure", shoot)
        self.assertIn("behold.apply_look", shoot)
        self.assertIn("behold.batch_angles", shoot)
        self.assertIn("run_batch_export", shoot)
        self.assertIn("behold.apply_camera_dof", shoot)
        self.assertIn("behold.focus_product", shoot)
        self.assertIn("behold.focus_selected", shoot)
        self.assertIn("behold.apply_quality", shoot)
        self.assertIn("quality_apply", shoot)
        self.assertIn("behold.apply_resolution", shoot)
        apply_src = _read("behold/shoot/exposure_apply.py")
        self.assertIn("on_exposure_update", apply_src)
        self.assertIn("LIGHT_DRAW_NEEDS_VIEWPORT", lights)
        self.assertIn("LIGHT_DRAW_NO_LIGHTS", lights)
        self.assertIn('self.report({"INFO"}, LIGHT_DRAW_NO_LIGHTS)', lights)
        self.assertIn("report_set", materials)
        self.assertIn("NO_FILE_SELECTED", product)
        self.assertIn("unsupported_file_message", product)
        self.assertIn("NO_MESH_SELECTED", cad)
        self.assertIn("NO_FILE_SELECTED", cad)
        self.assertIn("file_not_found_message", cad)
        self.assertIn('self.report({"INFO"}, TURNTABLE_READY_PLAY)', shoot)

    def test_update_check_copy_matches_core(self) -> None:
        core = load_addon_module("behold/updates/core.py", "behold.updates.core")
        check = core.describe_failure("check")
        missing = core.describe_failure("no_zip")
        self.assertEqual(
            messages.UPDATE_CHECK_OFFLINE,
            messages.update_failure_report(check),
        )
        self.assertEqual(
            messages.UPDATE_CHECK_UNAVAILABLE,
            messages.update_failure_report(missing),
        )
        self.assertIn("Could not reach GitHub", messages.UPDATE_CHECK_OFFLINE)
        self.assertIn("Check for updates", messages.UPDATE_CHECK_OFFLINE)
        self.assertIn("Open release", messages.UPDATE_CHECK_UNAVAILABLE)
        self.assertEqual(messages.report_type(messages.UPDATE_CHECK_OFFLINE), "WARNING")
        self.assertEqual(messages.report_type(messages.UPDATE_CHECK_UNAVAILABLE), "WARNING")
        ops = _read("behold/updates/operators.py")
        self.assertIn("update_failure_report", ops)
        self.assertIn("behold.check_updates", ops)


if __name__ == "__main__":
    unittest.main()
