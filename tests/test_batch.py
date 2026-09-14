# SPDX-License-Identifier: GPL-3.0-or-later
"""Catalog batch export planner and Shoot wiring — no Blender import."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module

batch = load_addon_module("behold/shoot/batch.py", "behold.shoot.batch")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class BatchPlanTests(unittest.TestCase):
    def test_standard_angles_are_front_three_quarter_top(self) -> None:
        slugs = [item[0] for item in batch.STANDARD_ANGLES]
        self.assertEqual(slugs, ["front", "three_quarter", "top"])
        jobs = batch.standard_angle_jobs()
        self.assertEqual([job.slug for job in jobs], slugs)
        self.assertEqual(jobs[1].label, "¾")
        self.assertTrue(all(job.kind == "angle" for job in jobs))
        self.assertEqual(jobs[0].filename, "front.png")

    def test_angle_offsets_match_historic_batch_framing(self) -> None:
        extent = 2.0
        distance = extent * 2.4
        front = batch.angle_world_offset("front", extent)
        three = batch.angle_world_offset("three_quarter", extent)
        top = batch.angle_world_offset("top", extent)
        self.assertAlmostEqual(front[0], 0.0)
        self.assertAlmostEqual(front[1], -distance)
        self.assertAlmostEqual(front[2], extent * 0.35)
        self.assertAlmostEqual(three[0], distance * 0.75)
        self.assertAlmostEqual(three[1], -distance * 0.85)
        self.assertAlmostEqual(three[2], extent * 0.45)
        self.assertAlmostEqual(top[0], 0.0)
        self.assertAlmostEqual(top[1], -distance * 0.15)
        self.assertAlmostEqual(top[2], distance)
        with self.assertRaises(RuntimeError):
            batch.angle_world_offset("hero", 1.0)

    def test_extent_clamps_tiny_and_uses_longest_side(self) -> None:
        self.assertEqual(batch.product_extent((0.0, 0.0, 0.0), (0.0, 0.0, 0.0)), 0.1)
        self.assertEqual(batch.product_extent((0.0, 0.0, 0.0), (4.0, 1.0, 2.0)), 4.0)

    def test_tokens_fill_angle_camera_quality(self) -> None:
        filled = batch.fill_output_tokens(
            "//behold_out/{quality}/{camera}/{angle}/",
            angle="front",
            camera="BEHOLD_Camera",
            quality="HERO",
        )
        self.assertEqual(filled, "//behold_out/hero/BEHOLD_Camera/front/")
        self.assertEqual(
            batch.fill_output_tokens("", angle="", camera="", quality=""),
            "//behold_out/",
        )
        self.assertEqual(
            set(batch.OUTPUT_TOKENS),
            {"{angle}", "{camera}", "{quality}"},
        )
        self.assertIn("{angle}", batch.TOKEN_HINT)
        self.assertIn("{camera}", batch.TOKEN_HINT)
        self.assertIn("{quality}", batch.TOKEN_HINT)

    def test_slugify_shot_names_for_angle_token(self) -> None:
        self.assertEqual(batch.slugify("Hero chrome"), "Hero_chrome")
        self.assertEqual(batch.slugify("pack/shot"), "pack_shot")
        self.assertEqual(batch.slugify("  "), "shot")
        jobs = batch.shot_jobs(["Hero chrome", "", "Pack shot"])
        self.assertEqual([job.slug for job in jobs], ["Hero_chrome", "Pack_shot"])
        self.assertEqual(jobs[0].kind, "shot")
        self.assertEqual(jobs[0].shot_name, "Hero chrome")
        self.assertEqual(jobs[0].filename, "Hero_chrome.png")

    def test_plan_requires_a_set_and_prerequisites(self) -> None:
        none, err = batch.plan_batch(
            include_angles=False,
            include_shots=False,
            shot_names=["Hero"],
            has_product=True,
            has_camera=True,
        )
        self.assertIsNone(none)
        self.assertEqual(err, batch.BATCH_NOTHING)

        no_mesh, mesh_err = batch.plan_batch(
            include_angles=True,
            include_shots=False,
            has_product=False,
            has_camera=True,
        )
        self.assertIsNone(no_mesh)
        self.assertEqual(mesh_err, batch.BATCH_NO_MESH)

        no_cam, cam_err = batch.plan_batch(
            include_angles=True,
            include_shots=False,
            has_product=True,
            has_camera=False,
        )
        self.assertIsNone(no_cam)
        self.assertEqual(cam_err, batch.BATCH_NO_CAMERA)

        no_shots, shot_err = batch.plan_batch(
            include_angles=False,
            include_shots=True,
            shot_names=[],
            has_product=True,
            has_camera=True,
        )
        self.assertIsNone(no_shots)
        self.assertEqual(shot_err, batch.BATCH_NO_SHOTS)

    def test_plan_angles_then_shots_and_shots_only_skips_camera(self) -> None:
        plan, error = batch.plan_batch(
            include_angles=True,
            include_shots=True,
            shot_names=["Hero chrome", "Pack"],
            has_product=True,
            has_camera=True,
        )
        self.assertIsNone(error)
        assert plan is not None
        self.assertEqual(plan.total, 5)
        kinds = [job.kind for job in plan.jobs]
        self.assertEqual(kinds, ["angle", "angle", "angle", "shot", "shot"])
        self.assertEqual(plan.jobs[0].slug, "front")
        self.assertEqual(plan.jobs[3].shot_name, "Hero chrome")

        shots_only, shots_err = batch.plan_batch(
            include_angles=False,
            include_shots=True,
            shot_names=["Hero"],
            has_product=False,
            has_camera=False,
        )
        self.assertIsNone(shots_err)
        assert shots_only is not None
        self.assertEqual(len(shots_only.jobs), 1)
        self.assertEqual(shots_only.jobs[0].kind, "shot")

    def test_progress_and_done_copy(self) -> None:
        job = batch.BatchJob(kind="angle", slug="front", label="front")
        self.assertEqual(batch.progress_message(1, 3, job), "Batch 1/3: front")
        self.assertEqual(
            batch.done_message(3, 3, last_dir="/tmp/out"),
            "Batch export 3/3 → /tmp/out",
        )
        self.assertIn(
            "gone",
            batch.done_message(2, 3, errors=["Shot camera “Hero” is gone — Add Camera"]),
        )
        self.assertEqual(batch.done_message(0, 3), "Batch export 0/3")


class BatchWiringTests(unittest.TestCase):
    def test_apply_renders_pngs_and_restores(self) -> None:
        apply = _read("behold/shoot/batch_apply.py")
        self.assertIn("plan_batch", apply)
        self.assertIn("write_still=True", apply)
        self.assertIn("product_targets", apply)
        self.assertIn("apply_shot_to_scene", apply)
        self.assertIn("apply_payload_to_scene", apply)
        self.assertIn("matrix_world", apply)
        self.assertIn("progress_begin", apply)
        self.assertIn("progress_update", apply)
        self.assertIn("progress_end", apply)
        self.assertIn("angle_world_offset", apply)
        self.assertIn("fill_output_tokens", _read("behold/shoot/operators.py"))

    def test_operator_and_properties(self) -> None:
        ops = _read("behold/shoot/operators.py")
        props = _read("behold/properties.py")
        self.assertIn('bl_idname = "behold.batch_angles"', ops)
        self.assertIn('bl_label = "Batch export"', ops)
        self.assertIn("run_batch_export", ops)
        self.assertIn("batch_include_angles", props)
        self.assertIn("batch_include_shots", props)
        self.assertIn("Front / ¾ / Top", props)
        self.assertIn("Saved shots", props)

    def test_shoot_batch_card_stays_compact(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        first = _func_source(source, tree, "draw_shoot_first_ship")
        compact = _func_source(source, tree, "draw_batch_compact")
        shots = _func_source(source, tree, "draw_shots_compact")
        parked = _func_source(source, tree, "draw_shoot_parked")
        self.assertIn("draw_batch_compact", first)
        self.assertLess(first.index("draw_shots_compact"), first.index("draw_batch_compact"))
        self.assertLess(
            first.index("draw_batch_compact"), first.index("draw_turntable_compact")
        )
        self.assertIn("behold.batch_angles", compact)
        self.assertIn("batch_include_angles", compact)
        self.assertIn("batch_include_shots", compact)
        self.assertIn("BATCH_TOKEN_HINT", compact)
        self.assertIn('text="Batch export"', compact)
        self.assertNotIn("batch_include_angles", shots)
        self.assertNotIn("exposure_ev", compact)
        self.assertNotIn("BEHOLD_PT_batch", source)
        self.assertIn("behold.batch_angles", parked)
        self.assertIn("batch_include_angles", parked)
        self.assertIn("output_directory", parked)

    def test_messages_cover_batch_failures(self) -> None:
        self.assertEqual(messages.BATCH_NO_MESH, batch.BATCH_NO_MESH)
        self.assertEqual(messages.BATCH_NO_CAMERA, messages.NO_CAMERA)
        self.assertEqual(messages.report_type(messages.BATCH_NOTHING), "WARNING")
        self.assertEqual(messages.report_type(messages.BATCH_NO_MESH), "WARNING")
        self.assertEqual(messages.report_type(messages.BATCH_NO_SHOTS), "WARNING")
        self.assertEqual(messages.report_type(messages.BATCH_RENDER_FAILED), "ERROR")
        self.assertEqual(
            messages.report_type("Batch export 2/3 — camera gone"),
            "WARNING",
        )
        self.assertIn("Import Product", messages.BATCH_NO_MESH)
        self.assertIn("Saved shots", messages.BATCH_NO_SHOTS)
        self.assertIn("Front / ¾ / Top", messages.BATCH_NOTHING)


if __name__ == "__main__":
    unittest.main()
