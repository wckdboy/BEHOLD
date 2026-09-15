# SPDX-License-Identifier: GPL-3.0-or-later
"""IES practical lite — BYO photometric profile (no Blender)."""

from __future__ import annotations

import ast
import math
import os
import tempfile
import unittest
from pathlib import Path

from tests.support import ROOT, load_addon_module, load_module

ies = load_module("behold/studio/ies.py", "behold_studio_ies")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class IesSpecTests(unittest.TestCase):
    def test_extensions_and_defaults(self) -> None:
        self.assertEqual(ies.IES_EXTENSIONS, frozenset({".ies"}))
        self.assertEqual(ies.IES_FILTER_GLOB, "*.ies")
        self.assertEqual(ies.DEFAULT_STRENGTH, 1.0)
        self.assertEqual(ies.DEFAULT_SCALE, 1.0)
        self.assertEqual(ies.NATIVE_TYPES, frozenset({"SPOT", "POINT"}))
        self.assertEqual(ies.CONVERTIBLE_TYPES, frozenset({"AREA"}))
        self.assertEqual(ies.REJECTED_TYPES, frozenset({"SUN"}))
        self.assertTrue(ies.is_ies_extension("lamp.ies"))
        self.assertTrue(ies.is_ies_extension("LAMP.IES"))
        self.assertFalse(ies.is_ies_extension("lamp.hdr"))
        self.assertTrue(ies.owned_node_name("BEHOLD_IESTex"))
        self.assertFalse(ies.owned_node_name("BEHOLD_GoboWave"))

    def test_clamp_strength_and_scale(self) -> None:
        self.assertAlmostEqual(ies.clamp_strength(1.0), 1.0)
        self.assertAlmostEqual(ies.clamp_strength(-1.0), ies.MIN_STRENGTH)
        self.assertAlmostEqual(ies.clamp_strength(99.0), ies.MAX_STRENGTH)
        self.assertAlmostEqual(ies.clamp_scale(0.0), ies.MIN_SCALE)
        self.assertAlmostEqual(ies.clamp_scale(99.0), ies.MAX_SCALE)
        self.assertEqual(ies.mapping_scale(2.0), (2.0, 2.0, 2.0))
        self.assertAlmostEqual(ies.default_spot_size_radians(), math.radians(45.0))

    def test_type_plan(self) -> None:
        keep = ies.plan_light_type("SPOT")
        self.assertEqual(keep.action, "keep")
        self.assertEqual(keep.target_type, "SPOT")
        point = ies.plan_light_type("POINT")
        self.assertEqual(point.action, "keep")
        area = ies.plan_light_type("AREA")
        self.assertEqual(area.action, "convert")
        self.assertEqual(area.target_type, "SPOT")
        self.assertEqual(area.prior_type, "AREA")
        sun = ies.plan_light_type("SUN")
        self.assertEqual(sun.action, "reject")
        empty = ies.plan_light_type("")
        self.assertEqual(empty.action, "reject")

    def test_path_classifier(self) -> None:
        self.assertEqual(ies.classify_ies_filepath("").kind, "empty")
        self.assertEqual(ies.classify_ies_filepath("   ").kind, "empty")
        bad = ies.classify_ies_filepath("look.hdr")
        self.assertIsNotNone(bad)
        self.assertEqual(bad.kind, "unsupported")
        self.assertEqual(bad.detail, ".hdr")
        missing = ies.classify_ies_filepath("/tmp/no-such-fixture.ies")
        self.assertIsNotNone(missing)
        self.assertEqual(missing.kind, "missing")
        self.assertEqual(ies.path_problem_message(ies.PathProblem("empty")), ies.NO_IES_FILE)
        self.assertIn(".ies", ies.path_problem_message(ies.PathProblem("unsupported", ".hdr")))
        self.assertIn("not found", ies.path_problem_message(ies.PathProblem("missing", "gone.ies")))

    def test_path_classifier_accepts_existing_file(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".ies", delete=False) as handle:
            handle.write(b"IESNA:LM-63-2002\n")
            path = handle.name
        try:
            self.assertIsNone(ies.classify_ies_filepath(path))
            self.assertEqual(ies.existing_filepath(path), os.path.abspath(path))
        finally:
            os.unlink(path)

    def test_applied_and_error_copy(self) -> None:
        self.assertEqual(
            ies.applied_message("/tmp/erco.ies", "BEHOLD_Key"),
            "IES loaded: erco.ies on Key",
        )
        self.assertEqual(ies.cleared_message(), ies.IES_CLEARED)
        self.assertIn("prior", ies.IES_CLEARED)
        self.assertIn("spot or point", ies.NO_IES_TYPE)
        self.assertIn("sun", ies.NO_IES_TYPE.lower())
        self.assertIn("Add Light", ies.NO_IES_TYPE)
        self.assertEqual(messages.NO_IES_FILE, ies.NO_IES_FILE)
        self.assertEqual(messages.NO_IES_TYPE, ies.NO_IES_TYPE)
        self.assertEqual(messages.IES_NODES_FAILED, ies.IES_NODES_FAILED)
        self.assertEqual(messages.report_type(messages.NO_IES_FILE), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_IES_TYPE), "WARNING")
        self.assertEqual(messages.report_type(messages.IES_NODES_FAILED), "ERROR")
        self.assertEqual(
            messages.report_type(ies.ies_file_not_found("gone.ies")),
            "WARNING",
        )
        self.assertEqual(
            messages.report_type(ies.unsupported_ies_message(".hdr")),
            "WARNING",
        )


