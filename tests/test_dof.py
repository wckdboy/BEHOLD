# SPDX-License-Identifier: GPL-3.0-or-later
"""Product DoF / focus pick helpers + Cameras wiring (no Blender)."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module

dof = load_addon_module("behold/studio/dof.py", "behold.studio.dof")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class FstopAndFocusMathTests(unittest.TestCase):
    def test_product_default_is_f_5_6(self) -> None:
        self.assertEqual(dof.DEFAULT_FSTOP, 5.6)
        self.assertEqual(dof.BLENDER_DEFAULT_FSTOP, 2.8)
        self.assertEqual(dof.format_fstop(5.6), "5.6")
        self.assertEqual(dof.format_fstop(8.0), "8")
        self.assertEqual(dof.format_fstop(2.8), "2.8")
        self.assertEqual(dof.clamp_fstop(0.1), 1.0)
        self.assertEqual(dof.clamp_fstop(64.0), 32.0)
        self.assertTrue(dof.is_factory_fstop(2.8))
        self.assertFalse(dof.is_factory_fstop(5.6))
        self.assertEqual(
            dof.resolve_product_fstop(2.8, enabling=True),
            5.6,
        )
        self.assertEqual(
            dof.resolve_product_fstop(2.8, enabling=True, requested=4.0),
            4.0,
        )
        self.assertEqual(dof.resolve_product_fstop(4.0, enabling=True), 4.0)
        self.assertEqual(dof.resolve_product_fstop(2.8, enabling=False), 2.8)

    def test_aabb_center_and_facing_surface(self) -> None:
        mins = (0.0, 0.0, 0.0)
        maxs = (2.0, 4.0, 6.0)
        self.assertEqual(dof.aabb_center(mins, maxs), (1.0, 2.0, 3.0))
        camera = (10.0, 2.0, 3.0)
        self.assertEqual(dof.aabb_nearest_point(mins, maxs, camera), (2.0, 2.0, 3.0))
        inside = (1.0, 2.0, 3.0)
        self.assertEqual(dof.aabb_nearest_point(mins, maxs, inside), inside)
        self.assertAlmostEqual(dof.focus_distance((0.0, 0.0, 0.0), (3.0, 4.0, 0.0)), 5.0)
        self.assertGreaterEqual(dof.focus_distance((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)), dof.FOCUS_MIN)
        self.assertEqual(dof.product_focus_point(mins, maxs), (1.0, 2.0, 3.0))
        self.assertEqual(
            dof.selected_focus_point(mins, maxs, camera),
            (2.0, 2.0, 3.0),
        )
        self.assertEqual(
            dof.selected_focus_point(mins, maxs, inside),
            (1.0, 2.0, 3.0),
        )


class DofPlanTests(unittest.TestCase):
    def test_missing_api_is_52_copy(self) -> None:
        self.assertIsNone(
            dof.capability_problem(
                has_dof=True,
                has_use_dof=True,
                has_fstop=True,
                has_focus_distance=True,
            )
        )
        self.assertEqual(
            dof.capability_problem(
                has_dof=False,
                has_use_dof=False,
                has_fstop=False,
                has_focus_distance=False,
            ),
            dof.NO_DOF_API,
        )
        self.assertIn("5.2", dof.NO_DOF_API)
        self.assertIn("DoF", dof.NO_DOF_API)

    def test_focus_on_product_uses_center(self) -> None:
        camera = (5.0, -5.0, 5.0)
        bounds = ((-1.0, -1.0, 0.0), (1.0, 1.0, 2.0))
        plan = dof.plan_dof(
            use_dof=True,
            fstop=5.6,
            current_fstop=2.8,
            current_focus_distance=10.0,
            camera=camera,
            product_bounds=bounds,
            selected_bounds=None,
            focus="PRODUCT",
            enabling=True,
        )
        self.assertIsInstance(plan, dof.DofPlan)
        self.assertTrue(plan.use_dof)
        self.assertEqual(plan.fstop, 5.6)
        self.assertEqual(plan.target, "PRODUCT")
        self.assertTrue(plan.autofocus)
        self.assertTrue(plan.clear_focus_object)
        expected = dof.focus_distance(camera, (0.0, 0.0, 1.0))
        self.assertAlmostEqual(plan.focus_distance, expected)
        self.assertIn("Focus on product", dof.apply_message(plan))
        self.assertIn("f/5.6", dof.apply_message(plan))

    def test_focus_on_selected_uses_facing_surface(self) -> None:
        camera = (10.0, 0.0, 0.5)
        selected = ((0.0, -1.0, 0.0), (2.0, 1.0, 1.0))
        plan = dof.plan_dof(
            use_dof=True,
            fstop=8.0,
            current_fstop=2.8,
            current_focus_distance=10.0,
            camera=camera,
            product_bounds=None,
            selected_bounds=selected,
            focus="SELECTED",
        )
        self.assertIsInstance(plan, dof.DofPlan)
        self.assertEqual(plan.target, "SELECTED")
        expected = dof.focus_distance(camera, (2.0, 0.0, 0.5))
        self.assertAlmostEqual(plan.focus_distance, expected)
        self.assertIn("Focus on selected", dof.apply_message(plan))
        self.assertIn("f/8", dof.apply_message(plan))

    def test_enable_autofocuses_factory_distance(self) -> None:
        camera = (4.0, -4.0, 2.0)
        bounds = ((-0.5, -0.5, 0.0), (0.5, 0.5, 1.0))
        plan = dof.plan_dof(
            use_dof=True,
            fstop=None,
            current_fstop=2.8,
            current_focus_distance=10.0,
            camera=camera,
            product_bounds=bounds,
            selected_bounds=None,
            focus="KEEP",
            enabling=True,
        )
        self.assertIsInstance(plan, dof.DofPlan)
        self.assertEqual(plan.fstop, 5.6)
        self.assertEqual(plan.target, "PRODUCT")
        self.assertTrue(plan.autofocus)

    def test_keep_does_not_steal_custom_distance(self) -> None:
        plan = dof.plan_dof(
            use_dof=True,
            fstop=4.0,
            current_fstop=4.0,
            current_focus_distance=1.25,
            camera=(3.0, -3.0, 1.0),
            product_bounds=((-1.0, -1.0, 0.0), (1.0, 1.0, 2.0)),
            selected_bounds=None,
            focus="KEEP",
            enabling=False,
        )
        self.assertIsInstance(plan, dof.DofPlan)
        self.assertEqual(plan.target, "KEEP")
        self.assertAlmostEqual(plan.focus_distance, 1.25)
        self.assertFalse(plan.autofocus)
        self.assertIn("DoF on", dof.apply_message(plan))

    def test_disable_message(self) -> None:
        plan = dof.plan_dof(
            use_dof=False,
            fstop=5.6,
            current_fstop=5.6,
            current_focus_distance=2.0,
            camera=(0.0, -2.0, 1.0),
            product_bounds=None,
            selected_bounds=None,
            focus="KEEP",
        )
        self.assertIsInstance(plan, dof.DofPlan)
        self.assertFalse(plan.use_dof)
        self.assertEqual(dof.apply_message(plan), dof.DOF_DISABLED)

    def test_missing_product_or_selection(self) -> None:
        self.assertEqual(
            dof.plan_dof(
                use_dof=True,
                fstop=5.6,
                current_fstop=5.6,
                current_focus_distance=10.0,
                camera=(0.0, -2.0, 1.0),
                product_bounds=None,
                selected_bounds=None,
                focus="PRODUCT",
            ),
            dof.FOCUS_NO_PRODUCT,
        )
        self.assertEqual(
            dof.plan_dof(
                use_dof=True,
                fstop=5.6,
                current_fstop=5.6,
                current_focus_distance=10.0,
                camera=(0.0, -2.0, 1.0),
                product_bounds=((-1.0, -1.0, 0.0), (1.0, 1.0, 1.0)),
                selected_bounds=None,
                focus="SELECTED",
            ),
            dof.FOCUS_NO_SELECTION,
        )
        self.assertEqual(
            dof.plan_dof(
                use_dof=True,
                fstop=5.6,
                current_fstop=5.6,
                current_focus_distance=10.0,
                camera=(0.0, -2.0, 1.0),
                product_bounds=None,
                selected_bounds=None,
                focus="gobo",
            ),
            dof.UNKNOWN_FOCUS,
        )
        self.assertEqual(dof.normalize_focus(""), "KEEP")
        self.assertEqual(dof.normalize_focus("selected"), "SELECTED")
        self.assertTrue(dof.is_focus("PRODUCT"))
        self.assertFalse(dof.is_focus("SURFACE"))


class DofMessageTests(unittest.TestCase):
    def test_shared_copy_is_sentence_plus_next_step(self) -> None:
        self.assertEqual(messages.NO_DOF_API, dof.NO_DOF_API)
        self.assertEqual(messages.FOCUS_NO_PRODUCT, dof.FOCUS_NO_PRODUCT)
        self.assertEqual(messages.FOCUS_NO_SELECTION, dof.FOCUS_NO_SELECTION)
        self.assertIn(" — ", dof.NO_DOF_API)
        self.assertIn("Import Product", dof.FOCUS_NO_PRODUCT)
        self.assertIn("surface", dof.FOCUS_NO_SELECTION)
        self.assertEqual(messages.report_type(dof.NO_DOF_API), "WARNING")
        self.assertEqual(messages.report_type(dof.FOCUS_NO_PRODUCT), "WARNING")
        self.assertEqual(messages.report_type(dof.FOCUS_NO_SELECTION), "WARNING")
        self.assertEqual(messages.report_type(dof.UNKNOWN_FOCUS), "WARNING")
        self.assertEqual(messages.report_type(dof.DOF_FAILED), "ERROR")


class DofWiringTests(unittest.TestCase):
    def test_apply_writes_camera_dof_rna(self) -> None:
        apply = _read("behold/studio/dof_apply.py")
        spec = _read("behold/studio/dof.py")
        self.assertIn("use_dof", apply)
        self.assertIn("aperture_fstop", apply)
        self.assertIn("focus_distance", apply)
        self.assertIn("focus_object", apply)
        self.assertIn("on_dof_update", apply)
        self.assertIn("product_focus_meshes", apply)
        self.assertIn("selected_focus_meshes", apply)
        self.assertIn("is_studio_mesh_name", apply)
        self.assertIn("Camera.dof", spec)
        self.assertIn("aperture_fstop", spec)
        cameras = _read("behold/studio/cameras.py")
        self.assertIn("dof_lib.DEFAULT_FSTOP", cameras)
        self.assertIn("use_dof = False", cameras)

    def test_operators_and_properties(self) -> None:
        ops = _read("behold/shoot/operators.py")
        props = _read("behold/properties.py")
        self.assertIn('bl_idname = "behold.apply_camera_dof"', ops)
        self.assertIn('bl_idname = "behold.focus_product"', ops)
        self.assertIn('bl_idname = "behold.focus_selected"', ops)
        self.assertIn('focus="PRODUCT"', ops)
        self.assertIn('focus="SELECTED"', ops)
        self.assertIn("dof_apply.apply_dof", ops)
        self.assertIn("dof_enabled", props)
        self.assertIn("dof_fstop", props)
        self.assertIn("on_dof_update", props)
        self.assertIn("DOF_DEFAULT_FSTOP", props)

    def test_cameras_card_stays_off_empty_state(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        section = _func_source(source, tree, "draw_cameras_section")
        card = _func_source(source, tree, "draw_cameras_dof")
        parked = _func_source(source, tree, "draw_shoot_parked")
        shoot = _func_source(source, tree, "draw_shoot_first_ship")
        self.assertIn("EMPTY_CAMERAS", section)
        self.assertIn("draw_empty_card", section)
        self.assertIn("draw_cameras_dof", section)
        empty_idx = section.index("draw_empty_card")
        dof_idx = section.index("draw_cameras_dof")
        self.assertLess(empty_idx, dof_idx)
        self.assertIn("dof_enabled", card)
        self.assertIn("dof_fstop", card)
        self.assertIn('text="DoF"', card)
        self.assertIn('text="f-stop"', card)
        self.assertIn("behold.focus_product", card)
        self.assertIn("behold.focus_selected", card)
        self.assertIn('text="Focus on product"', card)
        self.assertIn('text="Focus on selected"', card)
        self.assertNotIn("behold.apply_camera_dof", card)
        self.assertNotIn("gobo", card.lower())
        self.assertNotIn("IES", card)
        self.assertNotIn("BEHOLD_PT_dof", source)
        self.assertIn("behold.focus_product", parked)
        self.assertIn("behold.apply_camera_dof", parked)
        self.assertNotIn("behold.focus_product", shoot)
        self.assertNotIn("dof_enabled", shoot)


if __name__ == "__main__":
    unittest.main()
