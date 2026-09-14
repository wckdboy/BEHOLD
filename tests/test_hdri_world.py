# SPDX-License-Identifier: GPL-3.0-or-later
"""HDRI world graph spec and Studio wiring — no Blender import."""

from __future__ import annotations

import ast
import math
import tempfile
import unittest
from pathlib import Path

from tests.support import ROOT, load_addon_module, load_module

world = load_module("behold/studio/world.py", "behold_studio_world")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class HdriSpecTests(unittest.TestCase):
    def test_rotation_is_z_in_radians(self) -> None:
        x, y, z = world.rotation_radians_z(90.0)
        self.assertEqual(x, 0.0)
        self.assertEqual(y, 0.0)
        self.assertAlmostEqual(z, math.pi / 2.0)
        self.assertAlmostEqual(world.degrees_to_radians(180.0), math.pi)

    def test_simple_graph_has_env_mapping_and_background(self) -> None:
        nodes = {spec.key: spec.bl_idname for spec in world.hdri_nodes(reflections_only=False)}
        self.assertEqual(nodes["env"], "ShaderNodeTexEnvironment")
        self.assertEqual(nodes["mapping"], "ShaderNodeMapping")
        self.assertEqual(nodes["tex_coord"], "ShaderNodeTexCoord")
        self.assertEqual(nodes["bg"], "ShaderNodeBackground")
        self.assertEqual(nodes["output"], "ShaderNodeOutputWorld")
        self.assertNotIn("mix", nodes)
        links = {(link.from_key, link.to_key, link.to_socket) for link in world.hdri_links(reflections_only=False)}
        self.assertIn(("tex_coord", "mapping", "Vector"), links)
        self.assertIn(("mapping", "env", "Vector"), links)
        self.assertIn(("env", "bg", "Color"), links)
        self.assertIn(("bg", "output", "Surface"), links)

    def test_reflections_only_mixes_on_camera_ray(self) -> None:
        nodes = {spec.key: spec.bl_idname for spec in world.hdri_nodes(reflections_only=True)}
        self.assertEqual(nodes["mix"], "ShaderNodeMixShader")
        self.assertEqual(nodes["light_path"], "ShaderNodeLightPath")
        self.assertEqual(nodes["bg_camera"], "ShaderNodeBackground")
        links = world.hdri_links(reflections_only=True)
        self.assertIn(
            world.LinkSpec("light_path", "Is Camera Ray", "mix", 0),
            links,
        )
        self.assertIn(world.LinkSpec("bg", "Background", "mix", 1), links)
        self.assertIn(world.LinkSpec("bg_camera", "Background", "mix", 2), links)
        self.assertIn(world.LinkSpec("mix", "Shader", "output", "Surface"), links)

    def test_solid_world_is_background_only(self) -> None:
        names = tuple(spec.name for spec in world.solid_world_nodes())
        self.assertEqual(names, (world.NODE_BG, world.NODE_OUTPUT))
        self.assertEqual(
            world.solid_world_links(),
            (world.LinkSpec("bg", "Background", "output", "Surface"),),
        )

    def test_path_classifier(self) -> None:
        self.assertEqual(world.classify_hdri_filepath("").kind, "empty")
        self.assertEqual(world.classify_hdri_filepath("   ").kind, "empty")
        bad = world.classify_hdri_filepath("look.blend")
        self.assertIsNotNone(bad)
        self.assertEqual(bad.kind, "unsupported")
        self.assertEqual(bad.detail, ".blend")
        missing = world.classify_hdri_filepath("/tmp/no-such-studio.hdr")
        self.assertIsNotNone(missing)
        self.assertEqual(missing.kind, "missing")
        self.assertTrue(world.is_blender_relative("//studio.hdr"))
        self.assertIsNone(world.existing_filepath("//studio.hdr"))
        rel = world.classify_hdri_filepath("//studio.hdr")
        self.assertIsNotNone(rel)
        self.assertEqual(rel.kind, "missing")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "studio.hdr"
            path.write_bytes(b"#dummy")
            self.assertIsNone(world.classify_hdri_filepath(str(path)))
            resolved = world.existing_filepath(str(path))
            self.assertIsNotNone(resolved)
            self.assertTrue(str(resolved).endswith("studio.hdr"))
            via_resolved = world.classify_hdri_filepath(
                "/nope/missing.hdr",
                resolved=str(path),
            )
            self.assertIsNone(via_resolved)
            still_bad = world.classify_hdri_filepath(
                "look.blend",
                resolved=str(path),
            )
            self.assertIsNotNone(still_bad)
            self.assertEqual(still_bad.kind, "unsupported")

    def test_all_hdri_extensions_and_filter_glob(self) -> None:
        self.assertTrue(world.is_hdri_extension("studio.HDR"))
        self.assertTrue(world.is_hdri_extension("studio.JPEG"))
        self.assertEqual(world.hdri_extension("a.TIFF"), ".tiff")
        self.assertFalse(world.is_hdri_extension("a.blend"))
        self.assertFalse(world.is_hdri_extension(""))
        glob = world.HDRI_FILTER_GLOB.lower()
        with tempfile.TemporaryDirectory() as tmp:
            for ext in sorted(world.HDRI_EXTENSIONS):
                self.assertIn(f"*{ext}", glob, ext)
                path = Path(tmp) / f"env{ext}"
                path.write_bytes(b"#dummy")
                self.assertIsNone(world.classify_hdri_filepath(str(path)), ext)

    def test_rotation_edge_values(self) -> None:
        self.assertEqual(world.rotation_radians_z(0.0), (0.0, 0.0, 0.0))
        self.assertAlmostEqual(world.rotation_radians_z(360.0)[2], math.tau)
        self.assertAlmostEqual(world.rotation_radians_z(-90.0)[2], -math.pi / 2.0)
        self.assertAlmostEqual(world.degrees_to_radians(0.0), 0.0)

    def test_graph_keys_are_unique(self) -> None:
        for reflections in (False, True):
            nodes = world.hdri_nodes(reflections_only=reflections)
            keys = [spec.key for spec in nodes]
            names = [spec.name for spec in nodes]
            self.assertEqual(len(keys), len(set(keys)), keys)
            self.assertEqual(len(names), len(set(names)), names)
            for link in world.hdri_links(reflections_only=reflections):
                self.assertIn(link.from_key, keys)
                self.assertIn(link.to_key, keys)


