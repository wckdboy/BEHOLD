# SPDX-License-Identifier: GPL-3.0-or-later
"""Live tessellation regenerate — quality / deflection (no Blender)."""

from __future__ import annotations

import ast
import os
import tempfile
import unittest

from tests.support import ROOT, UNIT_CUBE_STEP, load_addon_module, load_module

regenerate = load_addon_module("behold/cad/regenerate.py", "behold.cad.regenerate")
stepper_api = load_module("behold/cad/stepper_api.py", "behold_stepper_api_regen")
formats = load_module("behold/product_import/formats.py", "behold_formats_regen")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")
ocp_core = load_module("behold/cad/ocp_core.py", "behold_ocp_core_regen")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class QualityPlanTests(unittest.TestCase):
    def test_presets_match_stepper_next_physical_meters(self) -> None:
        self.assertEqual(
            stepper_api.STEPPER_QUALITY_PRESETS["DRAFT"],
            (0.002, 0.6),
        )
        self.assertEqual(
            stepper_api.STEPPER_QUALITY_PRESETS["BALANCED"],
            (0.0008, 0.5),
        )
        self.assertEqual(
            stepper_api.STEPPER_QUALITY_PRESETS["FINE"],
            (0.0002, 0.25),
        )
        self.assertEqual(
            stepper_api.STEPPER_QUALITY_PRESETS["ULTRA"],
            (0.00005, 0.1),
        )
        self.assertEqual(regenerate.DEFAULT_QUALITY, "BALANCED")
        self.assertAlmostEqual(regenerate.DEFAULT_DEFLECTION, 0.0008)
        self.assertEqual(regenerate.CAD_EXTENSIONS, formats.CAD_EXTENSIONS)

    def test_named_presets_ignore_custom_slider(self) -> None:
        plan = regenerate.plan_tessellation("FINE", 0.05)
        self.assertNotIsInstance(plan, str)
        assert not isinstance(plan, str)
        self.assertEqual(plan.quality, "FINE")
        self.assertAlmostEqual(plan.deflection, 0.0002)
        self.assertAlmostEqual(plan.angular, 0.25)
        self.assertEqual(plan.stepper_quality, "FINE")
        self.assertIsNone(plan.stepper_lin_deflection_len)

    def test_custom_clamps_and_passes_lin_deflection_len(self) -> None:
        plan = regenerate.plan_tessellation("CUSTOM", 0.001)
        self.assertNotIsInstance(plan, str)
        assert not isinstance(plan, str)
        self.assertEqual(plan.quality, "CUSTOM")
        self.assertAlmostEqual(plan.deflection, 0.001)
        self.assertAlmostEqual(plan.angular, 0.5)
        self.assertEqual(plan.stepper_quality, "CUSTOM")
        self.assertAlmostEqual(plan.stepper_lin_deflection_len, 0.001)
        huge = regenerate.plan_tessellation("CUSTOM", 9.0)
        assert not isinstance(huge, str)
        self.assertAlmostEqual(huge.deflection, regenerate.MAX_DEFLECTION)
        tiny = regenerate.plan_tessellation("custom", 0.0)
        assert not isinstance(tiny, str)
        self.assertAlmostEqual(tiny.deflection, regenerate.MIN_DEFLECTION)

    def test_unknown_quality_is_sentence_plus_next_step(self) -> None:
        message = regenerate.plan_tessellation("GOBO", 0.001)
        self.assertIsInstance(message, str)
        self.assertIn("Unknown tessellation quality", str(message))
        self.assertIn("Draft", str(message))
        self.assertEqual(regenerate.plan_tessellation("", 0.001).quality, "BALANCED")  # type: ignore[union-attr]

    def test_enum_items_cover_stepper_names(self) -> None:
        ids = [item[0] for item in regenerate.quality_enum_items()]
        self.assertEqual(ids, list(stepper_api.STEPPER_QUALITY_IDS))


