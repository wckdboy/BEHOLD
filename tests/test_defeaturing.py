# SPDX-License-Identifier: GPL-3.0-or-later
"""Defeaturing lite — fillet / chamfer / hole suppress (no Blender)."""

from __future__ import annotations

import ast
import math
import unittest

from tests.support import ROOT, UNIT_CUBE_STEP, load_addon_module, load_module

try:
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeCylinder
    from OCP.gp import gp_Ax2, gp_Dir, gp_Pnt

    _OCP_PRIMS_ERROR: BaseException | None = None
except Exception as exc:  # noqa: BLE001
    BRepAlgoAPI_Cut = None  # type: ignore[assignment]
    BRepPrimAPI_MakeBox = None  # type: ignore[assignment]
    BRepPrimAPI_MakeCylinder = None  # type: ignore[assignment]
    gp_Ax2 = None  # type: ignore[assignment]
    gp_Dir = None  # type: ignore[assignment]
    gp_Pnt = None  # type: ignore[assignment]
    _OCP_PRIMS_ERROR = exc

defeaturing = load_addon_module(
    "behold/cad/defeaturing.py", "behold.cad.defeaturing"
)
ocp_defeature = load_addon_module(
    "behold/cad/ocp_defeature.py", "behold.cad.ocp_defeature"
)
ocp_core = load_module("behold/cad/ocp_core.py", "behold_ocp_core_defeature")
stepper_api = load_module("behold/cad/stepper_api.py", "behold_stepper_api_df")
regenerate = load_addon_module("behold/cad/regenerate.py", "behold.cad.regenerate")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class PlanAndUnitsTests(unittest.TestCase):
    def test_defaults_are_artist_millimetres(self) -> None:
        self.assertEqual(defeaturing.DEFAULT_BLEND_MM, 2.0)
        self.assertEqual(defeaturing.DEFAULT_HOLE_MM, 3.0)
        plan = defeaturing.plan_defeaturing(
            fillets=True,
            chamfers=False,
            holes=True,
            blend_mm=2.0,
            hole_mm=3.0,
        )
        self.assertTrue(plan.active)
        self.assertTrue(plan.fillets)
        self.assertFalse(plan.chamfers)
        self.assertTrue(plan.holes)
        off = defeaturing.plan_defeaturing(
            fillets=False,
            chamfers=False,
            holes=False,
            blend_mm=2.0,
            hole_mm=3.0,
        )
        self.assertFalse(off.active)

    def test_size_clamps(self) -> None:
        huge = defeaturing.plan_defeaturing(
            fillets=True,
            chamfers=True,
            holes=True,
            blend_mm=999.0,
            hole_mm=0.0,
        )
        self.assertEqual(huge.blend_mm, defeaturing.MAX_SIZE_MM)
        self.assertEqual(huge.hole_mm, defeaturing.MIN_SIZE_MM)

    def test_unit_cube_step_is_millimetres(self) -> None:
        text = UNIT_CUBE_STEP.read_text(encoding="utf-8")
        self.assertAlmostEqual(
            defeaturing.meters_per_file_unit_from_text(text) or 0.0,
            0.001,
        )
        self.assertAlmostEqual(defeaturing.meters_per_file_unit(str(UNIT_CUBE_STEP)), 0.001)
        self.assertAlmostEqual(defeaturing.mm_to_file_units(2.0, 0.001), 2.0)
        self.assertAlmostEqual(defeaturing.mm_to_file_units(2.0, 1.0), 0.002)
        self.assertAlmostEqual(
            defeaturing.hole_radius_file_units(
                defeaturing.plan_defeaturing(
                    fillets=False,
                    chamfers=False,
                    holes=True,
                    blend_mm=2.0,
                    hole_mm=3.0,
                ),
                0.001,
            ),
            1.5,
        )

    def test_metre_header_parses(self) -> None:
        header = "SI_UNIT($,.METRE.)"
        self.assertAlmostEqual(
            defeaturing.meters_per_file_unit_from_text(header) or 0.0,
            1.0,
        )
        self.assertIsNone(defeaturing.meters_per_file_unit_from_text("no units here"))


