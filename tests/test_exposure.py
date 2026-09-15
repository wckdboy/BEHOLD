# SPDX-License-Identifier: GPL-3.0-or-later
"""Physical exposure plan and Shoot Look wiring — no Blender import."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module

exposure = load_addon_module("behold/shoot/exposure.py", "behold.shoot.exposure")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class ExposurePlanTests(unittest.TestCase):
    def test_d65_is_neutral_kelvin_and_zero_offset(self) -> None:
        self.assertEqual(exposure.D65_KELVIN, 6500.0)
        self.assertAlmostEqual(exposure.kelvin_to_temperature_offset(6500.0), 0.0)
        self.assertAlmostEqual(exposure.temperature_offset_to_kelvin(0.0), 6500.0)
        self.assertAlmostEqual(exposure.kelvin_to_temperature_offset(5500.0), -1.0)
        self.assertAlmostEqual(exposure.kelvin_to_temperature_offset(7500.0), 1.0)

    def test_clamp_ev_and_kelvin(self) -> None:
        self.assertEqual(exposure.clamp_ev(-12.0), -6.0)
        self.assertEqual(exposure.clamp_ev(12.0), 6.0)
        self.assertEqual(exposure.clamp_kelvin(800.0), 2000.0)
        self.assertEqual(exposure.clamp_kelvin(20000.0), 10000.0)
        self.assertEqual(exposure.clamp_blender_kelvin(6500.0), 6500.0)
        self.assertGreaterEqual(exposure.clamp_blender_kelvin(100.0), 1800.0)

    def test_false_color_picks_agx_name_and_restores(self) -> None:
        self.assertTrue(exposure.is_false_color_transform("False Color"))
        self.assertTrue(exposure.is_false_color_transform("AgX False Color Rec.709"))
        self.assertFalse(exposure.is_false_color_transform("AgX"))
        picked = exposure.pick_false_color_transform(
            ("AgX", "AgX False Color Rec.709", "Standard")
        )
        self.assertEqual(picked, "AgX False Color Rec.709")
        target, saved, restored = exposure.plan_view_transform(
            false_color=True,
            current_view_transform="AgX",
            saved_view_transform="Filmic",
            available_transforms=("AgX", "False Color"),
        )
        self.assertEqual(target, "False Color")
        self.assertEqual(saved, "AgX")
        self.assertFalse(restored)
        target, saved, restored = exposure.plan_view_transform(
            false_color=False,
            current_view_transform="False Color",
            saved_view_transform="AgX",
        )
        self.assertEqual(target, "AgX")
        self.assertTrue(restored)

    def test_ev_does_not_force_agx_over_filmic(self) -> None:
        plan = exposure.plan_exposure(
            exposure_ev=1.5,
            white_balance_kelvin=3200.0,
            false_color=False,
            current_view_transform="Filmic",
            saved_view_transform="AgX",
        )
        self.assertEqual(plan.exposure, 1.5)
        self.assertEqual(plan.kelvin, 3200.0)
        self.assertEqual(plan.view_transform, "Filmic")
        self.assertEqual(plan.restore_transform, "Filmic")
        self.assertFalse(plan.restored)
        self.assertTrue(plan.use_white_balance)

    def test_apply_messages(self) -> None:
        on = exposure.plan_exposure(
            exposure_ev=0.0,
            white_balance_kelvin=6500.0,
            false_color=True,
            current_view_transform="AgX",
        )
        self.assertEqual(exposure.apply_message(on), exposure.FALSE_COLOR_ON)
        off = exposure.plan_exposure(
            exposure_ev=0.0,
            white_balance_kelvin=6500.0,
            false_color=False,
            current_view_transform="False Color",
            saved_view_transform="AgX",
        )
        self.assertEqual(exposure.apply_message(off), exposure.FALSE_COLOR_OFF)
        look = exposure.plan_exposure(
            exposure_ev=-1.0,
            white_balance_kelvin=5500.0,
            false_color=False,
            current_view_transform="AgX",
        )
        self.assertEqual(exposure.apply_message(look), exposure.EXPOSURE_APPLIED)
        self.assertEqual(
            exposure.apply_message(on, view_transform_ok=False),
            exposure.FALSE_COLOR_UNAVAILABLE,
        )
        self.assertEqual(
            exposure.apply_message(look, has_view=False),
            exposure.NO_VIEW_SETTINGS,
        )

    def test_white_balance_api_prefers_52_kelvin(self) -> None:
        self.assertEqual(
            exposure.prefer_white_balance_api(
                ("exposure", "use_white_balance", "white_balance_temperature")
            ),
            exposure.WB_API_WHITE_BALANCE,
        )
        self.assertEqual(
            exposure.prefer_white_balance_api(("exposure", "temperature")),
            exposure.WB_API_TEMPERATURE,
        )
        self.assertEqual(
            exposure.prefer_white_balance_api(("exposure",)),
            exposure.WB_API_NONE,
        )


class ExposureWiringTests(unittest.TestCase):
    def test_apply_module_writes_view_settings(self) -> None:
        apply = _read("behold/shoot/exposure_apply.py")
        self.assertIn("view.exposure", apply)
        self.assertIn("white_balance_temperature", apply)
        self.assertIn("use_white_balance", apply)
        self.assertIn("view_transform", apply)
        self.assertIn("on_exposure_update", apply)
        self.assertIn("plan_exposure", apply)
        ops = _read("behold/shoot/operators.py")
        self.assertIn("from .exposure_apply import apply_exposure", ops)
        self.assertNotIn("view.temperature = (settings.white_balance_kelvin", ops)

    def test_properties_auto_apply(self) -> None:
        props = _read("behold/properties.py")
        self.assertIn("on_exposure_update", props)
        self.assertIn("view_transform_restore", props)
        self.assertIn("white_balance_kelvin", props)
        self.assertIn("exposure_ev", props)
        self.assertIn("false_color", props)

    def test_shoot_look_card_is_compact(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        first = _func_source(source, tree, "draw_shoot_first_ship")
        look = _func_source(source, tree, "draw_look_compact")
        exposure = _func_source(source, tree, "draw_exposure_compact")
        parked = _func_source(source, tree, "draw_shoot_parked")
        self.assertIn("draw_look_compact", first)
        self.assertIn("draw_exposure_compact", first)
        self.assertIn("draw_shots_compact", first)
        self.assertIn("draw_batch_compact", first)
        self.assertIn("draw_turntable_compact", first)
        self.assertLess(first.index("draw_exposure_compact"), first.index("draw_look_compact"))
        self.assertLess(first.index("draw_look_compact"), first.index("draw_shots_compact"))
        self.assertLess(first.index("draw_shots_compact"), first.index("draw_batch_compact"))
        self.assertLess(first.index("draw_batch_compact"), first.index("draw_turntable_compact"))
        self.assertIn("exposure_ev", exposure)
        self.assertIn("white_balance_kelvin", exposure)
        self.assertIn("false_color", exposure)
        self.assertIn('text="EV"', exposure)
        self.assertIn('text="WB"', exposure)
        self.assertIn('text="False Color"', exposure)
        self.assertNotIn("exposure_ev", look)
        self.assertNotIn("batch_angles", look)
        self.assertNotIn("bookmark_camera", look)
        self.assertNotIn("apply_exposure", look)
        self.assertIn("exposure_ev", parked)
        self.assertIn("behold.apply_exposure", parked)
        self.assertIn("BATCH_NO_MESH", parked)
        self.assertNotIn('icon="ERROR"', parked)

    def test_messages_share_exposure_copy(self) -> None:
        self.assertEqual(messages.EXPOSURE_APPLIED, exposure.EXPOSURE_APPLIED)
        self.assertEqual(messages.FALSE_COLOR_ON, exposure.FALSE_COLOR_ON)
        self.assertIn("Color Management", messages.EXPOSURE_APPLIED)
        self.assertIn("AgX", messages.FALSE_COLOR_ON)
        self.assertEqual(
            messages.report_type(messages.FALSE_COLOR_UNAVAILABLE), "WARNING"
        )
        self.assertEqual(messages.report_type(messages.NO_VIEW_SETTINGS), "WARNING")
        self.assertIn("EV", messages.FALSE_COLOR_UNAVAILABLE)


if __name__ == "__main__":
    unittest.main()
