# SPDX-License-Identifier: GPL-3.0-or-later
"""Per-body auto-dress — STEP color / name → a local look (no Blender)."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module, load_module

auto_dress = load_addon_module("behold/cad/auto_dress.py", "behold.cad.auto_dress")
hints = load_module("behold/cad/hints.py", "behold_hints_auto_dress")
presets = load_module("behold/materials/presets.py", "behold_presets_auto_dress")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class ColorParseTests(unittest.TestCase):
    def test_rgb_from_floats_and_hex(self) -> None:
        self.assertEqual(auto_dress.rgb_from_any((0.72, 0.73, 0.75)), (0.72, 0.73, 0.75))
        self.assertEqual(auto_dress.rgb_from_any([12, 34, 56, 255]), (12 / 255, 34 / 255, 56 / 255))
        self.assertEqual(auto_dress.rgb_from_any("#C0C0C0")[0], 192 / 255)
        self.assertIsNone(auto_dress.rgb_from_any(None))
        self.assertIsNone(auto_dress.rgb_from_any(""))
        self.assertIsNone(auto_dress.rgb_from_any("nope"))

    def test_placeholder_white_and_blender_grey(self) -> None:
        self.assertTrue(auto_dress.is_placeholder_color((1.0, 1.0, 1.0)))
        self.assertTrue(auto_dress.is_placeholder_color((0.8, 0.8, 0.8)))
        self.assertFalse(auto_dress.is_placeholder_color((0.72, 0.73, 0.75)))
        self.assertIsNone(auto_dress.usable_color((1.0, 1.0, 1.0)))
        self.assertIsNone(auto_dress.preset_for_color((0.8, 0.8, 0.8)))


class ColorPresetTests(unittest.TestCase):
    def test_neutral_metals_and_black_rubber(self) -> None:
        self.assertEqual(auto_dress.preset_for_color((0.72, 0.73, 0.75)), "METAL")
        self.assertEqual(auto_dress.preset_for_color((0.55, 0.55, 0.56)), "METAL")
        self.assertEqual(auto_dress.preset_for_color((0.90, 0.90, 0.92)), "METAL")
        self.assertEqual(auto_dress.preset_for_color((0.05, 0.05, 0.05)), "RUBBER")

    def test_gold_copper_red_blue(self) -> None:
        self.assertEqual(auto_dress.preset_for_color((0.83, 0.69, 0.22)), "METAL")
        self.assertEqual(auto_dress.preset_for_color((0.72, 0.45, 0.20)), "METAL")
        self.assertEqual(auto_dress.preset_for_color((0.75, 0.12, 0.10)), "PAINT")
        self.assertEqual(auto_dress.preset_for_color((0.12, 0.35, 0.75)), "PLASTIC")
        self.assertEqual(auto_dress.preset_for_color((0.20, 0.70, 0.25)), "PLASTIC")
        self.assertEqual(auto_dress.preset_for_color((0.90, 0.85, 0.15)), "PAINT")


class BodyPlanTests(unittest.TestCase):
    def test_name_beats_color(self) -> None:
        plan = auto_dress.plan_body_dress(
            auto_dress.BodyHint(
                name="housing_aluminum",
                color=(0.75, 0.12, 0.10),
            )
        )
        self.assertEqual(plan.preset_id, "METAL")
        self.assertEqual(plan.source, "name")
        self.assertEqual(plan.query, "brushed aluminum")
        self.assertIsNotNone(plan.base_color)
        self.assertTrue(plan.material_name.startswith("BEHOLD_Metal."))

    def test_custom_hint_beats_name(self) -> None:
        plan = auto_dress.plan_body_dress(
            auto_dress.BodyHint(
                name="housing_aluminum",
                custom_hints=("gasket_tpu",),
                color=(0.72, 0.73, 0.75),
            )
        )
        self.assertEqual(plan.preset_id, "RUBBER")
        self.assertEqual(plan.source, "name")
        self.assertEqual(plan.query, "matte rubber")

    def test_material_slot_name(self) -> None:
        plan = auto_dress.plan_body_dress(
            auto_dress.BodyHint(name="Solid3", material_names=("PMMA_clear",))
        )
        self.assertEqual(plan.preset_id, "GLASS")
        self.assertEqual(plan.source, "material")
        self.assertIsNone(plan.base_color)
        self.assertEqual(plan.material_name, "BEHOLD_Glass")

    def test_color_only(self) -> None:
        plan = auto_dress.plan_body_dress(
            auto_dress.BodyHint(name="Body.001", color=(0.10, 0.40, 0.80))
        )
        self.assertEqual(plan.preset_id, "PLASTIC")
        self.assertEqual(plan.source, "color")
        self.assertEqual(plan.base_color, (0.10, 0.40, 0.80))
        self.assertEqual(plan.material_name, "BEHOLD_Plastic.1A66CC")

    def test_default_query_custom_hint_is_ignored(self) -> None:
        plan = auto_dress.plan_body_dress(
            auto_dress.BodyHint(
                name="Solid1",
                custom_hints=(hints.DEFAULT_QUERY,),
                color=(0.12, 0.35, 0.75),
            )
        )
        self.assertEqual(plan.source, "color")
        self.assertEqual(plan.preset_id, "PLASTIC")

    def test_filepath_is_not_a_per_body_fallback(self) -> None:
        plan = auto_dress.plan_body_dress(auto_dress.BodyHint(name="Solid1"))
        self.assertEqual(plan.source, "skip")
        self.assertEqual(plan.preset_id, "")
        # Assist still uses the CAD stem; auto-dress must not.
        self.assertEqual(
            hints.suggest_query_from_parts(filepath="housing_aluminum.step"),
            "brushed aluminum",
        )

    def test_glass_name_does_not_tint(self) -> None:
        plan = auto_dress.plan_body_dress(
            auto_dress.BodyHint(name="lens_glass", color=(0.12, 0.35, 0.75))
        )
        self.assertEqual(plan.preset_id, "GLASS")
        self.assertIsNone(plan.base_color)

    def test_mixed_bodies_keep_separate_looks(self) -> None:
        plans = auto_dress.plan_bodies(
            (
                auto_dress.BodyHint(name="housing_aluminum"),
                auto_dress.BodyHint(name="cap_abs"),
                auto_dress.BodyHint(name="gasket_tpu"),
                auto_dress.BodyHint(name="lens_glass"),
                auto_dress.BodyHint(name="Solid9", color=(0.75, 0.12, 0.10)),
                auto_dress.BodyHint(name="unnamed"),
            )
        )
        presets = [plan.preset_id for plan in plans]
        sources = [plan.source for plan in plans]
        self.assertEqual(presets[:5], ["METAL", "PLASTIC", "RUBBER", "GLASS", "PAINT"])
        self.assertEqual(sources[-1], "skip")
        self.assertEqual(auto_dress.count_by_preset(plans)["METAL"], 1)
        text = auto_dress.auto_dress_summary(plans)
        self.assertIn("Auto-dressed 5 bodies", text)
        self.assertIn("Metal ×1", text)
        self.assertIn("1 skipped — Assist for one look", text)

    def test_all_skipped_copy(self) -> None:
        plans = auto_dress.plan_bodies((auto_dress.BodyHint(name="Solid1"),))
        self.assertEqual(auto_dress.auto_dress_summary(plans), auto_dress.NO_BODY_HINT)
        self.assertIn("Assist", auto_dress.NO_BODY_HINT)
        self.assertIn(" — ", auto_dress.NO_BODY_HINT)

    def test_source_label_is_exhaustive(self) -> None:
        self.assertEqual(auto_dress.source_label("name"), "part name")
        self.assertEqual(auto_dress.source_label("material"), "STEP material name")
        self.assertEqual(auto_dress.source_label("color"), "STEP color")
        self.assertEqual(auto_dress.source_label("skip"), "skipped")

    def test_hint_regexes_are_the_assist_ones(self) -> None:
        self.assertEqual(hints.suggest_query_for_text("Housing_Al6061"), "brushed aluminum")
        plan = auto_dress.plan_body_dress(auto_dress.BodyHint(name="Housing_Al6061"))
        self.assertEqual(plan.query, "brushed aluminum")
        self.assertEqual(presets.preset_for_query(plan.query), "METAL")


class AssistUnchangedTests(unittest.TestCase):
    def test_assist_still_one_look_from_filename(self) -> None:
        query = hints.suggest_query_from_parts(
            names=("Solid1", "Solid2"),
            filepath="housing_aluminum.step",
        )
        self.assertEqual(query, "brushed aluminum")
        self.assertEqual(presets.preset_for_query(query), "METAL")

    def test_parts_or_none_has_no_default(self) -> None:
        self.assertIsNone(hints.suggest_query_from_parts_or_none(names=("Solid1",)))
        self.assertEqual(
            hints.suggest_query_from_parts(names=("Solid1",), filepath="cap_abs.stl"),
            "abs plastic",
        )


class MessageTests(unittest.TestCase):
    def test_no_hint_is_warning(self) -> None:
        self.assertEqual(messages.NO_BODY_HINT, auto_dress.NO_BODY_HINT)
        self.assertEqual(messages.report_type(messages.NO_BODY_HINT), "WARNING")
        self.assertEqual(messages.report_type(messages.AUTO_DRESS_FAILED), "ERROR")
        self.assertEqual(messages.report_type(messages.NO_MESH_SELECTED), "WARNING")


class WiringTests(unittest.TestCase):
    def test_operator_and_runner(self) -> None:
        assist = _read("behold/cad/material_assist.py")
        self.assertIn("def run_auto_dress", assist)
        self.assertIn("def run_material_assist", assist)
        self.assertIn("def body_hint_from_object", assist)
        self.assertIn("plan_bodies", assist)
        self.assertIn("apply_look_to_objects", assist)
        self.assertNotIn("blenderkit_search", assist.split("def run_auto_dress", 1)[1])
        ops = _read("behold/cad/operators.py")
        self.assertIn('bl_idname = "behold.cad_auto_dress"', ops)
        self.assertIn('bl_idname = "behold.cad_material_assist"', ops)
        self.assertIn("BEHOLD_OT_cad_auto_dress", ops)
        self.assertIn("run_auto_dress", ops)
        self.assertIn("run_material_assist", ops)

    def test_cad_import_uses_auto_dress_mesh_keeps_assist(self) -> None:
        post = _read("behold/product_import/operators.py")
        self.assertIn("run_auto_dress", post)
        self.assertIn("run_material_assist", post)
        self.assertIn('kind == "cad"', post)
        source = _read("behold/cad/operators.py")
        self.assertIn("run_auto_dress", source)
        self.assertIn("import_auto_material_assist", source)

    def test_materials_card_keeps_assist_adds_auto_dress(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source)
        body = _func_source(source, tree, "draw_materials_section")
        self.assertIn("behold.cad_material_assist", body)
        self.assertIn("behold.cad_auto_dress", body)
        self.assertIn('text="Assist"', body)
        self.assertIn('text="Auto-dress"', body)
        self.assertLess(body.index("cad_material_assist"), body.index("cad_auto_dress"))
        self.assertIn("EMPTY_NO_MESH", body)
        self.assertNotIn("blenderkit_login", body)
        parked = _func_source(source, tree, "draw_materials_parked")
        self.assertIn("behold.cad_auto_dress", parked)
        self.assertIn("behold.cad_material_assist", parked)
        first_ship = _func_source(source, tree, "draw_import_first_ship")
        self.assertNotIn("cad_auto_dress", first_ship)

    def test_local_rack_tint_helper(self) -> None:
        rack = _read("behold/materials/local_rack.py")
        self.assertIn("def apply_look_to_objects", rack)
        self.assertIn("def apply_to_objects", rack)
        self.assertIn("base_color", rack)

    def test_panel_order_untouched(self) -> None:
        flow = _read("behold/ui/flow.py")
        self.assertIn('"BEHOLD_PT_import"', flow)
        self.assertLess(flow.index("BEHOLD_PT_materials"), flow.index("BEHOLD_PT_cameras"))
        self.assertLess(flow.index("BEHOLD_PT_cameras"), flow.index("BEHOLD_PT_shoot"))
        self.assertIn("behold.cad_material_assist", flow)


if __name__ == "__main__":
    unittest.main()
