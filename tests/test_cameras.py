# SPDX-License-Identifier: GPL-3.0-or-later
"""Product camera kit — naming, framing math, and wiring (no Blender)."""

from __future__ import annotations

import math
import unittest

from tests.support import ROOT, load_module

camera_ids = load_module("behold/studio/camera_ids.py", "behold_camera_ids")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


class CameraIdTests(unittest.TestCase):
    def test_display_strips_prefix(self) -> None:
        self.assertEqual(camera_ids.display_camera_name("BEHOLD_Camera"), "Camera")
        self.assertEqual(camera_ids.display_camera_name("BEHOLD_Camera_001"), "Camera_001")
        self.assertEqual(camera_ids.display_camera_name("Hero"), "Hero")

    def test_behold_camera_name(self) -> None:
        self.assertTrue(camera_ids.is_behold_camera_name("BEHOLD_Camera"))
        self.assertTrue(camera_ids.is_behold_camera_name("BEHOLD_Camera_001"))
        self.assertTrue(camera_ids.is_behold_camera_name("BEHOLD_Camera.001"))
        self.assertFalse(camera_ids.is_behold_camera_name("BEHOLD_Key"))
        self.assertFalse(camera_ids.is_behold_camera_name("BEHOLD_TurntablePivot"))
        self.assertFalse(camera_ids.is_behold_camera_name("BEHOLD_CameraRig"))
        self.assertFalse(camera_ids.is_behold_camera_name("Camera"))

    def test_studio_mesh_names(self) -> None:
        self.assertTrue(camera_ids.is_studio_mesh_name("BEHOLD_Cyclorama"))
        self.assertTrue(camera_ids.is_studio_mesh_name("BEHOLD_ShadowCatcher.001"))
        self.assertFalse(camera_ids.is_studio_mesh_name("housing"))
        self.assertFalse(camera_ids.is_studio_mesh_name("BEHOLD_Camera"))

    def test_next_camera_names(self) -> None:
        self.assertEqual(camera_ids.next_camera_name([]), "BEHOLD_Camera")
        self.assertEqual(
            camera_ids.next_camera_name(["BEHOLD_Camera"]),
            "BEHOLD_Camera_001",
        )
        self.assertEqual(
            camera_ids.next_camera_name(
                ["BEHOLD_Camera", "BEHOLD_Camera_001", "BEHOLD_Camera_003"]
            ),
            "BEHOLD_Camera_004",
        )
        self.assertEqual(
            camera_ids.next_camera_name(["BEHOLD_Camera_002"]),
            "BEHOLD_Camera",
        )

    def test_product_view_is_unit_three_quarter(self) -> None:
        dx, dy, dz = camera_ids.PRODUCT_VIEW_DIRECTION
        self.assertAlmostEqual(dx * dx + dy * dy + dz * dz, 1.0, places=6)
        self.assertLess(dy, 0.0)
        self.assertGreater(dz, 0.0)
        self.assertGreater(dx, 0.0)


class FramingMathTests(unittest.TestCase):
    def test_tele_sits_farther_than_wide(self) -> None:
        wide = camera_ids.frame_distance(1.0, lens_mm=35.0)
        tele = camera_ids.frame_distance(1.0, lens_mm=85.0)
        self.assertGreater(tele, wide)

    def test_distance_scales_with_size(self) -> None:
        one = camera_ids.frame_distance(1.0)
        two = camera_ids.frame_distance(2.0)
        self.assertAlmostEqual(two / one, 2.0, places=5)

    def test_vertical_fov_drives_full_frame_85mm(self) -> None:
        dist = camera_ids.frame_distance(1.0, lens_mm=85.0)
        half = 0.5 * camera_ids.DEFAULT_FRAME_PADDING
        vfov = camera_ids.vertical_fov_rad(85.0)
        expected = half / math.tan(vfov / 2.0)
        self.assertAlmostEqual(dist, expected, places=5)

    def test_offset_matches_distance_and_direction(self) -> None:
        size = 1.0
        offset = camera_ids.product_camera_offset(size, lens_mm=85.0)
        distance = camera_ids.frame_distance(size, lens_mm=85.0)
        length = math.sqrt(sum(c * c for c in offset))
        self.assertAlmostEqual(length, distance, places=5)
        dx, dy, dz = camera_ids.PRODUCT_VIEW_DIRECTION
        self.assertAlmostEqual(offset[0] / distance, dx, places=5)
        self.assertAlmostEqual(offset[1] / distance, dy, places=5)
        self.assertAlmostEqual(offset[2] / distance, dz, places=5)

    def test_clip_range_covers_product(self) -> None:
        start, end = camera_ids.clip_range(1.0, 4.0)
        self.assertGreater(end, start)
        self.assertLess(start, 0.1)
        self.assertGreaterEqual(end, 80.0)

    def test_bounds_center_size(self) -> None:
        center, size = camera_ids.bounds_center_size((-1.0, 0.0, 0.0), (1.0, 2.0, 4.0))
        self.assertEqual(center, (0.0, 1.0, 2.0))
        self.assertEqual(size, 4.0)


class CameraWiringTests(unittest.TestCase):
    def test_operators_register_crud(self) -> None:
        source = _read("behold/shoot/operators.py")
        for bl_id in (
            "behold.add_camera",
            "behold.remove_camera",
            "behold.set_active_camera",
            "behold.frame_camera",
            "behold.clear_cameras",
            "behold.bookmark_camera",
            "behold.use_main_camera",
            "behold.render_still",
            "behold.apply_camera_dof",
            "behold.focus_product",
            "behold.focus_selected",
        ):
            self.assertIn(f'bl_idname = "{bl_id}"', source)
        self.assertIn("resolve_shoot_camera", source)
        self.assertIn("set_active_behold_camera", source)

    def test_properties_expose_active_and_lens(self) -> None:
        source = _read("behold/properties.py")
        self.assertIn("active_camera_name", source)
        self.assertIn("new_camera_lens", source)
        self.assertIn("main_camera_name", source)
        self.assertIn("dof_enabled", source)
        self.assertIn("dof_fstop", source)

    def test_helpers_create_frame_and_resolve(self) -> None:
        source = _read("behold/studio/cameras.py")
        for name in (
            "def is_behold_camera",
            "def iter_behold_cameras",
            "def get_active_behold_camera",
            "def set_active_behold_camera",
            "def resolve_shoot_camera",
            "def add_product_camera",
            "def frame_behold_camera",
            "def remove_behold_camera",
            "def clear_behold_cameras",
            "def product_targets",
            "apply_product_lens",
            'sensor_fit = "HORIZONTAL"',
            "dof_lib.DEFAULT_FSTOP",
        ):
            self.assertIn(name, source)

    def test_build_studio_uses_camera_kit(self) -> None:
        source = _read("behold/studio/setup.py")
        self.assertIn("create_product_camera", source)
        self.assertIn("set_active_behold_camera", source)
        self.assertIn("STUDIO_CAMERA_NAME", source)

    def test_panel_registers_cameras_section(self) -> None:
        source = _read("behold/ui/panels.py")
        self.assertIn("BEHOLD_PT_cameras", source)
        self.assertIn("draw_cameras_section", source)
        self.assertIn("behold.add_camera", source)
        self.assertIn("behold.frame_camera", source)
        self.assertIn("behold.clear_cameras", source)
        self.assertIn("behold.set_active_camera", source)
        self.assertIn("behold.remove_camera", source)
        self.assertIn("draw_cameras_dof", source)
        self.assertIn("behold.focus_product", source)
        self.assertIn("behold.focus_selected", source)


if __name__ == "__main__":
    unittest.main()
