# SPDX-License-Identifier: GPL-3.0-or-later
"""Catalog resolution presets + Shoot Size wiring — no Blender import."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module, load_module

resolution = load_module("behold/shoot/resolution.py", "behold_shoot_resolution")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class ResolutionPresetTests(unittest.TestCase):
    def test_aspect_and_size_labels(self) -> None:
        self.assertEqual(resolution.DEFAULT_ASPECT, "SQUARE")
        self.assertEqual(resolution.DEFAULT_SIZE, "SQ2048")
        aspects = [item[0] for item in resolution.aspect_enum_items()]
        sizes = [item[0] for item in resolution.size_enum_items()]
        self.assertEqual(aspects, ["SQUARE", "PORTRAIT", "LANDSCAPE"])
        self.assertEqual(sizes, ["SQ2048", "HD1080", "UHD4K"])
        self.assertEqual(resolution.aspect_enum_items()[0][1], "Square 1:1")
        self.assertEqual(resolution.aspect_enum_items()[1][1], "Portrait 4:5")
        self.assertEqual(resolution.aspect_enum_items()[2][1], "Landscape 16:9")
        self.assertEqual(resolution.size_enum_items()[0][1], "2048²")
        self.assertEqual(resolution.size_enum_items()[1][1], "1080p")
        self.assertEqual(resolution.size_enum_items()[2][1], "4K")
        self.assertEqual(resolution.aspect_label("SQUARE"), "Square 1:1")
        self.assertEqual(resolution.size_label("SQ2048"), "2048²")
        self.assertEqual(resolution.long_edge_for("HD1080"), 1920)
        self.assertEqual(resolution.long_edge_for("UHD4K"), 3840)
        self.assertEqual(resolution.ratio_for("PORTRAIT"), (4, 5))
        self.assertEqual(resolution.ratio_for("LANDSCAPE"), (16, 9))

    def test_square_2048_is_the_catalog_default(self) -> None:
        self.assertEqual(resolution.resolution_wh("SQUARE", "SQ2048"), (2048, 2048))
        plan = resolution.plan_resolution("", "")
        self.assertIsInstance(plan, resolution.ResolutionPlan)
        self.assertEqual(plan.resolution_x, 2048)
        self.assertEqual(plan.resolution_y, 2048)
        self.assertEqual(plan.resolution_percentage, 100)
        self.assertEqual(plan.pixel_aspect_x, 1.0)
        self.assertEqual(plan.pixel_aspect_y, 1.0)
        self.assertEqual(resolution.summary_label("SQUARE", "SQ2048"), "2048 × 2048")
        self.assertIn("Square 1:1", resolution.apply_message(plan))
        self.assertIn("2048²", resolution.apply_message(plan))
        self.assertIn("square pixels", resolution.apply_message(plan))

    def test_named_video_sizes_keep_native_landscape(self) -> None:
        self.assertEqual(resolution.resolution_wh("LANDSCAPE", "HD1080"), (1920, 1080))
        self.assertEqual(resolution.resolution_wh("LANDSCAPE", "UHD4K"), (3840, 2160))
        self.assertEqual(resolution.resolution_wh("LANDSCAPE", "SQ2048"), (2048, 1152))
        self.assertEqual(resolution.resolution_wh("landscape", "hd1080"), (1920, 1080))

    def test_portrait_4_5_uses_long_edge_as_height(self) -> None:
        self.assertEqual(resolution.resolution_wh("PORTRAIT", "SQ2048"), (1638, 2048))
        self.assertEqual(resolution.resolution_wh("PORTRAIT", "HD1080"), (1536, 1920))
        self.assertEqual(resolution.resolution_wh("PORTRAIT", "UHD4K"), (3072, 3840))
        width, height = resolution.resolution_wh("PORTRAIT", "HD1080")
        self.assertLess(width, height)
        self.assertAlmostEqual(width / height, 4 / 5, places=6)

    def test_square_uses_long_edge_on_both_axes(self) -> None:
        self.assertEqual(resolution.resolution_wh("SQUARE", "HD1080"), (1920, 1920))
        self.assertEqual(resolution.resolution_wh("SQUARE", "UHD4K"), (3840, 3840))

    def test_all_nine_combos_are_square_pixels_and_clamped(self) -> None:
        for aspect in ("SQUARE", "PORTRAIT", "LANDSCAPE"):
            for size in ("SQ2048", "HD1080", "UHD4K"):
                plan = resolution.plan_resolution(aspect, size)
                self.assertIsInstance(plan, resolution.ResolutionPlan, (aspect, size))
                assert isinstance(plan, resolution.ResolutionPlan)
                self.assertGreaterEqual(plan.resolution_x, resolution.MIN_RESOLUTION)
                self.assertGreaterEqual(plan.resolution_y, resolution.MIN_RESOLUTION)
                self.assertEqual(plan.pixel_aspect_x, 1.0)
                self.assertEqual(plan.pixel_aspect_y, 1.0)
                self.assertEqual(plan.resolution_percentage, 100)
                names = [name for name, _value in plan.rna_pairs()]
                self.assertEqual(
                    names,
                    [
                        "resolution_x",
                        "resolution_y",
                        "resolution_percentage",
                        "pixel_aspect_x",
                        "pixel_aspect_y",
                    ],
                )

    def test_unknown_copy_is_sentence_plus_next_step(self) -> None:
        self.assertEqual(
            resolution.plan_resolution("GOBO", "SQ2048"),
            resolution.unknown_aspect_message("GOBO"),
        )
        self.assertEqual(
            resolution.plan_resolution("SQUARE", "GOBO"),
            resolution.unknown_size_message("GOBO"),
        )
        self.assertIn("Gobo", resolution.unknown_aspect_message("Gobo"))
        self.assertIn("Square 1:1", resolution.unknown_aspect_message("Gobo"))
        self.assertIn("Gobo", resolution.unknown_size_message("Gobo"))
        self.assertIn("2048²", resolution.unknown_size_message("Gobo"))
        self.assertEqual(resolution.unknown_aspect_message(""), resolution.UNKNOWN_ASPECT)
        self.assertEqual(resolution.unknown_size_message(""), resolution.UNKNOWN_SIZE)
        self.assertTrue(resolution.is_aspect("SQUARE"))
        self.assertFalse(resolution.is_aspect("GOBO"))
        self.assertTrue(resolution.is_size("UHD4K"))
        self.assertFalse(resolution.is_size("8K"))
        self.assertEqual(resolution.normalize_aspect(""), "SQUARE")
        self.assertEqual(resolution.normalize_size("uhd4k"), "UHD4K")

    def test_shared_copy_matches_messages(self) -> None:
        self.assertEqual(messages.NO_RENDER_SETTINGS, resolution.NO_RENDER_SETTINGS)
        self.assertEqual(messages.RESOLUTION_FAILED, resolution.RESOLUTION_FAILED)
        self.assertEqual(messages.UNKNOWN_ASPECT, resolution.UNKNOWN_ASPECT)
        self.assertEqual(messages.UNKNOWN_SIZE, resolution.UNKNOWN_SIZE)
        self.assertEqual(
            messages.unknown_aspect_preset_message("Gobo"),
            resolution.unknown_aspect_message("Gobo"),
        )
        self.assertEqual(
            messages.unknown_size_preset_message("Gobo"),
            resolution.unknown_size_message("Gobo"),
        )
        self.assertIn(" — ", resolution.NO_RENDER_SETTINGS)
        self.assertIn("Shoot", resolution.NO_RENDER_SETTINGS)
        self.assertEqual(messages.report_type(resolution.NO_RENDER_SETTINGS), "WARNING")
        self.assertEqual(messages.report_type(resolution.UNKNOWN_ASPECT), "WARNING")
        self.assertEqual(messages.report_type(resolution.UNKNOWN_SIZE), "WARNING")
        self.assertEqual(
            messages.report_type(resolution.unknown_aspect_message("Gobo")),
            "WARNING",
        )
        self.assertEqual(
            messages.report_type(resolution.unknown_size_message("Gobo")),
            "WARNING",
        )
        self.assertEqual(messages.report_type(resolution.RESOLUTION_FAILED), "ERROR")


class ResolutionWiringTests(unittest.TestCase):
    def test_apply_writes_render_rna(self) -> None:
        apply = _read("behold/shoot/resolution_apply.py")
        spec = _read("behold/shoot/resolution.py")
        self.assertIn("resolution_x", spec)
        self.assertIn("pixel_aspect_x", spec)
        self.assertIn("resolution_percentage", spec)
        self.assertIn("on_resolution_update", apply)
        self.assertIn("rna_pairs", apply)
        self.assertIn("NO_RENDER_SETTINGS", apply)
        setup = _read("behold/studio/setup.py")
        self.assertIn("apply_resolution(context)", setup)
        batch = _read("behold/shoot/batch_apply.py")
        self.assertIn("apply_resolution(context)", batch)
        smoke = _read("scripts/smoke_step_vertical.py")
        self.assertIn("resolution_x = 128", smoke)

    def test_operators_and_properties(self) -> None:
        ops = _read("behold/shoot/operators.py")
        props = _read("behold/properties.py")
        self.assertIn("from .resolution_apply import apply_resolution", ops)
        self.assertIn('bl_idname = "behold.apply_resolution"', ops)
        self.assertIn("apply_resolution(context)", ops)
        self.assertIn("resolution_aspect", props)
        self.assertIn("resolution_size", props)
        self.assertIn("RESOLUTION_ASPECT_DEFAULT", props)
        self.assertIn("RESOLUTION_SIZE_DEFAULT", props)
        self.assertIn("resolution_aspect_enum_items", props)
        self.assertIn("on_resolution_update", props)
        self.assertIn("Square 1:1", props)
        self.assertIn("2048²", props)

    def test_shoot_size_card_stays_compact(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        first = _func_source(source, tree, "draw_shoot_first_ship")
        size = _func_source(source, tree, "draw_resolution_compact")
        parked = _func_source(source, tree, "draw_shoot_parked")
        self.assertIn("draw_resolution_compact", first)
        self.assertLess(first.index('"DRAFT"'), first.index("draw_resolution_compact"))
        self.assertLess(first.index("draw_resolution_compact"), first.index("draw_look_compact"))
        self.assertIn("SHOOT_ENGINE_HINT", first)
        self.assertIn('"FINAL"', first)
        self.assertIn("resolution_aspect", size)
        self.assertIn("resolution_size", size)
        self.assertIn('text="Size"', size)
        self.assertIn("summary_label", size)
        self.assertNotIn("behold.apply_resolution", size)
        self.assertNotIn("bookmark_camera", size)
        self.assertNotIn("BEHOLD_PT_size", source)
        self.assertNotIn("BEHOLD_PT_resolution", source)
        self.assertNotIn("gobo", first.lower())
        self.assertIn("resolution_aspect", parked)
        self.assertIn("resolution_size", parked)
        self.assertIn("behold.apply_resolution", parked)
        self.assertIn("behold.apply_quality", parked)
        flow = load_addon_module("behold/ui/flow.py", "behold.ui.flow")
        self.assertEqual(
            list(flow.N_PANEL_CLASS_ORDER),
            [
                "BEHOLD_PT_main",
                "BEHOLD_PT_import",
                "BEHOLD_PT_studio",
                "BEHOLD_PT_lights",
                "BEHOLD_PT_materials",
                "BEHOLD_PT_cameras",
                "BEHOLD_PT_shoot",
                "BEHOLD_PT_advanced",
            ],
        )


if __name__ == "__main__":
    unittest.main()