class IesNodeGraphTests(unittest.TestCase):
    def test_graph_is_ies_into_emission(self) -> None:
        graph = ies.node_graph_for("/tmp/spot.ies", strength=0.5, scale=2.0)
        types = {node.key: node.bl_idname for node in graph.nodes}
        self.assertEqual(types["geom"], "ShaderNodeNewGeometry")
        self.assertEqual(types["mapping"], "ShaderNodeMapping")
        self.assertEqual(types["ies"], "ShaderNodeTexIES")
        self.assertEqual(types["emission"], "ShaderNodeEmission")
        self.assertEqual(types["output"], "ShaderNodeOutputLight")
        self.assertEqual(graph.ies_mode, "EXTERNAL")
        self.assertAlmostEqual(graph.strength, 0.5)
        self.assertEqual(graph.scale, (2.0, 2.0, 2.0))
        self.assertEqual(graph.filepath, "/tmp/spot.ies")
        links = {(link.from_key, link.to_key, link.to_socket) for link in graph.links}
        self.assertIn(("geom", "mapping", "Vector"), links)
        self.assertIn(("mapping", "ies", "Vector"), links)
        self.assertIn(("ies", "emission", "Strength"), links)
        self.assertIn(("emission", "output", "Surface"), links)


class IesSampleTests(unittest.TestCase):
    def test_bundled_sample_is_tiny_cc0_ies(self) -> None:
        path = Path(ies.bundled_sample_path())
        self.assertTrue(path.is_file(), path)
        self.assertEqual(path.name, "sample_spot.ies")
        text = path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("IESNA:LM-63-2002"))
        self.assertIn("TILT=NONE", text)
        self.assertIn("CC0", text)
        self.assertLess(path.stat().st_size, 2048)
        readme = _read("behold/ies/README.md")
        self.assertIn("CC0", readme)
        self.assertIn("Bring your own", readme)
        self.assertIn("sample_spot.ies", readme)