class BackendAndCacheTests(unittest.TestCase):
    def test_prefers_stepper_when_available(self) -> None:
        self.assertEqual(
            regenerate.pick_regenerate_backend("OCP", "STEPPER"),
            "STEPPER",
        )
        self.assertEqual(
            regenerate.pick_regenerate_backend("STEPPER", "OCP"),
            "OCP",
        )
        self.assertEqual(
            regenerate.pick_regenerate_backend("OCP", "OCP"),
            "OCP",
        )
        self.assertEqual(
            regenerate.pick_regenerate_backend("STEPPER", "NONE"),
            "NONE",
        )
        self.assertEqual(regenerate.regenerate_strategy("STEPPER"), "stepper_reimport")
        self.assertEqual(regenerate.regenerate_strategy("OCP"), "ocp_inplace")
        self.assertEqual(regenerate.regenerate_strategy("NONE"), "none")

    def test_empty_cache_is_none(self) -> None:
        self.assertIsNone(
            regenerate.resolve_cad_cache(
                scene_filepath="",
                scene_backend="",
                scene_quality="BALANCED",
                scene_deflection=0.0008,
            )
        )
        self.assertEqual(regenerate.classify_cad_source(""), regenerate.SourceProblem("empty"))
        self.assertEqual(
            regenerate.cad_source_problem_message(regenerate.SourceProblem("empty")),
            regenerate.NO_CAD_SOURCE,
        )

    def test_scene_cache_wins_then_object_tags(self) -> None:
        scene = regenerate.resolve_cad_cache(
            scene_filepath="/tmp/housing.step",
            scene_backend="STEPPER",
            scene_quality="FINE",
            scene_deflection=0.0002,
            object_sources=(("/tmp/other.step", "OCP"),),
        )
        self.assertIsNotNone(scene)
        assert scene is not None
        self.assertEqual(scene.filepath, "/tmp/housing.step")
        self.assertEqual(scene.backend, "STEPPER")
        tagged = regenerate.resolve_cad_cache(
            scene_filepath="",
            scene_backend="",
            scene_quality="BALANCED",
            scene_deflection=0.0008,
            object_sources=(("/data/part.stp", "OCP"),),
        )
        assert tagged is not None
        self.assertEqual(tagged.filepath, "/data/part.stp")
        self.assertEqual(tagged.backend, "OCP")

    def test_source_classifier(self) -> None:
        bad = regenerate.classify_cad_source("hero.obj")
        self.assertIsNotNone(bad)
        assert bad is not None
        self.assertEqual(bad.kind, "unsupported")
        self.assertIn("not CAD", regenerate.cad_source_problem_message(bad))
        missing = regenerate.classify_cad_source("/tmp/no-such-housing.step")
        assert missing is not None
        self.assertEqual(missing.kind, "missing")
        self.assertIn("not found", regenerate.cad_source_problem_message(missing))
        ok = regenerate.classify_cad_source(str(UNIT_CUBE_STEP))
        self.assertIsNone(ok)

    def test_error_copy_is_warning(self) -> None:
        self.assertEqual(messages.NO_CAD_SOURCE, regenerate.NO_CAD_SOURCE)
        self.assertEqual(messages.UNKNOWN_CAD_QUALITY, regenerate.UNKNOWN_CAD_QUALITY)
        self.assertEqual(messages.report_type(messages.NO_CAD_SOURCE), "WARNING")
        self.assertEqual(messages.report_type(messages.UNKNOWN_CAD_QUALITY), "WARNING")
        self.assertEqual(
            messages.report_type(regenerate.cad_source_problem_message(
                regenerate.SourceProblem("missing", "gone.step")
            )),
            "WARNING",
        )
        self.assertEqual(
            messages.report_type(regenerate.cad_source_problem_message(
                regenerate.SourceProblem("unsupported", ".obj")
            )),
            "WARNING",
        )
        self.assertEqual(messages.report_type(regenerate.REGENERATE_EMPTY), "ERROR")
        self.assertEqual(messages.report_type(regenerate.REGENERATE_FAILED), "ERROR")
        self.assertIn("Import Product", regenerate.NO_CAD_SOURCE)
        self.assertIn("Regenerate", regenerate.NO_CAD_SOURCE)


