# SPDX-License-Identifier: GPL-3.0-or-later
"""Bake-to-HDRI path helpers and Studio wiring — no Blender import."""

from __future__ import annotations

import ast
import math
import tempfile
import unittest
from pathlib import Path

from tests.support import ROOT, load_addon_module, load_module

bake = load_addon_module("behold/studio/bake.py", "behold.studio.bake")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class BakePlanTests(unittest.TestCase):
    def test_resolution_presets_are_equirect_2_to_1(self) -> None:
        self.assertEqual(bake.resolution_wh("1K"), (1024, 512))
        self.assertEqual(bake.resolution_wh("2K"), (2048, 1024))
        self.assertEqual(bake.resolution_wh("1k"), (1024, 512))
        self.assertEqual(bake.normalize_resolution("nope"), "1K")
        self.assertEqual(bake.samples_for("1K"), 64)
        self.assertEqual(bake.samples_for("2K"), 128)
        self.assertEqual(bake.samples_for(""), 64)
        labels = {item[0] for item in bake.resolution_enum_items()}
        self.assertEqual(labels, {"1K", "2K"})

    def test_default_path_next_to_blend_or_temp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            next_to = bake.default_bake_filepath(
                "/proj/hero.blend",
                tempdir=tmp,
            )
            self.assertEqual(next_to, os_join("/proj", "behold_studio.exr"))
            unsaved = bake.default_bake_filepath("", tempdir=tmp)
            self.assertEqual(unsaved, str(Path(tmp) / "behold_studio.exr"))
            rel = bake.default_bake_filepath("//hero.blend", tempdir=tmp)
            self.assertEqual(rel, "//behold_studio.exr")

    def test_ensure_fills_empty_dir_and_extension(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = bake.ensure_bake_filepath(
                "",
                blend_filepath="/proj/a.blend",
                tempdir=tmp,
            )
            self.assertTrue(empty.endswith("behold_studio.exr"))
            folder = bake.ensure_bake_filepath(
                tmp,
                blend_filepath="",
                tempdir=tmp,
                is_dir=True,
            )
            self.assertEqual(folder, str(Path(tmp) / "behold_studio.exr"))
            no_ext = bake.ensure_bake_filepath(
                str(Path(tmp) / "look"),
                blend_filepath="",
                tempdir=tmp,
                is_dir=False,
            )
            self.assertTrue(no_ext.endswith("look.exr"))
            hdr = bake.ensure_bake_filepath(
                str(Path(tmp) / "look.hdr"),
                blend_filepath="",
                tempdir=tmp,
                is_dir=False,
            )
            self.assertTrue(hdr.endswith("look.hdr"))

    def test_classify_empty_and_unsupported(self) -> None:
        self.assertEqual(bake.classify_bake_filepath("").kind, "empty")
        self.assertEqual(bake.classify_bake_filepath("   ").kind, "empty")
        bad = bake.classify_bake_filepath("look.png")
        self.assertIsNotNone(bad)
        assert bad is not None
        self.assertEqual(bad.kind, "unsupported")
        self.assertEqual(bad.detail, ".png")
        self.assertIsNone(bake.classify_bake_filepath("/tmp/studio.exr"))
        self.assertIsNone(bake.classify_bake_filepath("/tmp/studio.HDR"))
        self.assertEqual(
            bake.path_problem_message(bake.BakePathProblem("empty")),
            bake.NO_BAKE_PATH,
        )
        self.assertIn(".png", bake.path_problem_message(bad))

    def test_plan_bake_wires_format_and_flags(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan, error = bake.plan_bake(
                filepath=str(Path(tmp) / "env.exr"),
                blend_filepath="",
                tempdir=tmp,
                resolution="2K",
                include_world=True,
                apply_after=True,
                is_dir=False,
            )
            self.assertIsNone(error)
            self.assertIsNotNone(plan)
            assert plan is not None
            self.assertEqual(plan.resolution, "2K")
            self.assertEqual(plan.width, 2048)
            self.assertEqual(plan.height, 1024)
            self.assertEqual(plan.samples, 128)
            self.assertTrue(plan.include_world)
            self.assertTrue(plan.apply_after)
            self.assertEqual(plan.image_format, "OPEN_EXR")
            self.assertEqual(plan.rotation_xyz, bake.PROBE_ROTATION_XYZ)
            hdr, hdr_error = bake.plan_bake(
                filepath=str(Path(tmp) / "env.hdr"),
                blend_filepath="",
                tempdir=tmp,
                resolution="1K",
                include_world=False,
                apply_after=False,
                is_dir=False,
            )
            self.assertIsNone(hdr_error)
            assert hdr is not None
            self.assertEqual(hdr.image_format, "HDR")
            self.assertEqual(hdr.width, 1024)
            nope, nope_error = bake.plan_bake(
                filepath=str(Path(tmp) / "env.png"),
                blend_filepath="",
                tempdir=tmp,
                resolution="1K",
                include_world=False,
                apply_after=False,
                is_dir=False,
            )
            self.assertIsNone(nope)
            self.assertIsNotNone(nope_error)
            self.assertIn(".png", nope_error or "")

    def test_hide_meshes_only_and_probe_clip(self) -> None:
        self.assertTrue(bake.should_hide_for_bake("MESH"))
        self.assertTrue(bake.should_hide_for_bake("mesh"))
        self.assertFalse(bake.should_hide_for_bake("LIGHT"))
        self.assertFalse(bake.should_hide_for_bake("CAMERA"))
        self.assertFalse(bake.should_hide_for_bake("EMPTY"))
        start, end = bake.probe_clip(2.0)
        self.assertGreater(end, start)
        self.assertGreaterEqual(end, 100.0)
        self.assertAlmostEqual(bake.PROBE_ROTATION_XYZ[0], math.pi / 2.0)
        self.assertEqual(bake.PROBE_ROTATION_XYZ[1:], (0.0, 0.0))

    def test_baked_message(self) -> None:
        self.assertEqual(
            bake.baked_message("/tmp/behold_studio.exr", applied=False),
            "Baked studio HDRI: behold_studio.exr",
        )
        self.assertIn(
            "applied as world",
            bake.baked_message("/tmp/behold_studio.exr", applied=True),
        )


def os_join(*parts: str) -> str:
    return str(Path(*parts))


class BakeWiringTests(unittest.TestCase):
    def test_apply_module_renders_equirect_and_restores(self) -> None:
        apply = _read("behold/studio/bake_apply.py")
        self.assertIn("plan_bake", apply)
        self.assertIn("CYCLES", apply)
        self.assertIn("EQUIRECTANGULAR", apply)
        self.assertIn("PANO", apply)
        self.assertIn("hide_render", apply)
        self.assertIn("include_world", apply)
        self.assertIn("apply_hdri", apply)
        self.assertIn("_snapshot_render", apply)
        self.assertIn("_restore_render", apply)
        self.assertIn("PROBE_NAME", apply)
        self.assertIn("iter_behold_lights", apply)
        self.assertIn("product_frame", apply)
        self.assertIn("save_render", apply)
        self.assertIn("scene.world = None", apply)

    def test_operator_and_properties(self) -> None:
        ops = _read("behold/studio/operators.py")
        props = _read("behold/properties.py")
        self.assertIn('bl_idname = "behold.bake_hdri"', ops)
        self.assertIn("bake_apply.bake_studio_hdri", ops)
        self.assertIn("report_set", ops)
        self.assertIn("bake_hdri_filepath", props)
        self.assertIn("bake_hdri_resolution", props)
        self.assertIn("bake_hdri_include_world", props)
        self.assertIn("bake_hdri_apply", props)
        self.assertIn("bake_resolution_enum_items", props)

    def test_studio_bake_card_stays_compact(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        first = _func_source(source, tree, "draw_studio_first_ship")
        hdri = _func_source(source, tree, "draw_studio_hdri")
        bake_ui = _func_source(source, tree, "draw_studio_bake")
        self.assertIn("draw_studio_hdri", first)
        self.assertIn("draw_studio_bake", first)
        self.assertLess(first.index("draw_studio_hdri"), first.index("draw_studio_bake"))
        self.assertNotIn("studio_margin", first)
        self.assertNotIn("key_power", first)
        self.assertNotIn("behold.bake_hdri", hdri)
        self.assertIn("behold.bake_hdri", bake_ui)
        self.assertIn("bake_hdri_filepath", bake_ui)
        self.assertIn("bake_hdri_resolution", bake_ui)
        self.assertIn("bake_hdri_include_world", bake_ui)
        self.assertIn("bake_hdri_apply", bake_ui)
        self.assertIn('text="Bake HDRI"', bake_ui)
        self.assertNotIn("studio_margin", bake_ui)
        self.assertNotIn("Light Mixer", bake_ui)
        self.assertNotIn("BEHOLD_PT_bake", source)
        self.assertNotIn("BEHOLD_PT_hdri", source)

    def test_messages_cover_bake_failures(self) -> None:
        self.assertEqual(messages.NO_LIGHTS_TO_BAKE, messages.NO_LIGHTS)
        self.assertEqual(messages.report_type(messages.NO_LIGHTS_TO_BAKE), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_BAKE_PATH), "WARNING")
        self.assertEqual(messages.report_type(messages.UNSUPPORTED_BAKE), "WARNING")
        self.assertEqual(
            messages.report_type(messages.bake_path_problem_message(
                bake.BakePathProblem("unsupported", ".png")
            )),
            "WARNING",
        )
        self.assertEqual(messages.report_type(messages.BAKE_FAILED), "ERROR")
        self.assertEqual(messages.report_type(messages.BAKE_RENDER_FAILED), "ERROR")
        self.assertIn("applied as world", messages.bake_hdri_message("a.exr", applied=True))
        self.assertIn(".hdr", messages.NO_BAKE_PATH)
        self.assertIn("Cycles", messages.BAKE_RENDER_FAILED)


if __name__ == "__main__":
    unittest.main()
