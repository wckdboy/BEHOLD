# SPDX-License-Identifier: GPL-3.0-or-later
"""Procedural gobo lite — blinds / window / circle (no Blender)."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module, load_module

gobos = load_module("behold/studio/gobos.py", "behold_studio_gobos")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class GoboPresetTests(unittest.TestCase):
    def test_rack_order_and_labels(self) -> None:
        self.assertEqual(list(gobos.PRESETS), ["NONE", "BLINDS", "WINDOW", "CIRCLE"])
        self.assertEqual(gobos.DEFAULT_PRESET, "NONE")
        labels = [preset.label for preset in gobos.PRESETS.values()]
        self.assertEqual(labels, ["None", "Blinds", "Window", "Circle"])
        items = gobos.preset_enum_items()
        self.assertEqual(len(items), 4)
        self.assertEqual(items[0][0], "NONE")
        self.assertEqual(items[1][1], "Blinds")
        self.assertEqual(items[2][1], "Window")
        self.assertEqual(items[3][1], "Circle")
        self.assertTrue(gobos.is_gobo("BLINDS"))
        self.assertFalse(gobos.is_gobo("IES"))

    def test_patterns_map_to_cycles_light_nodes(self) -> None:
        self.assertEqual(gobos.PRESETS["NONE"].pattern, "NONE")
        self.assertEqual(gobos.PRESETS["BLINDS"].pattern, "WAVE")
        self.assertEqual(gobos.PRESETS["WINDOW"].pattern, "BRICK")
        self.assertEqual(gobos.PRESETS["CIRCLE"].pattern, "SPHERE")
        self.assertEqual(gobos.SUPPORTED_TYPES, frozenset({"AREA", "SPOT"}))
        self.assertTrue(gobos.owned_node_name("BEHOLD_GoboWave"))
        self.assertFalse(gobos.owned_node_name("BEHOLD_LightEmission"))

    def test_scale_and_strength_clamp(self) -> None:
        self.assertAlmostEqual(gobos.clamp_scale(1.0), 1.0)
        self.assertAlmostEqual(gobos.clamp_scale(0.0), gobos.MIN_SCALE)
        self.assertAlmostEqual(gobos.clamp_scale(99.0), gobos.MAX_SCALE)
        self.assertAlmostEqual(gobos.clamp_strength(-1.0), 0.0)
        self.assertAlmostEqual(gobos.clamp_strength(2.0), 1.0)
        self.assertAlmostEqual(gobos.clamp_strength(0.4), 0.4)

    def test_mapping_scale_grows_with_control(self) -> None:
        blinds = gobos.mapping_for("WAVE", 1.0)
        blinds_hi = gobos.mapping_for("WAVE", 2.0)
        self.assertEqual(blinds.location, gobos.IDENTITY_MAPPING_LOCATION)
        self.assertGreater(blinds_hi.scale[1], blinds.scale[1])
        window = gobos.mapping_for("BRICK", 1.0)
        self.assertGreater(window.scale[1], window.scale[0])
        circle = gobos.mapping_for("SPHERE", 1.0)
        self.assertEqual(circle.location, gobos.CENTER_MAPPING_LOCATION)
        self.assertAlmostEqual(circle.scale[0], 2.0)

    def test_applied_and_unknown_copy(self) -> None:
        self.assertEqual(
            gobos.applied_message("Blinds", "BEHOLD_Key"),
            "Applied Blinds gobo to Key",
        )
        self.assertEqual(gobos.cleared_message(), gobos.GOBO_CLEARED)
        self.assertIn("uniform", gobos.GOBO_CLEARED)
        self.assertEqual(gobos.unknown_gobo_message(""), gobos.UNKNOWN_GOBO)
        self.assertIn("IES", gobos.unknown_gobo_message("IES"))
        self.assertIn("Blinds", gobos.unknown_gobo_message("IES"))
        self.assertEqual(
            messages.unknown_gobo_preset_message("IES"),
            gobos.unknown_gobo_message("IES"),
        )
        self.assertEqual(messages.UNKNOWN_GOBO, gobos.UNKNOWN_GOBO)
        self.assertEqual(messages.NO_GOBO_TYPE, gobos.NO_GOBO_TYPE)
        self.assertEqual(messages.GOBO_NODES_FAILED, gobos.GOBO_NODES_FAILED)
        self.assertEqual(messages.report_type(messages.UNKNOWN_GOBO), "ERROR")
        self.assertEqual(
            messages.report_type(messages.unknown_gobo_preset_message("IES")),
            "ERROR",
        )
        self.assertEqual(messages.report_type(messages.NO_GOBO_TYPE), "WARNING")
        self.assertEqual(messages.report_type(messages.GOBO_NODES_FAILED), "ERROR")
        self.assertIn("area or spot", messages.NO_GOBO_TYPE)
        self.assertIn("Add Light", messages.NO_GOBO_TYPE)


class GoboNodeGraphTests(unittest.TestCase):
    def test_none_has_no_graph(self) -> None:
        self.assertIsNone(gobos.node_graph_for("NONE"))
        self.assertIsNone(gobos.node_graph_for(""))
        self.assertIsNone(gobos.node_graph_for("IES"))

    def test_blinds_is_wave_bands_into_mix(self) -> None:
        graph = gobos.node_graph_for("BLINDS", scale=1.0, strength=0.8)
        self.assertIsNotNone(graph)
        assert graph is not None
        types = {node.key: node.bl_idname for node in graph.nodes}
        self.assertEqual(types["tex_coord"], "ShaderNodeTexCoord")
        self.assertEqual(types["mapping"], "ShaderNodeMapping")
        self.assertEqual(types["wave"], "ShaderNodeTexWave")
        self.assertEqual(types["ramp"], "ShaderNodeValToRGB")
        self.assertEqual(types["mix"], "ShaderNodeMixRGB")
        self.assertEqual(types["emission"], "ShaderNodeEmission")
        self.assertEqual(types["output"], "ShaderNodeOutputLight")
        self.assertEqual(graph.pattern, "WAVE")
        self.assertEqual(graph.wave_type, "BANDS")
        self.assertEqual(graph.bands_direction, "Y")
        self.assertAlmostEqual(graph.mix_fac, 0.8)
        links = {(link.from_key, link.to_key, link.to_socket) for link in graph.links}
        self.assertIn(("tex_coord", "mapping", "Vector"), links)
        self.assertIn(("wave", "ramp", "Fac"), links)
        self.assertIn(("ramp", "mix", "Color2"), links)
        self.assertIn(("mix", "emission", "Color"), links)
        self.assertIn(("emission", "output", "Surface"), links)
        self.assertLess(graph.ramp[0].color[0], 0.1)
        self.assertGreater(graph.ramp[-1].color[0], 0.9)

    def test_window_is_soft_brick_circle_is_sphere(self) -> None:
        window = gobos.node_graph_for("WINDOW")
        circle = gobos.node_graph_for("CIRCLE", strength=1.0)
        self.assertIsNotNone(window)
        self.assertIsNotNone(circle)
        assert window is not None and circle is not None
        types_w = {node.key: node.bl_idname for node in window.nodes}
        types_c = {node.key: node.bl_idname for node in circle.nodes}
        self.assertEqual(types_w["brick"], "ShaderNodeTexBrick")
        self.assertNotIn("wave", types_w)
        self.assertGreater(window.brick_mortar_smooth, 0.0)
        self.assertAlmostEqual(window.brick_offset, 0.0)
        self.assertEqual(types_c["gradient"], "ShaderNodeTexGradient")
        self.assertEqual(circle.gradient_type, "QUADRATIC_SPHERE")
        self.assertEqual(circle.mapping.location, gobos.CENTER_MAPPING_LOCATION)
        self.assertGreater(circle.ramp[0].color[0], 0.9)
        self.assertLess(circle.ramp[-1].color[0], 0.1)
        self.assertGreater(window.ramp[0].color[0], 0.9)
        self.assertLess(window.ramp[-1].color[0], 0.2)


class GoboWiringTests(unittest.TestCase):
    def test_apply_module_wires_the_spec(self) -> None:
        source = _read("behold/studio/gobo_apply.py")
        self.assertIn("node_graph_for", source)
        self.assertIn("nodes.clear()", source)
        self.assertIn("tree.nodes.new", source)
        self.assertIn("teardown_gobo", source)
        self.assertIn("apply_gobo_in_scene", source)
        self.assertIn("apply_gobo_to_object", source)
        self.assertIn("on_gobo_update", source)
        self.assertIn("get_active_behold_light", source)
        self.assertIn("NO_GOBO_TYPE", source)
        self.assertIn("GOBO_NODES_FAILED", source)
        self.assertIn("SUPPORTED_TYPES", source)
        self.assertIn("apply_preset_to_object", source)
        self.assertIn("PRESET_ID_KEY", source)
        self.assertIn("use_nodes = False", source)
        self.assertIn("ShaderNodeMix", source)

    def test_operator_and_property(self) -> None:
        ops = _read("behold/studio/operators.py")
        props = _read("behold/properties.py")
        self.assertIn('bl_idname = "behold.apply_gobo"', ops)
        self.assertIn("apply_gobo_in_scene", ops)
        self.assertIn("light_gobo_preset", props)
        self.assertIn("light_gobo_scale", props)
        self.assertIn("light_gobo_strength", props)
        self.assertIn("LIGHT_GOBO_DEFAULT", props)
        self.assertIn("light_gobo_enum_items", props)
        self.assertIn("on_gobo_update", props)
        self.assertIn("gobo_apply.apply_gobo_in_scene", ops)

    def test_shape_apply_reapplies_active_gobo(self) -> None:
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
        self.assertIn("light_gobo_preset", src)
        self.assertIn("apply_gobo_in_scene", src)

    def test_panel_gobo_row_stays_off_empty_state(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        body = _func_source(source, tree, "draw_lights_section")
        self.assertIn("EMPTY_LIGHTS", body)
        self.assertIn("draw_empty_card", body)
        self.assertIn("light_gobo_preset", body)
        self.assertIn("light_gobo_scale", body)
        self.assertIn("light_gobo_strength", body)
        self.assertIn('text="Gobo"', body)
        self.assertIn("Blinds", _read("behold/studio/gobos.py"))
        empty_idx = body.index("draw_empty_card")
        gobo_idx = body.index("light_gobo_preset")
        shape_idx = body.index("light_shape_preset")
        link_idx = body.index("behold.link_selected")
        self.assertLess(empty_idx, gobo_idx)
        self.assertLess(shape_idx, gobo_idx)
        self.assertLess(gobo_idx, body.index("light_ies_filepath"))
        self.assertLess(body.index("light_ies_filepath"), link_idx)
        self.assertNotIn("BEHOLD_PT_gobo", source)
        parked = _func_source(source, tree, "draw_light_draw_parked")
        self.assertIn("behold.apply_gobo", parked)
        self.assertIn("light_gobo_preset", parked)


if __name__ == "__main__":
    unittest.main()