class SnapshotMatchTests(unittest.TestCase):
    def test_exact_and_blender_suffix(self) -> None:
        mapping = regenerate.match_snapshots(
            ("housing", "housing.bolt"),
            ("housing.001", "housing.bolt.001"),
        )
        self.assertEqual(mapping["housing.001"], "housing")
        self.assertEqual(mapping["housing.bolt.001"], "housing.bolt")

    def test_one_to_one_fallback(self) -> None:
        mapping = regenerate.match_snapshots(("part",), ("unit_cube",))
        self.assertEqual(mapping["unit_cube"], "part")

    def test_does_not_guess_many_to_one(self) -> None:
        mapping = regenerate.match_snapshots(("a", "b"), ("c",))
        self.assertEqual(mapping, {})

    def test_stem_helper(self) -> None:
        self.assertEqual(regenerate.blender_stem("housing.001"), "housing")
        self.assertEqual(regenerate.blender_stem("housing"), "housing")
        self.assertEqual(regenerate.blender_stem("bolt.12"), "bolt.12")


class StepperKwargsPlanTests(unittest.TestCase):
    def test_named_preset_omits_lin_when_quality_rna_exists(self) -> None:
        plan = regenerate.plan_tessellation("ULTRA", 0.001)
        assert not isinstance(plan, str)
        quality, lin = regenerate.stepper_kwargs_plan(
            plan,
            frozenset({"filepath", "override_file", "quality_preset", "lin_deflection_len"}),
        )
        self.assertEqual(quality, "ULTRA")
        self.assertIsNone(lin)

    def test_custom_passes_lin_deflection_len(self) -> None:
        plan = regenerate.plan_tessellation("CUSTOM", 0.001)
        assert not isinstance(plan, str)
        quality, lin = regenerate.stepper_kwargs_plan(
            plan,
            frozenset({"filepath", "override_file", "quality_preset", "lin_deflection_len"}),
        )
        self.assertEqual(quality, "CUSTOM")
        self.assertAlmostEqual(lin or 0.0, 0.001)

    def test_no_quality_rna_falls_back_to_deflection(self) -> None:
        plan = regenerate.plan_tessellation("FINE", 0.05)
        assert not isinstance(plan, str)
        quality, lin = regenerate.stepper_kwargs_plan(
            plan,
            frozenset({"filepath", "override_file", "lin_deflection_len"}),
        )
        self.assertIsNone(quality)
        self.assertAlmostEqual(lin or 0.0, 0.0002)

    def test_applied_message_names_backend(self) -> None:
        text = regenerate.regenerated_message(
            "/tmp/housing.step",
            backend="STEPPER",
            quality="FINE",
            object_count=2,
        )
        self.assertIn("housing.step", text)
        self.assertIn("STEPper NEXT", text)
        self.assertIn("Fine", text)
        self.assertIn("2 meshes", text)
        self.assertIn(
            "unit_cube.step",
            regenerate.cached_label(str(UNIT_CUBE_STEP)),
        )
        self.assertIn("Import Product", regenerate.cached_label(""))


class OcpTessellationTests(unittest.TestCase):
    def test_angular_argument_is_wired(self) -> None:
        source = _read("behold/cad/ocp_core.py")
        self.assertIn("angular_deflection", source)
        self.assertIn("BRepMesh_IncrementalMesh", source)

    def test_fixture_tessellates_when_ocp_present(self) -> None:
        if not ocp_core.ocp_available():
            self.skipTest("OCP unavailable — regenerate still plans without bindings")
        shape, error = ocp_core.read_cad_shape(str(UNIT_CUBE_STEP))
        self.assertIsNone(error, error)
        coarse = ocp_core.tessellate_shape(shape, deflection=0.2, angular_deflection=0.6)
        self.assertGreater(len(coarse[0]), 0)
        self.assertGreater(len(coarse[1]), 0)