class FaceSelectionTests(unittest.TestCase):
    def test_small_fillet_cylinder_not_a_hole(self) -> None:
        plan = defeaturing.plan_defeaturing(
            fillets=True,
            chamfers=False,
            holes=True,
            blend_mm=2.0,
            hole_mm=3.0,
        )
        fillet = defeaturing.FaceHint(
            kind="cylinder",
            radius=1.0,
            u_span=math.pi / 2,
            v_span=20.0,
            closed_u=False,
        )
        hole = defeaturing.FaceHint(
            kind="cylinder",
            radius=1.0,
            u_span=2 * math.pi,
            v_span=10.0,
            closed_u=True,
        )
        torus = defeaturing.FaceHint(kind="torus", radius=0.8, u_span=math.pi, v_span=math.pi)
        picks = defeaturing.select_feature_faces(
            (fillet, hole, torus),
            plan,
            meters_per_unit=0.001,
            bbox_diag=40.0,
        )
        roles = {pick.index: pick.role for pick in picks}
        self.assertEqual(roles[0], "fillet")
        self.assertEqual(roles[1], "hole")
        self.assertEqual(roles[2], "fillet")

    def test_chamfer_strip_not_a_side_face(self) -> None:
        plan = defeaturing.plan_defeaturing(
            fillets=False,
            chamfers=True,
            holes=False,
            blend_mm=2.0,
            hole_mm=3.0,
        )
        strip = defeaturing.FaceHint(
            kind="plane",
            width=1.5,
            u_span=1.5,
            v_span=30.0,
            area=45.0,
        )
        side = defeaturing.FaceHint(
            kind="plane",
            width=20.0,
            u_span=20.0,
            v_span=20.0,
            area=400.0,
        )
        square = defeaturing.FaceHint(
            kind="plane",
            width=1.5,
            u_span=1.5,
            v_span=1.5,
            area=2.25,
        )
        picks = defeaturing.select_feature_faces(
            (strip, side, square),
            plan,
            meters_per_unit=0.001,
            bbox_diag=40.0,
        )
        self.assertEqual([pick.index for pick in picks], [0])
        self.assertEqual(picks[0].role, "chamfer")

    def test_inactive_plan_selects_nothing(self) -> None:
        plan = defeaturing.plan_defeaturing(
            fillets=False,
            chamfers=False,
            holes=False,
            blend_mm=2.0,
            hole_mm=3.0,
        )
        hint = defeaturing.FaceHint(kind="cylinder", radius=0.5, closed_u=True, u_span=6.3)
        self.assertEqual(
            defeaturing.select_feature_faces(
                (hint,),
                plan,
                meters_per_unit=0.001,
                bbox_diag=10.0,
            ),
            (),
        )

    def test_large_fillet_is_kept(self) -> None:
        plan = defeaturing.plan_defeaturing(
            fillets=True,
            chamfers=False,
            holes=False,
            blend_mm=2.0,
            hole_mm=3.0,
        )
        big = defeaturing.FaceHint(
            kind="cylinder",
            radius=8.0,
            u_span=math.pi / 2,
            closed_u=False,
        )
        self.assertEqual(
            defeaturing.select_feature_faces(
                (big,),
                plan,
                meters_per_unit=0.001,
                bbox_diag=40.0,
            ),
            (),
        )


