# SPDX-License-Identifier: GPL-3.0-or-later
"""Auto turntable — timing math, loop plan, and wiring (no Blender)."""

from __future__ import annotations

import math
import unittest

from tests.support import ROOT, load_module

turntable = load_module("behold/shoot/turntable.py", "behold_turntable")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


class TurntableMathTests(unittest.TestCase):
    def test_default_is_six_seconds_at_24fps(self) -> None:
        self.assertEqual(turntable.DEFAULT_DURATION_S, 6.0)
        self.assertEqual(turntable.DEFAULT_FPS, 24.0)
        self.assertEqual(turntable.DEFAULT_FRAMES, 144)
        self.assertEqual(turntable.frames_from_duration(6.0, 24.0), 144)
        self.assertAlmostEqual(turntable.duration_from_frames(144, 24.0), 6.0)

    def test_frames_round_and_minimum(self) -> None:
        self.assertEqual(turntable.frames_from_duration(1.0, 24.0), 24)
        self.assertEqual(turntable.frames_from_duration(0.01, 24.0), turntable.MIN_FRAMES)
        self.assertEqual(turntable.frames_from_duration(6.0, 30.0), 180)

    def test_ntsc_fps_uses_base(self) -> None:
        rate = turntable.effective_fps(30.0, 1.001)
        self.assertAlmostEqual(rate, 30.0 / 1.001, places=6)

    def test_linear_loop_keys_one_past_last_frame(self) -> None:
        plan = turntable.plan_turntable(
            seconds=6.0,
            fps=24.0,
            interpolation=turntable.INTERP_LINEAR,
        )
        self.assertEqual(plan.frames, 144)
        self.assertEqual(plan.frame_start, 1)
        self.assertEqual(plan.frame_end, 144)
        self.assertEqual(plan.key_start, 1)
        self.assertEqual(plan.key_end, 145)
        self.assertTrue(plan.loop_friendly)
        self.assertEqual(plan.interpolation, "LINEAR")
        self.assertAlmostEqual(plan.angle_end, math.tau)
        self.assertAlmostEqual(plan.seconds, 6.0)

    def test_ease_keys_on_last_frame(self) -> None:
        plan = turntable.plan_turntable(
            seconds=6.0,
            fps=24.0,
            interpolation=turntable.INTERP_EASE,
        )
        self.assertEqual(plan.key_end, plan.frame_end)
        self.assertEqual(plan.interpolation, "BEZIER")
        self.assertFalse(plan.loop_friendly)

    def test_unknown_interpolation_is_linear_loop(self) -> None:
        plan = turntable.plan_turntable(interpolation="NOPE")
        self.assertEqual(plan.interpolation, "LINEAR")
        self.assertTrue(plan.loop_friendly)

    def test_fcurve_interpolation_map(self) -> None:
        self.assertEqual(turntable.fcurve_interpolation("LINEAR"), "LINEAR")
        self.assertEqual(turntable.fcurve_interpolation("EASE"), "BEZIER")
        self.assertEqual(turntable.fcurve_interpolation("other"), "LINEAR")


class TurntableEmptyStateTests(unittest.TestCase):
    def test_empty_state_copy(self) -> None:
        self.assertEqual(
            turntable.empty_state(has_camera=False, has_product=True),
            turntable.EMPTY_NO_CAMERA,
        )
        self.assertEqual(
            turntable.empty_state(has_camera=True, has_product=False),
            turntable.EMPTY_NO_PRODUCT,
        )
        self.assertIsNone(turntable.empty_state(has_camera=True, has_product=True))
        self.assertIn("Build Studio", turntable.EMPTY_NO_CAMERA)
        self.assertIn("Add Camera", turntable.EMPTY_NO_CAMERA)
        self.assertIn("Import", turntable.EMPTY_NO_PRODUCT)

    def test_pivot_and_prop_names(self) -> None:
        self.assertEqual(turntable.PIVOT_NAME, "BEHOLD_TurntablePivot")
        self.assertTrue(turntable.PROP_CAMERA.startswith("BEHOLD_"))
        self.assertTrue(turntable.PROP_BAKED.startswith("BEHOLD_"))


class TurntableWiringTests(unittest.TestCase):
    def test_operators_register_setup_play_bake_clear(self) -> None:
        source = _read("behold/shoot/operators.py")
        for bl_id in (
            "behold.setup_turntable",
            "behold.play_turntable",
            "behold.clear_turntable",
            "behold.bake_turntable",
            "behold.render_turntable",
            "behold.render_still",
        ):
            self.assertIn(f'bl_idname = "{bl_id}"', source)
        self.assertIn("turntable_rig.setup_turntable", source)
        self.assertIn("turntable_rig.has_turntable", source)
        self.assertIn("resolve_shoot_camera", source)

    def test_properties_expose_seconds_and_spin(self) -> None:
        source = _read("behold/properties.py")
        self.assertIn("turntable_seconds", source)
        self.assertIn("turntable_interpolation", source)
        self.assertIn("turntable_frames", source)
        self.assertIn("default=6.0", source)
        self.assertIn("default=144", source)
        self.assertIn('("LINEAR", "Linear"', source)
        self.assertIn('("EASE", "Ease"', source)

    def test_rig_uses_active_camera_and_product_bounds(self) -> None:
        source = _read("behold/shoot/turntable_rig.py")
        for name in (
            "def setup_turntable",
            "def clear_turntable",
            "def bake_turntable",
            "def iter_fcurves",
            "resolve_shoot_camera",
            "product_targets",
            "action_get_channelbag_for_slot",
            "keyframe_insert",
            'data_path="rotation_euler"',
            "index=2",
        ):
            self.assertIn(name, source)
        self.assertIn("PROP_BAKED", source)
        self.assertNotIn("apply_exposure", source)

    def test_compact_shoot_row_and_advanced_extras(self) -> None:
        source = _read("behold/ui/panels.py")
        self.assertIn("draw_turntable_compact", source)
        self.assertIn("behold.setup_turntable", source)
        self.assertIn("behold.play_turntable", source)
        self.assertIn("behold.bake_turntable", source)
        self.assertIn("behold.clear_turntable", source)
        self.assertIn("behold.render_turntable", source)
        self.assertIn("turntable_seconds", source)
        self.assertIn("turntable_interpolation", source)
        self.assertIn("EMPTY_NO_CAMERA", source)
        self.assertIn("EMPTY_NO_PRODUCT", source)


if __name__ == "__main__":
    unittest.main()
