# SPDX-License-Identifier: GPL-3.0-or-later
"""EEVEE Draft / Cycles Final quality helpers + Shoot wiring (no Blender)."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module, load_module

quality = load_module("behold/shoot/quality.py", "behold_shoot_quality")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class QualityEnginePlanTests(unittest.TestCase):
    def test_draft_prefers_eevee_next(self) -> None:
        available = {
            quality.ENGINE_EEVEE_NEXT,
            quality.ENGINE_EEVEE,
            quality.ENGINE_CYCLES,
        }
        plan = quality.plan_quality("DRAFT", available)
        self.assertIsInstance(plan, quality.QualityPlan)
        self.assertEqual(plan.quality, "DRAFT")
        self.assertEqual(plan.engine_kind, "EEVEE")
        self.assertEqual(plan.engine, quality.ENGINE_EEVEE_NEXT)
        self.assertEqual(plan.engine_label, "EEVEE Next")
        self.assertEqual(plan.samples, 32)
        self.assertFalse(plan.use_denoising)
        self.assertFalse(plan.fallback)
        self.assertEqual(
            plan.engines_to_try,
            (quality.ENGINE_EEVEE_NEXT, quality.ENGINE_EEVEE),
        )
        self.assertIsNotNone(plan.eevee_defaults)
        self.assertTrue(plan.eevee_defaults.use_shadows)
        self.assertTrue(plan.eevee_defaults.use_raytracing)
        self.assertEqual(plan.eevee_defaults.taa_render_samples, 32)
        self.assertEqual(plan.eevee_defaults.shadow_ray_count, 2)
        self.assertIn("EEVEE Next", quality.apply_message(plan))
        self.assertIn("32 samples", quality.apply_message(plan))

    def test_blender_52_eevee_id_is_next(self) -> None:
        plan = quality.plan_quality(
            "DRAFT",
            {quality.ENGINE_EEVEE, quality.ENGINE_CYCLES},
        )
        self.assertIsInstance(plan, quality.QualityPlan)
        self.assertEqual(plan.engine, quality.ENGINE_EEVEE)
        self.assertEqual(plan.engine_label, "EEVEE Next")
        self.assertEqual(plan.engines_to_try, (quality.ENGINE_EEVEE,))

    def test_empty_available_still_tries_eevee_next(self) -> None:
        plan = quality.plan_quality("DRAFT", ())
        self.assertIsInstance(plan, quality.QualityPlan)
        self.assertEqual(plan.engine, quality.ENGINE_EEVEE_NEXT)
        self.assertEqual(plan.engines_to_try, quality.EEVEE_TRY_ORDER)
        self.assertFalse(plan.fallback)

    def test_final_product_hero_stay_cycles(self) -> None:
        available = {
            quality.ENGINE_EEVEE_NEXT,
            quality.ENGINE_CYCLES,
        }
        for key, samples in (
            ("FINAL", 256),
            ("PRODUCT", 128),
            ("HERO", 512),
        ):
            plan = quality.plan_quality(key, available)
            self.assertIsInstance(plan, quality.QualityPlan, key)
            self.assertEqual(plan.engine_kind, "CYCLES", key)
            self.assertEqual(plan.engine, quality.ENGINE_CYCLES, key)
            self.assertEqual(plan.samples, samples, key)
            self.assertTrue(plan.use_denoising, key)
            self.assertFalse(plan.fallback, key)
            self.assertIsNone(plan.eevee_defaults, key)
            self.assertIn("Cycles", quality.apply_message(plan))

    def test_draft_falls_back_to_cycles_when_eevee_missing(self) -> None:
        plan = quality.plan_quality("DRAFT", {quality.ENGINE_CYCLES})
        self.assertIsInstance(plan, quality.QualityPlan)
        self.assertTrue(plan.fallback)
        self.assertEqual(plan.engine_kind, "CYCLES")
        self.assertEqual(plan.engine, quality.ENGINE_CYCLES)
        self.assertEqual(plan.samples, 32)
        self.assertEqual(quality.apply_message(plan), quality.NO_EEVEE)
        self.assertIn("EEVEE Next", quality.NO_EEVEE)
        self.assertIn("Cycles", quality.NO_EEVEE)
        self.assertIn("Still", quality.NO_EEVEE)

    def test_final_without_cycles_is_copy(self) -> None:
        self.assertEqual(
            quality.plan_quality("FINAL", {quality.ENGINE_EEVEE_NEXT}),
            quality.NO_CYCLES,
        )
        self.assertIn("Cycles", quality.NO_CYCLES)
        self.assertIn("Still", quality.NO_CYCLES)

    def test_unknown_quality_is_copy(self) -> None:
        self.assertEqual(quality.plan_quality("ULTRA"), quality.UNKNOWN_QUALITY)
        self.assertIn("Draft", quality.UNKNOWN_QUALITY)
        self.assertTrue(quality.is_quality("DRAFT"))
        self.assertFalse(quality.is_quality("ULTRA"))
        self.assertEqual(quality.normalize_quality(""), "DRAFT")
        self.assertEqual(quality.normalize_quality("hero"), "HERO")

    def test_enum_items_document_engines(self) -> None:
        items = quality.quality_enum_items()
        ids = [item[0] for item in items]
        self.assertEqual(ids, ["DRAFT", "FINAL", "PRODUCT", "HERO"])
        self.assertIn("EEVEE Next", items[0][2])
        self.assertIn("Cycles", items[1][2])
        self.assertEqual(quality.QUALITY_SAMPLES["FINAL"], 256)
        self.assertEqual(quality.SHOOT_ENGINE_HINT, "Draft = EEVEE · Final = Cycles")
        self.assertEqual(quality.engine_kind_for("DRAFT"), "EEVEE")
        self.assertEqual(quality.engine_kind_for("FINAL"), "CYCLES")
        self.assertEqual(quality.engine_kind_for("PRODUCT"), "CYCLES")
        self.assertEqual(quality.engine_kind_for("HERO"), "CYCLES")

    def test_eevee_defaults_rna_pairs_are_cheap_product(self) -> None:
        defaults = quality.product_eevee_defaults(samples=32)
        names = [name for name, _value in defaults.rna_pairs()]
        self.assertIn("use_shadows", names)
        self.assertIn("use_raytracing", names)
        self.assertIn("use_ssr", names)
        self.assertIn("taa_render_samples", names)
        self.assertEqual(dict(defaults.rna_pairs())["taa_render_samples"], 32)
        self.assertLessEqual(defaults.shadow_ray_count, 4)
        fallback = quality.cycles_fallback_plan("DRAFT")
        self.assertTrue(fallback.fallback)
        self.assertEqual(fallback.engines_to_try, quality.CYCLES_TRY_ORDER)
        rewritten = quality.with_engine(fallback, quality.ENGINE_CYCLES)
        self.assertEqual(rewritten.engine, quality.ENGINE_CYCLES)
        self.assertEqual(rewritten.engine_label, "Cycles")


class QualityMessageTests(unittest.TestCase):
    def test_shared_copy_is_sentence_plus_next_step(self) -> None:
        self.assertEqual(messages.NO_EEVEE, quality.NO_EEVEE)
        self.assertEqual(messages.NO_CYCLES, quality.NO_CYCLES)
        self.assertEqual(messages.UNKNOWN_QUALITY, quality.UNKNOWN_QUALITY)
        self.assertEqual(messages.QUALITY_FAILED, quality.QUALITY_FAILED)
        self.assertIn(" — ", quality.NO_EEVEE)
        self.assertIn(" — ", quality.NO_CYCLES)
        self.assertEqual(messages.report_type(quality.NO_EEVEE), "WARNING")
        self.assertEqual(messages.report_type(quality.NO_CYCLES), "WARNING")
        self.assertEqual(messages.report_type(quality.UNKNOWN_QUALITY), "WARNING")
        self.assertEqual(messages.report_type(quality.QUALITY_FAILED), "ERROR")


class QualityWiringTests(unittest.TestCase):
    def test_apply_writes_engine_rna(self) -> None:
        apply = _read("behold/shoot/quality_apply.py")
        spec = _read("behold/shoot/quality.py")
        self.assertIn("BLENDER_EEVEE_NEXT", spec)
        self.assertIn("available_engine_ids", apply)
        self.assertIn("on_quality_update", apply)
        self.assertIn("use_shadows", spec)
        self.assertIn("use_raytracing", spec)
        self.assertIn("rna_pairs", apply)
        self.assertIn("eevee_defaults", apply)
        self.assertIn("taa_render_samples", spec)
        self.assertIn("OPENIMAGEDENOISE", apply)
        self.assertIn("cycles_fallback_plan", apply)
        setup = _read("behold/studio/setup.py")
        self.assertIn("apply_render_quality(context)", setup)
        self.assertNotIn('render.engine = "CYCLES"', setup)

    def test_operators_and_properties(self) -> None:
        ops = _read("behold/shoot/operators.py")
        props = _read("behold/properties.py")
        self.assertIn("from .quality_apply import apply_render_quality", ops)
        self.assertIn("QUALITY_SAMPLES = quality_lib.QUALITY_SAMPLES", ops)
        self.assertIn("engine_label", ops)
        self.assertIn("fallback", ops)
        self.assertIn("quality_enum_items", props)
        self.assertIn("on_quality_update", props)
        self.assertIn("QUALITY_DEFAULT", props)
        self.assertIn("Draft = EEVEE Next", props)
        batch = _read("behold/shoot/batch_apply.py")
        self.assertIn('result.get("ok")', batch)
        smoke = _read("scripts/smoke_step_vertical.py")
        self.assertIn("apply_render_quality", smoke)
        self.assertNotIn('scene.render.engine = "CYCLES"', smoke)

    def test_shoot_card_keeps_draft_final_and_hint(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        first = _func_source(source, tree, "draw_shoot_first_ship")
        parked = _func_source(source, tree, "draw_shoot_parked")
        self.assertIn('"DRAFT"', first)
        self.assertIn('"FINAL"', first)
        self.assertIn("SHOOT_ENGINE_HINT", first)
        self.assertLess(first.index("SHOOT_ENGINE_HINT"), first.index('text="Still"'))
        self.assertIn("draw_look_compact", first)
        self.assertIn("draw_shots_compact", first)
        self.assertNotIn("BEHOLD_PT_engine", source)
        self.assertNotIn("gobo", first.lower())
        self.assertIn("SHOOT_ENGINE_HINT", parked)
        self.assertIn("behold.apply_quality", parked)
        self.assertIn("render_quality", parked)
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