class BlockerAndCopyTests(unittest.TestCase):
    def test_stepper_has_no_defeaturing_rna(self) -> None:
        self.assertFalse(defeaturing.stepper_supports_defeaturing())
        self.assertEqual(stepper_api.STEPPER_DEFEATURE_KWARGS, frozenset())
        lowered = {name.lower() for name in stepper_api.STEPPER_OCC_OPTIONAL_KWARGS}
        for banned in ("fillet", "chamfer", "hole", "defeature", "cleanup"):
            self.assertTrue(all(banned not in name for name in lowered), banned)

    def test_blockers_are_sentence_plus_next_step(self) -> None:
        plan = defeaturing.plan_defeaturing(
            fillets=True,
            chamfers=True,
            holes=True,
            blend_mm=2.0,
            hole_mm=3.0,
        )
        self.assertIsNone(
            defeaturing.cleanup_blockers(
                plan,
                ocp_available=True,
                has_defeaturing=True,
                has_remove_wires=True,
            )
        )
        needs = defeaturing.cleanup_blockers(
            plan,
            ocp_available=False,
            has_defeaturing=False,
            has_remove_wires=False,
        )
        self.assertEqual(needs, defeaturing.DEFEATURE_NEEDS_OCP)
        self.assertIn("OCP", needs or "")
        self.assertIn("STEPper NEXT tessellates only", needs or "")
        self.assertIn("Apply cleanup", needs or "")
        no_fillet = defeaturing.cleanup_blockers(
            plan,
            ocp_available=True,
            has_defeaturing=False,
            has_remove_wires=True,
        )
        self.assertEqual(no_fillet, defeaturing.DEFEATURE_NO_FILLET_API)
        holes_only = defeaturing.plan_defeaturing(
            fillets=False,
            chamfers=False,
            holes=True,
            blend_mm=2.0,
            hole_mm=3.0,
        )
        self.assertIsNone(
            defeaturing.cleanup_blockers(
                holes_only,
                ocp_available=True,
                has_defeaturing=False,
                has_remove_wires=True,
            )
        )
        self.assertEqual(
            defeaturing.cleanup_blockers(
                holes_only,
                ocp_available=True,
                has_defeaturing=False,
                has_remove_wires=False,
            ),
            defeaturing.DEFEATURE_NO_HOLE_API,
        )

    def test_warning_vs_error(self) -> None:
        self.assertEqual(messages.DEFEATURE_NEEDS_OCP, defeaturing.DEFEATURE_NEEDS_OCP)
        self.assertEqual(messages.report_type(messages.DEFEATURE_NEEDS_OCP), "WARNING")
        self.assertEqual(messages.report_type(messages.DEFEATURE_NO_FILLET_API), "WARNING")
        self.assertEqual(messages.report_type(messages.DEFEATURE_NO_HOLE_API), "WARNING")
        self.assertEqual(messages.report_type(messages.DEFEATURE_NO_SOLID), "WARNING")
        self.assertEqual(messages.report_type(messages.DEFEATURE_FAILED), "ERROR")

    def test_captions(self) -> None:
        plan = defeaturing.plan_defeaturing(
            fillets=True,
            chamfers=True,
            holes=True,
            blend_mm=2.0,
            hole_mm=3.0,
        )
        caption = defeaturing.cleanup_caption(plan)
        self.assertIn("fillets ≤ 2 mm", caption)
        self.assertIn("chamfers ≤ 2 mm", caption)
        self.assertIn("holes Ø ≤ 3 mm", caption)
        applied = defeaturing.cleanup_applied_caption(
            plan,
            defeaturing.CleanupStats(fillets=2, chamfers=1, holes=0, wires=1),
        )
        self.assertIn("removed 2 fillets", applied)
        self.assertIn("1 chamfer", applied)
        self.assertIn("1 hole", applied)
        none = defeaturing.cleanup_applied_caption(plan, defeaturing.CleanupStats())
        self.assertIn("none matched", none)
        self.assertEqual(
            defeaturing.cleanup_caption(
                defeaturing.plan_defeaturing(
                    fillets=False,
                    chamfers=False,
                    holes=False,
                    blend_mm=2.0,
                    hole_mm=3.0,
                )
            ),
            "",
        )

    def test_regenerate_message_includes_cleanup(self) -> None:
        text = regenerate.regenerated_message(
            "/tmp/housing.step",
            backend="OCP",
            quality="FINE",
            object_count=1,
            cleanup="fillets ≤ 2 mm; removed 3 fillets",
        )
        self.assertIn("housing.step", text)
        self.assertIn("OCP", text)
        self.assertIn("Fine", text)
        self.assertIn("fillets ≤ 2 mm", text)
        plain = regenerate.regenerated_message(
            "/tmp/housing.step",
            backend="STEPPER",
            quality="BALANCED",
            object_count=1,
        )
        self.assertIn("STEPper NEXT", plain)
        self.assertNotIn("fillet", plain)


