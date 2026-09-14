# SPDX-License-Identifier: GPL-3.0-or-later
"""Cyclorama auto-fit math — no bpy."""

from __future__ import annotations

import math
import unittest

from tests.support import ROOT, load_module

fit = load_module("behold/studio/fit.py", "behold_studio_fit")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _legacy_size(width: float, depth: float, height: float) -> float:
    return max(width, depth, height, 0.1)


class FitMathTests(unittest.TestCase):
    def test_tiny_cube_clamps_and_keeps_margin(self) -> None:
        result = fit.fit_cyclorama(0.01, 0.01, 0.01)
        self.assertEqual(result.width, fit.MIN_EXTENT)
        self.assertEqual(result.depth, fit.MIN_EXTENT)
        self.assertEqual(result.height, fit.MIN_EXTENT)
        self.assertGreaterEqual(result.floor_size, result.horizontal_span * result.margin)
        self.assertGreater(result.floor_size, result.width)
        self.assertGreaterEqual(result.wall_height, result.height * result.headroom)

    def test_long_bar_uses_horizontal_diagonal(self) -> None:
        width, depth, height = 10.0, 1.0, 0.5
        result = fit.fit_cyclorama(width, depth, height)
        expected_span = math.hypot(width, depth)
        self.assertAlmostEqual(result.horizontal_span, expected_span, places=6)
        self.assertGreater(result.horizontal_span, max(width, depth) - 1e-9)
        self.assertAlmostEqual(result.floor_size, expected_span * fit.DEFAULT_MARGIN, places=6)
        self.assertGreaterEqual(result.wall_height, height * fit.DEFAULT_HEADROOM)
        self.assertGreater(result.floor_size, width)
        self.assertGreater(result.floor_size, depth)

    def test_tall_tower_wall_clears_height_with_headroom(self) -> None:
        width, depth, height = 0.5, 0.5, 20.0
        result = fit.fit_cyclorama(width, depth, height)
        self.assertGreaterEqual(result.wall_height, height * fit.DEFAULT_HEADROOM)
        self.assertGreater(result.wall_height, height)
        self.assertGreaterEqual(result.floor_size, height * fit.FLOOR_FROM_HEIGHT)
        self.assertGreater(result.floor_size, math.hypot(width, depth))

    def test_flat_sheet_covers_diagonal_corners(self) -> None:
        width, depth, height = 10.0, 10.0, 0.2
        result = fit.fit_cyclorama(width, depth, height)
        diagonal = math.hypot(width, depth)
        self.assertAlmostEqual(result.horizontal_span, diagonal, places=6)
        self.assertGreater(result.floor_size, diagonal)
        self.assertGreaterEqual(result.floor_size, diagonal * fit.DEFAULT_MARGIN)
        self.assertGreaterEqual(result.wall_height, result.floor_size * fit.WALL_FROM_FLOOR)
        half = result.floor_size * 0.5
        corner = diagonal * 0.5
        self.assertGreater(half, corner)

    def test_margin_scales_floor(self) -> None:
        tight = fit.fit_cyclorama(2.0, 2.0, 2.0, margin=1.5)
        roomy = fit.fit_cyclorama(2.0, 2.0, 2.0, margin=2.5)
        self.assertAlmostEqual(roomy.floor_size / tight.floor_size, 2.5 / 1.5, places=5)
        self.assertGreater(roomy.floor_size, tight.floor_size)
        self.assertEqual(tight.wall_height, roomy.wall_height)

    def test_margin_clamps_nan_and_out_of_range(self) -> None:
        self.assertEqual(fit.clamp_margin(float("nan")), fit.DEFAULT_MARGIN)
        self.assertEqual(fit.clamp_margin(float("inf")), fit.DEFAULT_MARGIN)
        self.assertEqual(fit.clamp_margin(0.1), fit.MIN_MARGIN)
        self.assertEqual(fit.clamp_margin(99.0), fit.MAX_MARGIN)
        result = fit.fit_cyclorama(1.0, 1.0, 1.0, margin=0.0)
        self.assertEqual(result.margin, fit.MIN_MARGIN)

    def test_zero_and_inverted_aabb(self) -> None:
        empty = fit.fit_from_aabb((0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
        self.assertEqual(empty.width, fit.MIN_EXTENT)
        inverted = fit.fit_from_aabb((2.0, 2.0, 2.0), (0.0, 0.0, 0.0))
        self.assertEqual(inverted.width, fit.MIN_EXTENT)
        box = fit.fit_from_aabb((-1.0, -2.0, 0.0), (1.0, 2.0, 3.0))
        self.assertAlmostEqual(box.width, 2.0)
        self.assertAlmostEqual(box.depth, 4.0)
        self.assertAlmostEqual(box.height, 3.0)

    def test_wide_sheet_floor_beats_legacy_max_extent(self) -> None:
        width, depth, height = 8.0, 8.0, 0.3
        result = fit.fit_cyclorama(width, depth, height)
        legacy_floor = _legacy_size(width, depth, height) * 2.5
        self.assertGreater(result.floor_size, legacy_floor)

    def test_lights_sit_outside_the_sweep(self) -> None:
        shapes = (
            (0.01, 0.01, 0.01),
            (10.0, 1.0, 0.5),
            (0.5, 0.5, 20.0),
            (10.0, 10.0, 0.2),
        )
        for width, depth, height in shapes:
            result = fit.fit_cyclorama(width, depth, height)
            for factors in (fit.KEY_OFFSET, fit.FILL_OFFSET, fit.RIM_OFFSET):
                offset = result.scaled_offset(factors)
                self.assertTrue(
                    fit.xy_outside_floor(offset, result.floor_size),
                    msg=f"{(width, depth, height)} offset {offset} inside floor {result.floor_size}",
                )
            self.assertGreater(result.scaled_offset(fit.KEY_OFFSET)[2], result.wall_height * 0.5)

    def test_catcher_matches_floor(self) -> None:
        result = fit.fit_cyclorama(3.0, 1.5, 0.8)
        self.assertEqual(result.catcher_size, result.floor_size)
        self.assertAlmostEqual(result.radius, result.floor_size / fit.FLOOR_FROM_RADIUS)

    def test_headroom_raises_wall_only(self) -> None:
        low = fit.fit_cyclorama(1.0, 1.0, 4.0, headroom=1.2)
        high = fit.fit_cyclorama(1.0, 1.0, 4.0, headroom=2.0)
        self.assertGreater(high.wall_height, low.wall_height)
        self.assertEqual(low.floor_size, high.floor_size)


class FitWiringTests(unittest.TestCase):
    def test_setup_uses_fit_helpers_and_rebuilds_backdrop(self) -> None:
        source = _read("behold/studio/setup.py")
        self.assertIn("from .fit import", source)
        self.assertIn("fit_from_aabb", source)
        self.assertIn("BUILD_NEEDS_MESH", source)
        self.assertIn("EMPTY_NO_MESH", source)
        self.assertIn("No mesh selected", source)
        ops = _read("behold/studio/operators.py")
        self.assertIn("BUILD_NEEDS_MESH", ops)
        self.assertIn("NO_MESH_SELECTED", ops)
        self.assertIn("remove_studio_backdrops", source)
        self.assertIn("studio_margin", source)
        self.assertIn("fit.floor_size", source)
        self.assertIn("fit.wall_height", source)
        self.assertIn("fit.rig_size", source)
        self.assertNotIn("size = max(extents.x, extents.y, extents.z, 0.1)", source)

    def test_properties_expose_studio_margin(self) -> None:
        source = _read("behold/properties.py")
        self.assertIn("studio_margin", source)
        self.assertIn("Studio Margin", source)

    def test_docs_mention_auto_fit(self) -> None:
        readme = _read("README.md")
        checkpoint = _read("CHECKPOINT.md")
        self.assertIn("0.11.0", readme)
        self.assertIn("Studio Margin", readme)
        self.assertIn("auto-fit", checkpoint.lower())
        self.assertIn("test_studio_fit.py", checkpoint)

    def test_margin_stays_off_first_ship_studio(self) -> None:
        source = _read("behold/ui/panels.py")
        first = source.split("def draw_studio_first_ship", 1)[1].split("def ", 1)[0]
        parked = source.split("def draw_studio_parked", 1)[1].split("def ", 1)[0]
        self.assertNotIn("studio_margin", first)
        self.assertIn("studio_margin", parked)
        self.assertIn('text="Build"', first)


if __name__ == "__main__":
    unittest.main()
