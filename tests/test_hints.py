# SPDX-License-Identifier: GPL-3.0-or-later
"""Material Assist filename hints (no Blender)."""

from __future__ import annotations

import unittest

from tests.support import load_module

hints = load_module("behold/cad/hints.py", "behold_hints")


class HintTests(unittest.TestCase):
    def test_aluminum_part_name(self) -> None:
        self.assertEqual(hints.suggest_query_for_text("Housing_Al6061"), "brushed aluminum")

    def test_steel_and_plastic(self) -> None:
        self.assertEqual(hints.suggest_query_for_text("bracket-ss-304"), "brushed steel")
        self.assertEqual(hints.suggest_query_for_text("cap_abs"), "abs plastic")

    def test_path_uses_stem_before_extension(self) -> None:
        self.assertEqual(
            hints.suggest_query_for_path("/cad/anodized_cover.step"),
            "matte paint",
        )

    def test_stl_defaults_to_plastic(self) -> None:
        self.assertEqual(hints.suggest_query_for_path("prototype.stl"), "abs plastic")
        self.assertEqual(hints.suggest_query_for_path("printer.3mf"), "abs plastic")

    def test_generic_obj_defaults_to_metal(self) -> None:
        self.assertEqual(hints.suggest_query_for_path("widget.obj"), hints.DEFAULT_QUERY)

    def test_parts_rank_custom_hint_then_name(self) -> None:
        self.assertEqual(
            hints.suggest_query_from_parts(
                custom_hints=["STEP_Steel"],
                names=["housing_aluminum"],
                filepath="cap_abs.stl",
            ),
            "brushed steel",
        )
        self.assertEqual(
            hints.suggest_query_from_parts(names=["cap_abs"], filepath="widget.obj"),
            "abs plastic",
        )
        self.assertEqual(
            hints.suggest_query_from_parts(filepath="prototype.stl"),
            "abs plastic",
        )

    def test_empty_text(self) -> None:
        self.assertIsNone(hints.suggest_query_for_text(""))
        self.assertIsNone(hints.suggest_query_for_text("   "))


if __name__ == "__main__":
    unittest.main()