class WiringTests(unittest.TestCase):
    def test_operator_and_properties(self) -> None:
        ops = _read("behold/cad/operators.py")
        props = _read("behold/properties.py")
        apply_src = _read("behold/cad/regenerate_apply.py")
        self.assertIn('bl_idname = "behold.regenerate_cad"', ops)
        self.assertIn('bl_idname = "behold.cleanup_cad"', ops)
        self.assertIn("def regenerate_cad_file", ops)
        self.assertIn("def cleanup_cad_file", ops)
        self.assertIn("invoke_stepper_occ_import", ops)
        self.assertIn("quality_preset", ops)
        self.assertIn("regenerate_ocp", ops)
        self.assertIn("NO_CAD_SOURCE", ops)
        self.assertIn("match_snapshots", ops)
        self.assertIn("restore_snapshot", ops)
        self.assertIn("cad_source_filepath", props)
        self.assertIn("cad_source_backend", props)
        self.assertIn("cad_quality", props)
        self.assertIn("cad_deflection", props)
        self.assertIn("replace_mesh_geometry", apply_src)
        self.assertIn("write_scene_cache", apply_src)
        self.assertIn("snapshot_objects", apply_src)
        self.assertNotIn("INVOKE_DEFAULT", ops)
        self.assertNotIn("stepper.background_import", ops)

    def test_import_writes_cache(self) -> None:
        ops = _read("behold/cad/operators.py")
        self.assertIn("_remember_import", ops)
        self.assertIn("write_scene_cache", ops)
        self.assertIn("tag_cad_meshes", ops)
        tree = ast.parse(ops, filename="operators.py")
        names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        self.assertIn("regenerate_cad_file", names)
        self.assertIn("import_cad_file", names)

    def test_panel_tessellation_card_stays_on_import(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        body = _func_source(source, tree, "draw_import_first_ship")
        self.assertIn("behold.import_product", body)
        self.assertIn("draw_cad_status_line", body)
        self.assertIn("draw_import_tessellation", body)
        self.assertLess(body.index("behold.import_product"), body.index("draw_import_tessellation"))
        self.assertIn("draw_import_cleanup", body)
        tess = _func_source(source, tree, "draw_import_tessellation")
        self.assertIn("cad_quality", tess)
        self.assertIn("cad_deflection", tess)
        self.assertIn("behold.regenerate_cad", tess)
        self.assertIn('text="Tessellation"', tess)
        self.assertIn("CUSTOM", tess)
        self.assertNotIn("BEHOLD_PT_tessellation", source)
        self.assertNotIn("occ_import_step", tess)
        parked = _func_source(source, tree, "draw_import_parked")
        self.assertIn("behold.regenerate_cad", parked)
        self.assertIn("Apply tessellation", parked)
        self.assertIn("behold.cleanup_cad", parked)
        self.assertIn("Apply cleanup", parked)
        self.assertIn("cad_quality", parked)
        self.assertIn("cad_cleanup_fillets", parked)
        self.assertIn("light_ies_filepath", _func_source(source, tree, "draw_lights_ies"))
        self.assertNotIn("behold.regenerate_cad", _func_source(source, tree, "draw_lights_section"))


class TempCadSourceTests(unittest.TestCase):
    def test_existing_step_classifies_ok(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".step", delete=False) as handle:
            handle.write(b"ISO-10303-21;\nEND-ISO-10303-21;\n")
            path = handle.name
        try:
            self.assertIsNone(regenerate.classify_cad_source(path))
            self.assertTrue(os.path.isfile(path))
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