class WiringTests(unittest.TestCase):
    def test_operators_force_ocp_when_cleanup_on(self) -> None:
        ops = _read("behold/cad/operators.py")
        apply_src = _read("behold/cad/regenerate_apply.py")
        import_src = _read("behold/cad/ocp_import.py")
        props = _read("behold/properties.py")
        self.assertIn("scene_cleanup_plan", ops)
        self.assertIn("_cleanup_blockers", ops)
        self.assertIn("cad_cleanup_fillets", ops)
        self.assertIn("cleanup.active", ops)
        self.assertIn('backend = "OCP"', ops)
        self.assertIn("apply_defeaturing", apply_src)
        self.assertIn("cleanup=cleanup", apply_src)
        self.assertIn("apply_defeaturing", import_src)
        self.assertIn("cad_cleanup_fillets", props)
        self.assertIn("cad_cleanup_chamfers", props)
        self.assertIn("cad_cleanup_holes", props)
        self.assertIn("cad_blend_mm", props)
        self.assertIn("cad_hole_mm", props)
        self.assertNotIn("fillet_suppress", ops)
        self.assertNotIn("occ_defeature", ops)

    def test_import_panel_cleanup_card(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        body = _func_source(source, tree, "draw_import_first_ship")
        self.assertIn("draw_import_tessellation", body)
        self.assertIn("draw_import_cleanup", body)
        self.assertLess(
            body.index("draw_import_tessellation"),
            body.index("draw_import_cleanup"),
        )
        cleanup = _func_source(source, tree, "draw_import_cleanup")
        self.assertIn("cad_cleanup_fillets", cleanup)
        self.assertIn("cad_cleanup_chamfers", cleanup)
        self.assertIn("cad_cleanup_holes", cleanup)
        self.assertIn("cad_blend_mm", cleanup)
        self.assertIn("cad_hole_mm", cleanup)
        self.assertIn('text="Cleanup"', cleanup)
        self.assertNotIn("BEHOLD_PT_cleanup", source)
        self.assertNotIn("BEHOLD_PT_defeaturing", source)
        tess = _func_source(source, tree, "draw_import_tessellation")
        self.assertIn("behold.regenerate_cad", tess)
        cleanup = _func_source(source, tree, "draw_import_cleanup")
        self.assertIn("behold.cleanup_cad", cleanup)
        self.assertNotIn("behold.regenerate_cad", cleanup)
        parked = _func_source(source, tree, "draw_import_parked")
        self.assertIn("cad_cleanup_fillets", parked)
        self.assertIn("cad_blend_mm", parked)
        self.assertIn("behold.cleanup_cad", parked)
        lights = _func_source(source, tree, "draw_lights_section")
        self.assertNotIn("cad_cleanup_fillets", lights)
        self.assertIn("light_ies_filepath", _func_source(source, tree, "draw_lights_ies"))


class OcpDefeaturingTests(unittest.TestCase):
    def test_probe_without_bindings(self) -> None:
        probe = ocp_defeature.probe_defeaturing_api()
        self.assertIn("ocp", probe)
        self.assertIn("defeaturing", probe)
        self.assertIn("remove_wires", probe)
        self.assertEqual(probe["ocp"], ocp_core.ocp_available())

    def test_unit_cube_selects_no_features_when_ocp_present(self) -> None:
        if not ocp_core.ocp_available():
            self.skipTest("OCP unavailable — classification still runs without bindings")
        shape, error = ocp_core.read_cad_shape(str(UNIT_CUBE_STEP))
        self.assertIsNone(error, error)
        plan = defeaturing.plan_defeaturing(
            fillets=True,
            chamfers=True,
            holes=True,
            blend_mm=2.0,
            hole_mm=3.0,
        )
        applied = ocp_defeature.apply_defeaturing(
            shape,
            plan,
            filepath=str(UNIT_CUBE_STEP),
        )
        self.assertNotIsInstance(applied, str, applied)
        assert not isinstance(applied, str)
        _shape, stats = applied
        self.assertEqual(stats.fillets, 0)
        self.assertEqual(stats.chamfers, 0)
        self.assertEqual(stats.holes, 0)

    def test_box_with_hole_suppresses_when_ocp_present(self) -> None:
        if not ocp_core.ocp_available() or _OCP_PRIMS_ERROR is not None:
            self.skipTest("OCP unavailable — hole suppress needs OpenCASCADE")
        if (
            BRepPrimAPI_MakeBox is None
            or BRepPrimAPI_MakeCylinder is None
            or BRepAlgoAPI_Cut is None
            or gp_Ax2 is None
            or gp_Pnt is None
            or gp_Dir is None
        ):
            self.skipTest("OCP primitives unavailable")
        box = BRepPrimAPI_MakeBox(40.0, 40.0, 10.0).Shape()
        axis = gp_Ax2(gp_Pnt(20.0, 20.0, -1.0), gp_Dir(0.0, 0.0, 1.0))
        cyl = BRepPrimAPI_MakeCylinder(axis, 1.5, 12.0).Shape()
        cut = BRepAlgoAPI_Cut(box, cyl).Shape()
        plan = defeaturing.plan_defeaturing(
            fillets=False,
            chamfers=False,
            holes=True,
            blend_mm=2.0,
            hole_mm=4.0,
        )
        applied = ocp_defeature.apply_defeaturing(cut, plan, filepath="")
        faces = ocp_defeature._iter_faces(cut)
        hints = tuple(ocp_defeature.face_hint(face) for face in faces)
        picks = defeaturing.select_feature_faces(
            hints,
            plan,
            meters_per_unit=0.001,
            bbox_diag=60.0,
        )
        self.assertTrue(
            any(pick.role == "hole" for pick in picks),
            "expected a cylindrical hole face under 4 mm Ø",
        )
        if isinstance(applied, str):
            return
        _shape, stats = applied
        self.assertGreater(stats.holes + stats.wires, 0)


if __name__ == "__main__":
    unittest.main()