class HdriWiringTests(unittest.TestCase):
    def test_apply_module_wires_the_spec(self) -> None:
        source = _read("behold/studio/world_apply.py")
        self.assertIn("hdri_nodes", source)
        self.assertIn("hdri_links", source)
        self.assertIn("_wire_plan", source)
        self.assertIn("nodes.clear()", source)
        self.assertIn("tree.nodes.new", source)
        self.assertIn("images.load", source)
        self.assertIn("reapply_hdri_if_loaded", source)
        self.assertIn("setup_solid_world", source)
        self.assertIn("path_problem_message", source)
        self.assertIn("classify_hdri_filepath", source)
        self.assertIn("Is Camera Ray", _read("behold/studio/world.py"))

    def test_setup_preserves_hdri_after_build(self) -> None:
        setup = _read("behold/studio/setup.py")
        self.assertIn("reapply_hdri_if_loaded", setup)
        self.assertIn("setup_solid_world", setup)

    def test_operators_and_properties(self) -> None:
        ops = _read("behold/studio/operators.py")
        props = _read("behold/properties.py")
        self.assertIn('bl_idname = "behold.load_hdri"', ops)
        self.assertIn('bl_idname = "behold.reset_world"', ops)
        self.assertIn("ImportHelper", ops)
        self.assertIn("HDRI_FILTER_GLOB", ops)
        self.assertIn("report_set", ops)
        self.assertIn("hdri_filepath", props)
        self.assertIn("hdri_strength", props)
        self.assertIn("hdri_rotation", props)
        self.assertIn("hdri_reflections_only", props)
        self.assertIn("hdri_background_strength", props)
        self.assertIn("on_hdri_filepath_update", props)
        self.assertIn("on_hdri_values_update", props)

    def test_studio_hdri_card_stays_compact(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        first = _func_source(source, tree, "draw_studio_first_ship")
        hdri = _func_source(source, tree, "draw_studio_hdri")
        self.assertIn("draw_studio_hdri", first)
        self.assertIn("studio_backdrop_tone", first)
        self.assertIn('text="Build"', first)
        self.assertNotIn("studio_margin", first)
        self.assertNotIn("key_power", first)
        self.assertIn("behold.load_hdri", hdri)
        self.assertIn("behold.reset_world", hdri)
        self.assertIn("hdri_strength", hdri)
        self.assertIn("hdri_rotation", hdri)
        self.assertIn("hdri_reflections_only", hdri)
        self.assertIn("hdri_background_strength", hdri)
        self.assertNotIn("studio_margin", hdri)
        self.assertNotIn("Light Mixer", hdri)
        self.assertNotIn("BEHOLD_PT_hdri", source)

    def test_messages_cover_hdri_failures(self) -> None:
        self.assertIn("pick an HDR", messages.NO_HDRI_FILE)
        self.assertIn("Load HDRI", messages.NO_WORLD)
        self.assertIn("solid studio", messages.WORLD_RESET)
        missing = messages.hdri_file_not_found("/tmp/gone.hdr")
        self.assertTrue(missing.startswith("HDRI file not found:"))
        self.assertIn("gone.hdr", missing)
        self.assertEqual(messages.report_type(messages.NO_HDRI_FILE), "WARNING")
        self.assertEqual(messages.report_type(missing), "WARNING")
        self.assertEqual(
            messages.report_type(messages.unsupported_hdri_message(".blend")),
            "WARNING",
        )
        self.assertEqual(messages.report_type(messages.HDRI_LOAD_FAILED), "ERROR")
        self.assertIn("studio.hdr", messages.hdri_loaded_message("/tmp/studio.hdr"))


if __name__ == "__main__":
    unittest.main()