class IesWiringTests(unittest.TestCase):
    def test_apply_module_wires_the_spec(self) -> None:
        source = _read("behold/studio/ies_apply.py")
        self.assertIn("node_graph_for", source)
        self.assertIn("nodes.clear()", source)
        self.assertIn("tree.nodes.new", source)
        self.assertIn("teardown_ies", source)
        self.assertIn("apply_ies_in_scene", source)
        self.assertIn("apply_ies_to_object", source)
        self.assertIn("on_ies_filepath_update", source)
        self.assertIn("on_ies_values_update", source)
        self.assertIn("release_ies_if_active", source)
        self.assertIn("get_active_behold_light", source)
        self.assertIn("NO_IES_TYPE", source)
        self.assertIn("IES_NODES_FAILED", source)
        self.assertIn("plan_light_type", source)
        self.assertIn("use_nodes = False", source)
        self.assertIn("ies.mode", source)
        self.assertIn("ies.filepath", source)
        self.assertIn("_restore_prior_type", source)
        self.assertIn("apply_preset_to_object", source)
        self.assertIn("apply_gobo_to_object", source)

    def test_operator_and_property(self) -> None:
        ops = _read("behold/studio/operators.py")
        props = _read("behold/properties.py")
        self.assertIn('bl_idname = "behold.load_ies"', ops)
        self.assertIn('bl_idname = "behold.clear_ies"', ops)
        self.assertIn('bl_idname = "behold.apply_ies"', ops)
        self.assertIn('bl_idname = "behold.load_ies_sample"', ops)
        self.assertIn("apply_ies_in_scene", ops)
        self.assertIn("teardown_ies_in_scene", ops)
        self.assertIn("light_ies_filepath", props)
        self.assertIn("light_ies_strength", props)
        self.assertIn("light_ies_scale", props)
        self.assertIn("on_ies_filepath_update", props)
        self.assertIn("on_ies_values_update", props)
        self.assertIn("bundled_sample_path", ops)

    def test_shape_apply_reapplies_active_ies(self) -> None:
        ops = _read("behold/studio/operators.py")
        tree = ast.parse(ops, filename="operators.py")
        shape_cls = None
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == "BEHOLD_OT_apply_light_preset":
                shape_cls = node
                break
        self.assertIsNotNone(shape_cls)
        assert shape_cls is not None
        execute = next(
            child
            for child in shape_cls.body
            if isinstance(child, ast.FunctionDef) and child.name == "execute"
        )
        src = ast.get_source_segment(ops, execute) or ""
        self.assertIn("light_ies_filepath", src)
        self.assertIn("release_ies_if_active", src)
        self.assertIn("apply_ies_in_scene", src)
        self.assertLess(src.index("release_ies_if_active"), src.index("apply_preset_in_scene"))

    def test_gobo_apply_releases_ies(self) -> None:
        source = _read("behold/studio/gobo_apply.py")
        self.assertIn("release_ies_if_active", source)

    def test_panel_ies_card_stays_off_empty_state(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        body = _func_source(source, tree, "draw_lights_section")
        self.assertIn("EMPTY_LIGHTS", body)
        self.assertIn("draw_empty_card", body)
        self.assertIn("light_ies_filepath", body)
        self.assertIn("light_ies_strength", body)
        self.assertIn("light_ies_scale", body)
        self.assertIn("behold.load_ies", body)
        self.assertIn("behold.clear_ies", body)
        self.assertIn("behold.load_ies_sample", body)
        self.assertIn('text="IES"', body)
        empty_idx = body.index("draw_empty_card")
        gobo_idx = body.index("light_gobo_preset")
        ies_idx = body.index("light_ies_filepath")
        shape_idx = body.index("light_shape_preset")
        link_idx = body.index("behold.link_selected")
        self.assertLess(empty_idx, ies_idx)
        self.assertLess(shape_idx, gobo_idx)
        self.assertLess(gobo_idx, ies_idx)
        self.assertLess(ies_idx, link_idx)
        self.assertNotIn("BEHOLD_PT_ies", source)
        parked = _func_source(source, tree, "draw_light_draw_parked")
        self.assertIn("behold.apply_ies", parked)
        self.assertIn("behold.clear_ies", parked)
        self.assertIn("light_ies_filepath", parked)


if __name__ == "__main__":
    unittest.main()
