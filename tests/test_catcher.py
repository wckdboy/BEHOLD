# SPDX-License-Identifier: GPL-3.0-or-later
"""Ground contact / shadow catcher helpers + Studio wiring (no Blender)."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module

catcher = load_addon_module("behold/studio/catcher.py", "behold.studio.catcher")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class CatcherPlanTests(unittest.TestCase):
    def test_cyclorama_uses_soft_contact_not_the_sweep_as_catcher(self) -> None:
        plan = catcher.plan_catcher(
            enabled=True,
            backdrop="CYCLORAMA",
            width=2.0,
            depth=1.0,
            height=1.5,
            floor_size=8.0,
            has_shadow_catcher=True,
        )
        self.assertIsInstance(plan, catcher.CatcherPlan)
        self.assertEqual(plan.host, "CYCLORAMA")
        self.assertEqual(plan.kind, "CONTACT")
        self.assertTrue(plan.use_contact)
        self.assertFalse(plan.use_cycles_catcher)
        self.assertFalse(plan.use_eevee_fallback)
        self.assertLessEqual(plan.contact_size, plan.catcher_size)
        self.assertAlmostEqual(plan.contact_size, max(2.0, 1.0) * catcher.CONTACT_MARGIN)
        self.assertGreater(plan.contact_offset, 0.0)
        self.assertEqual(plan.contact_strength, catcher.CONTACT_STRENGTH)
        self.assertTrue(plan.light_contact.use_contact_shadow)
        self.assertIn("cyclorama", catcher.apply_message(plan))
        self.assertIn("contact", catcher.apply_message(plan).lower())

    def test_solid_and_hdri_use_optional_plane(self) -> None:
        for backdrop in ("SOLID", "HDRI"):
            plan = catcher.plan_catcher(
                enabled=True,
                backdrop=backdrop,
                width=1.0,
                depth=1.0,
                height=2.0,
                floor_size=4.0,
                has_shadow_catcher=True,
            )
            self.assertIsInstance(plan, catcher.CatcherPlan, backdrop)
            self.assertEqual(plan.host, "PLANE", backdrop)
            self.assertEqual(plan.kind, "PLANE", backdrop)
            self.assertTrue(plan.use_cycles_catcher, backdrop)
            self.assertFalse(plan.use_eevee_fallback, backdrop)
            self.assertTrue(plan.use_contact, backdrop)
            self.assertEqual(plan.catcher_size, 4.0, backdrop)
            self.assertEqual(
                plan.contact_strength,
                catcher.CONTACT_STRENGTH_WITH_PLANE,
                backdrop,
            )
            self.assertIn("plane", catcher.apply_message(plan).lower())
            self.assertIn("Cycles", catcher.apply_message(plan))

    def test_missing_shadow_catcher_rna_falls_back_for_plane(self) -> None:
        plan = catcher.plan_catcher(
            enabled=True,
            backdrop="SOLID",
            width=1.0,
            depth=1.0,
            height=1.0,
            floor_size=3.0,
            has_shadow_catcher=False,
        )
        self.assertIsInstance(plan, catcher.CatcherPlan)
        self.assertFalse(plan.use_cycles_catcher)
        self.assertTrue(plan.use_eevee_fallback)
        self.assertTrue(plan.use_contact)
        self.assertIsNone(
            catcher.capability_problem(
                has_shadow_catcher=False,
                needs_cycles_flag=True,
            )
        )
        self.assertIn("EEVEE", catcher.apply_message(plan))
        self.assertIn("fallback", catcher.apply_message(plan).lower())

    def test_disabled_tears_down_contact(self) -> None:
        plan = catcher.plan_catcher(
            enabled=False,
            backdrop="CYCLORAMA",
            width=1.0,
            depth=1.0,
            height=1.0,
            floor_size=4.0,
        )
        self.assertIsInstance(plan, catcher.CatcherPlan)
        self.assertEqual(plan.kind, "NONE")
        self.assertFalse(plan.use_contact)
        self.assertFalse(plan.use_cycles_catcher)
        self.assertFalse(plan.light_contact.use_contact_shadow)
        self.assertEqual(catcher.apply_message(plan), catcher.CATCHER_OFF)

    def test_unknown_backdrop_is_copy(self) -> None:
        self.assertEqual(
            catcher.plan_catcher(
                enabled=True,
                backdrop="gobo",
                width=1.0,
                depth=1.0,
                height=1.0,
                floor_size=2.0,
            ),
            catcher.UNKNOWN_BACKDROP,
        )
        self.assertEqual(catcher.normalize_backdrop(""), "CYCLORAMA")
        self.assertEqual(catcher.normalize_backdrop("hdri"), "HDRI")
        self.assertTrue(catcher.is_backdrop("SOLID"))
        self.assertFalse(catcher.is_backdrop("SWEEP"))
        self.assertEqual(catcher.host_for("CYCLORAMA"), "CYCLORAMA")
        self.assertEqual(catcher.host_for("SOLID"), "PLANE")
        self.assertEqual(catcher.host_for("HDRI"), "PLANE")
        self.assertEqual(catcher.host_label("CYCLORAMA"), "cyclorama")
        self.assertEqual(catcher.host_label("PLANE"), "plane")

    def test_contact_size_clamps_to_floor_and_nan(self) -> None:
        huge = catcher.contact_size_for(10.0, 10.0, 2.0)
        self.assertEqual(huge, 2.0)
        self.assertGreater(
            catcher.contact_size_for(1.0, 0.5, 8.0),
            1.0,
        )
        self.assertAlmostEqual(
            catcher.contact_size_for(float("nan"), -2.0, 4.0),
            catcher.MIN_EXTENT * catcher.CONTACT_MARGIN,
        )
        offset = catcher.contact_offset_for(2.0)
        self.assertGreaterEqual(offset, catcher.CONTACT_OFFSET_MIN)
        self.assertAlmostEqual(offset, 2.0 * catcher.CONTACT_OFFSET_RATIO)
        self.assertGreaterEqual(
            catcher.light_contact_distance_for(0.01),
            catcher.LIGHT_CONTACT_DISTANCE_MIN,
        )


class CatcherGraphTests(unittest.TestCase):
    def test_contact_graph_is_radial_falloff(self) -> None:
        graph = catcher.contact_graph(0.5)
        keys = [node.key for node in graph.nodes]
        self.assertEqual(
            keys,
            [
                "tex",
                "mapping",
                "gradient",
                "math",
                "transparent",
                "diffuse",
                "mix",
                "output",
            ],
        )
        self.assertEqual(graph.gradient_type, catcher.GRADIENT_SPHERE)
        self.assertEqual(graph.math_operation, "MULTIPLY")
        self.assertEqual(graph.math_value, 0.5)
        self.assertEqual(graph.mapping.location, catcher.CENTER_MAPPING_LOCATION)
        sockets = {(link.from_key, link.to_key) for link in graph.links}
        self.assertIn(("gradient", "math"), sockets)
        self.assertIn(("math", "mix"), sockets)
        self.assertIn(("mix", "output"), sockets)

    def test_fallback_graph_uses_shadow_ray(self) -> None:
        graph = catcher.fallback_graph()
        keys = [node.key for node in graph.nodes]
        self.assertEqual(
            keys,
            ["light_path", "transparent", "diffuse", "mix", "output"],
        )
        fac = next(link for link in graph.links if link.to_key == "mix" and link.to_socket == 0)
        self.assertEqual(fac.from_key, "light_path")
        self.assertEqual(fac.from_socket, "Is Shadow Ray")
        self.assertIsNone(graph.gradient_type)


class CatcherMessageTests(unittest.TestCase):
    def test_shared_copy_is_sentence_plus_next_step(self) -> None:
        self.assertEqual(messages.NO_CATCHER_API, catcher.NO_CATCHER_API)
        self.assertEqual(messages.NO_STUDIO, catcher.NO_STUDIO)
        self.assertEqual(messages.NO_PRODUCT_FOR_CATCHER, catcher.NO_PRODUCT_FOR_CATCHER)
        self.assertEqual(messages.UNKNOWN_BACKDROP, catcher.UNKNOWN_BACKDROP)
        self.assertIn(" — ", catcher.NO_CATCHER_API)
        self.assertIn("Build Studio", catcher.NO_STUDIO)
        self.assertIn("Import Product", catcher.NO_PRODUCT_FOR_CATCHER)
        self.assertEqual(messages.report_type(catcher.NO_CATCHER_API), "WARNING")
        self.assertEqual(messages.report_type(catcher.NO_STUDIO), "WARNING")
        self.assertEqual(messages.report_type(catcher.NO_PRODUCT_FOR_CATCHER), "WARNING")
        self.assertEqual(messages.report_type(catcher.UNKNOWN_BACKDROP), "WARNING")
        self.assertEqual(messages.report_type(catcher.CATCHER_FAILED), "ERROR")


class CatcherWiringTests(unittest.TestCase):
    def test_apply_writes_catcher_and_contact_rna(self) -> None:
        apply = _read("behold/studio/catcher_apply.py")
        spec = _read("behold/studio/catcher.py")
        setup = _read("behold/studio/setup.py")
        self.assertIn("is_shadow_catcher", apply)
        self.assertIn("use_contact_shadow", apply)
        self.assertIn("contact_shadow_distance", apply)
        self.assertIn("surface_render_method", apply)
        self.assertIn("blend_method", apply)
        self.assertIn("BEHOLD_ContactShadow", spec)
        self.assertIn("BEHOLD_ShadowCatcher", spec)
        self.assertIn("Is Shadow Ray", spec)
        self.assertIn("QUADRATIC_SPHERE", spec)
        self.assertIn("apply_ground_contact", setup)
        self.assertNotIn("studio_backdrop != \"CYCLORAMA\"", setup)
        self.assertIn("on_catcher_update", apply)

    def test_operators_and_properties(self) -> None:
        ops = _read("behold/studio/operators.py")
        props = _read("behold/properties.py")
        ids = _read("behold/studio/camera_ids.py")
        presets = _read("behold/materials/presets.py")
        self.assertIn('bl_idname = "behold.apply_catcher"', ops)
        self.assertIn("catcher_apply.apply_ground_contact", ops)
        self.assertIn("include_shadow_catcher", props)
        self.assertIn("on_catcher_update", props)
        self.assertIn("_ContactShadow", ids)
        self.assertIn("BEHOLD_ContactShadow", presets)

    def test_studio_toggle_stays_on_build_row(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        first = _func_source(source, tree, "draw_studio_first_ship")
        parked = _func_source(source, tree, "draw_studio_parked")
        self.assertIn("include_shadow_catcher", first)
        self.assertIn('text="Catcher"', first)
        self.assertIn('text="Build"', first)
        self.assertLess(first.index('text="Build"'), first.index("include_shadow_catcher"))
        self.assertNotIn("studio_margin", first)
        self.assertNotIn("key_power", first)
        self.assertNotIn("BEHOLD_PT_catcher", source)
        self.assertNotIn("gobo", first.lower())
        self.assertIn("include_shadow_catcher", parked)
        self.assertIn("behold.apply_catcher", parked)
        self.assertNotIn("behold.apply_catcher", first)
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
