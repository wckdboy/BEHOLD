# SPDX-License-Identifier: GPL-3.0-or-later
"""Compositor look pack spec and Shoot wiring — no Blender import."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module, load_module

looks = load_module("behold/shoot/looks.py", "behold_shoot_looks")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class LookPresetTests(unittest.TestCase):
    def test_rack_order_and_labels(self) -> None:
        self.assertEqual(list(looks.PRESETS), ["CLEAN", "CATALOG", "DRAMATIC"])
        self.assertEqual(looks.DEFAULT_PRESET, "CLEAN")
        labels = [preset.label for preset in looks.PRESETS.values()]
        self.assertEqual(labels, ["Clean", "Catalog", "Dramatic"])
        items = looks.preset_enum_items()
        self.assertEqual(len(items), 3)
        self.assertEqual(items[0][0], "CLEAN")
        self.assertEqual(items[1][1], "Catalog")
        self.assertEqual(items[2][1], "Dramatic")

    def test_catalog_is_milder_and_bloom_safe(self) -> None:
        clean = looks.PRESETS["CLEAN"]
        catalog = looks.PRESETS["CATALOG"]
        dramatic = looks.PRESETS["DRAMATIC"]
        self.assertEqual(clean.vignette, 0.0)
        self.assertEqual(clean.grain, 0.0)
        self.assertEqual(clean.contrast, 0.0)
        self.assertEqual(clean.glare_mix, -1.0)
        self.assertTrue(clean.bloom_safe)
        self.assertGreater(catalog.vignette, 0.0)
        self.assertLess(catalog.vignette, dramatic.vignette)
        self.assertGreater(catalog.grain, 0.0)
        self.assertLess(catalog.grain, dramatic.grain)
        self.assertGreater(catalog.contrast, 0.0)
        self.assertLess(catalog.contrast, dramatic.contrast)
        self.assertEqual(catalog.glare_mix, -1.0)
        self.assertTrue(catalog.bloom_safe)
        self.assertGreater(dramatic.glare_mix, -1.0)
        self.assertLess(dramatic.glare_mix, 0.0)
        self.assertTrue(dramatic.bloom_safe)
        self.assertGreater(catalog.vignette_width, dramatic.vignette_width)
        self.assertGreater(catalog.vignette_height, dramatic.vignette_height)

    def test_applied_and_unknown_copy(self) -> None:
        self.assertIn("passthrough", looks.applied_message(looks.PRESETS["CLEAN"]))
        self.assertIn("bloom off", looks.applied_message(looks.PRESETS["CATALOG"]))
        self.assertIn("bloom-safe", looks.applied_message(looks.PRESETS["DRAMATIC"]))
        self.assertEqual(looks.disabled_message(), looks.LOOK_DISABLED)
        self.assertEqual(messages.LOOK_DISABLED, looks.LOOK_DISABLED)
        self.assertIn("vignette", looks.LOOK_DISABLED)
        self.assertEqual(looks.unknown_look_message(""), looks.UNKNOWN_LOOK_PRESET)
        self.assertIn("Gobo", looks.unknown_look_message("Gobo"))
        self.assertIn("Clean", looks.unknown_look_message("Gobo"))
        self.assertEqual(
            messages.unknown_look_preset_message("Gobo"),
            looks.unknown_look_message("Gobo"),
        )
        self.assertEqual(messages.UNKNOWN_LOOK_PRESET, looks.UNKNOWN_LOOK_PRESET)
        self.assertEqual(messages.report_type(messages.UNKNOWN_LOOK_PRESET), "ERROR")
        self.assertEqual(
            messages.report_type(messages.unknown_look_preset_message("Gobo")),
            "ERROR",
        )
        self.assertEqual(messages.report_type(messages.NO_COMPOSITOR), "WARNING")
        self.assertEqual(messages.report_type(messages.LOOK_COMPOSITOR_BUSY), "WARNING")
        self.assertEqual(messages.report_type(messages.LOOK_NODES_FAILED), "ERROR")
        self.assertIn("toggle Compositor", messages.NO_COMPOSITOR)
        self.assertIn("clear them", messages.LOOK_COMPOSITOR_BUSY)


class NodeGraphTests(unittest.TestCase):
    def test_clean_is_passthrough(self) -> None:
        graph = looks.node_graph_for("CLEAN")
        self.assertIsNotNone(graph)
        assert graph is not None
        keys = [spec.key for spec in graph.nodes]
        self.assertEqual(keys, ["rlayers", "composite"])
        self.assertEqual(
            graph.links,
            (looks.LinkSpec("rlayers", "Image", "composite", "Image"),),
        )
        self.assertFalse(graph.include_vignette)
        self.assertFalse(graph.include_grain)
        self.assertFalse(graph.include_contrast)
        self.assertFalse(graph.include_glare)
        self.assertIsNone(looks.node_graph_for("GOBO"))
        self.assertIsNone(looks.node_graph_for(""))

    def test_catalog_has_vignette_grain_contrast_no_glare(self) -> None:
        graph = looks.node_graph_for("CATALOG")
        self.assertIsNotNone(graph)
        assert graph is not None
        types = {spec.key: spec.bl_idname for spec in graph.nodes}
        self.assertEqual(types["rlayers"], "CompositorNodeRLayers")
        self.assertEqual(types["composite"], "CompositorNodeComposite")
        self.assertEqual(types["contrast"], "CompositorNodeBrightContrast")
        self.assertEqual(types["vignette_mask"], "CompositorNodeEllipseMask")
        self.assertEqual(types["vignette_blur"], "CompositorNodeBlur")
        self.assertEqual(types["vignette_invert"], "CompositorNodeInvert")
        self.assertEqual(types["vignette_amount"], "CompositorNodeMath")
        self.assertEqual(types["vignette_mix"], "CompositorNodeMixRGB")
        self.assertEqual(types["grain"], "CompositorNodeTexture")
        self.assertEqual(types["grain_mix"], "CompositorNodeMixRGB")
        self.assertNotIn("glare", types)
        self.assertTrue(graph.include_vignette)
        self.assertTrue(graph.include_grain)
        self.assertTrue(graph.include_contrast)
        self.assertFalse(graph.include_glare)
        self.assertAlmostEqual(graph.glare_mix, -1.0)
        self.assertAlmostEqual(graph.vignette, looks.PRESETS["CATALOG"].vignette)
        self.assertAlmostEqual(graph.grain, looks.PRESETS["CATALOG"].grain)
        links = {(link.from_key, link.to_key, link.to_socket) for link in graph.links}
        self.assertIn(("rlayers", "contrast", "Image"), links)
        self.assertIn(("vignette_mask", "vignette_blur", "Image"), links)
        self.assertIn(("vignette_amount", "vignette_mix", "Fac"), links)
        self.assertIn(("grain", "grain_mix", "Color2"), links)
        self.assertIn(("grain_mix", "composite", "Image"), links)
        self.assertNotIn(("glare", "composite", "Image"), links)

    def test_dramatic_adds_bloom_safe_glare(self) -> None:
        graph = looks.node_graph_for("DRAMATIC")
        self.assertIsNotNone(graph)
        assert graph is not None
        types = {spec.key: spec.bl_idname for spec in graph.nodes}
        self.assertEqual(types["glare"], "CompositorNodeGlare")
        self.assertTrue(graph.include_glare)
        self.assertGreater(graph.glare_mix, -1.0)
        self.assertLess(graph.glare_mix, 0.0)
        self.assertEqual(graph.glare_type, "FOG_GLOW")
        links = {(link.from_key, link.to_key, link.to_socket) for link in graph.links}
        self.assertIn(("grain_mix", "glare", "Image"), links)
        self.assertIn(("glare", "composite", "Image"), links)
        self.assertNotIn(("grain_mix", "composite", "Image"), links)

    def test_graph_keys_and_owned_names_are_unique(self) -> None:
        for preset_id in looks.PRESETS:
            graph = looks.node_graph_for(preset_id)
            self.assertIsNotNone(graph, preset_id)
            assert graph is not None
            keys = [spec.key for spec in graph.nodes]
            names = [spec.name for spec in graph.nodes]
            self.assertEqual(len(keys), len(set(keys)), keys)
            self.assertEqual(len(names), len(set(names)), names)
            for spec in graph.nodes:
                self.assertTrue(looks.owned_node_name(spec.name), spec.name)
                self.assertTrue(spec.name.startswith(looks.OWNED_PREFIX), spec.name)
            for link in graph.links:
                self.assertIn(link.from_key, keys)
                self.assertIn(link.to_key, keys)

    def test_teardown_keeps_foreign_nodes(self) -> None:
        names = (
            looks.NODE_VIGNETTE_MIX,
            "Render Layers",
            "Composite",
            looks.NODE_GRAIN,
            "MyGlare",
        )
        remaining = looks.remaining_after_teardown(names)
        self.assertEqual(remaining, ("Render Layers", "Composite", "MyGlare"))
        self.assertTrue(looks.owned_node_name("BEHOLD_LookGrain"))
        self.assertFalse(looks.owned_node_name("Composite"))
        self.assertFalse(looks.owned_node_name(""))


class LookWiringTests(unittest.TestCase):
    def test_apply_module_wires_the_spec(self) -> None:
        source = _read("behold/shoot/looks_apply.py")
        self.assertIn("node_graph_for", source)
        self.assertIn("nodes.clear()", source)
        self.assertIn("tree.nodes.new", source)
        self.assertIn("tree_has_foreign_nodes", source)
        self.assertIn("clear_owned_nodes", source)
        self.assertIn("use_compositing", source)
        self.assertIn("LOOK_COMPOSITOR_BUSY", source)
        self.assertIn("NO_COMPOSITOR", source)
        self.assertIn("CompositorNodeMix", source)
        self.assertIn("CompositorNodeNoiseTexture", source)
        self.assertIn("GLARE_FOG_GLOW", source)
        self.assertIn("FOG_GLOW", _read("behold/shoot/looks.py"))
        self.assertIn("on_look_update", source)
        self.assertIn("GRAIN_TEXTURE_NAME", source)

    def test_operator_and_property(self) -> None:
        ops = _read("behold/shoot/operators.py")
        props = _read("behold/properties.py")
        self.assertIn('bl_idname = "behold.apply_look"', ops)
        self.assertIn("from .looks_apply import apply_look", ops)
        self.assertIn("apply_look(context)", ops)
        self.assertIn("look_preset", props)
        self.assertIn("look_enabled", props)
        self.assertIn("LOOK_DEFAULT", props)
        self.assertIn("look_preset_enum_items", props)
        self.assertIn("on_look_update", props)
        self.assertIn("apply_look(context)", _read("behold/shoot/batch_apply.py"))

    def test_shoot_look_card_stays_compact(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        first = _func_source(source, tree, "draw_shoot_first_ship")
        look = _func_source(source, tree, "draw_look_compact")
        parked = _func_source(source, tree, "draw_shoot_parked")
        self.assertIn("draw_look_compact", first)
        self.assertLess(first.index("draw_look_compact"), first.index("draw_shots_compact"))
        self.assertIn("look_preset", look)
        self.assertIn("look_enabled", look)
        self.assertIn('text="Compositor"', look)
        self.assertIn("exposure_ev", look)
        self.assertIn("false_color", look)
        self.assertNotIn("behold.apply_look", look)
        self.assertNotIn("bookmark_camera", look)
        self.assertNotIn("BEHOLD_PT_look", source)
        self.assertIn("look_preset", parked)
        self.assertIn("look_enabled", parked)
        self.assertIn("behold.apply_look", parked)
        self.assertIn("behold.apply_exposure", parked)
        self.assertNotIn('icon="ERROR"', parked)

    def test_panel_order_unchanged(self) -> None:
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
