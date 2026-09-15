# SPDX-License-Identifier: GPL-3.0-or-later
"""Area-light shape presets + wiring (no Blender)."""

from __future__ import annotations

import ast
import math
import unittest

from tests.support import ROOT, load_addon_module, load_module

presets = load_module("behold/studio/light_presets.py", "behold_light_presets")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class FakeLightData:
    def __init__(self) -> None:
        self.type = "POINT"
        self.shape = "SQUARE"
        self.size = 0.4
        self.size_y = 0.4
        self.energy = 50.0
        self.spread = math.pi
        self.use_nodes = False


class PresetDefinitionTests(unittest.TestCase):
    def test_rack_order_and_labels(self) -> None:
        self.assertEqual(
            list(presets.PRESETS),
            ["SOFTBOX", "SOFTBOX_STRIP", "OCTA", "HARD_KEY", "RIM_EDGE"],
        )
        self.assertEqual(presets.DEFAULT_PRESET, "SOFTBOX")
        labels = [preset.label for preset in presets.PRESETS.values()]
        self.assertEqual(labels, ["Softbox", "Strip", "Octa", "Hard", "Rim"])
        items = presets.preset_enum_items()
        self.assertEqual(len(items), 5)
        self.assertEqual(items[0][0], "SOFTBOX")
        self.assertEqual(items[0][1], "Softbox")

    def test_shapes_map_to_cycles_area_rna(self) -> None:
        self.assertEqual(presets.PRESETS["SOFTBOX"].shape, "RECTANGLE")
        self.assertEqual(presets.PRESETS["SOFTBOX_STRIP"].shape, "RECTANGLE")
        self.assertEqual(presets.PRESETS["OCTA"].shape, "DISK")
        self.assertEqual(presets.PRESETS["HARD_KEY"].shape, "SQUARE")
        self.assertEqual(presets.PRESETS["RIM_EDGE"].shape, "RECTANGLE")
        self.assertTrue(presets.uses_size_y("RECTANGLE"))
        self.assertTrue(presets.uses_size_y("ELLIPSE"))
        self.assertFalse(presets.uses_size_y("SQUARE"))
        self.assertFalse(presets.uses_size_y("DISK"))

    def test_softbox_is_large_full_spread(self) -> None:
        soft = presets.PRESETS["SOFTBOX"]
        hard = presets.PRESETS["HARD_KEY"]
        strip = presets.PRESETS["SOFTBOX_STRIP"]
        rim = presets.PRESETS["RIM_EDGE"]
        octa = presets.PRESETS["OCTA"]
        self.assertGreater(soft.size, hard.size)
        self.assertGreater(soft.size_y, hard.size_y)
        self.assertAlmostEqual(soft.spread_deg, 180.0)
        self.assertLess(hard.spread_deg, 45.0)
        self.assertGreater(hard.energy, soft.energy)
        self.assertGreater(strip.size_y, strip.size * 3)
        self.assertGreater(rim.size_y, rim.size * 5)
        self.assertEqual(octa.shape, "DISK")
        self.assertAlmostEqual(octa.spread_deg, 180.0)

    def test_spread_is_stored_as_degrees_written_as_radians(self) -> None:
        self.assertAlmostEqual(presets.spread_radians(180.0), math.pi)
        self.assertAlmostEqual(presets.spread_radians(90.0), math.pi / 2.0)
        hard = presets.PRESETS["HARD_KEY"]
        self.assertLess(presets.spread_radians(hard.spread_deg), math.pi / 4.0)

    def test_scale_prefers_product_size(self) -> None:
        self.assertAlmostEqual(
            presets.resolve_shape_scale(product_size=0.5, current_size=2.0),
            0.5,
        )
        self.assertAlmostEqual(
            presets.resolve_shape_scale(product_size=0.0, current_size=0.8),
            0.8,
        )
        self.assertGreaterEqual(
            presets.resolve_shape_scale(product_size=0.0, current_size=0.0),
            presets.MIN_SIZE,
        )

    def test_apply_shape_props_writes_area_rna(self) -> None:
        data = FakeLightData()
        preset = presets.PRESETS["SOFTBOX"]
        written = presets.apply_shape_props(data, preset, scale=1.0)
        self.assertEqual(data.type, "AREA")
        self.assertEqual(data.shape, "RECTANGLE")
        self.assertAlmostEqual(data.size, 1.6)
        self.assertAlmostEqual(data.size_y, 1.2)
        self.assertAlmostEqual(data.energy, 250.0)
        self.assertAlmostEqual(data.spread, math.pi)
        self.assertEqual(written["nodes"], "SOFTBOX")
        self.assertTrue(written["uses_size_y"])

        hard = presets.PRESETS["HARD_KEY"]
        written_hard = presets.apply_shape_props(data, hard, scale=2.0)
        self.assertEqual(data.shape, "SQUARE")
        self.assertAlmostEqual(data.size, 0.44)
        self.assertAlmostEqual(data.energy, 800.0)
        self.assertAlmostEqual(data.spread, presets.spread_radians(35.0))
        self.assertFalse(written_hard["uses_size_y"])
        self.assertEqual(written_hard["nodes"], "NONE")

    def test_applied_and_unknown_copy(self) -> None:
        self.assertEqual(
            presets.applied_message("Softbox", "BEHOLD_Key"),
            "Applied Softbox to Key",
        )
        self.assertIn("Gobo", presets.unknown_preset_message("Gobo"))
        self.assertIn("Softbox", presets.unknown_preset_message(""))
        self.assertEqual(
            messages.unknown_light_preset_message("Gobo"),
            presets.unknown_preset_message("Gobo"),
        )
        self.assertEqual(messages.report_type(messages.UNKNOWN_LIGHT_PRESET), "ERROR")
        self.assertEqual(
            messages.report_type(messages.unknown_light_preset_message("Gobo")),
            "ERROR",
        )


class NodeGraphTests(unittest.TestCase):
    def test_hard_key_has_no_nodes(self) -> None:
        self.assertIsNone(presets.node_graph_for("NONE"))
        self.assertEqual(presets.PRESETS["HARD_KEY"].nodes, "NONE")

    def test_softbox_graph_is_centered_quadratic_sphere(self) -> None:
        graph = presets.node_graph_for("SOFTBOX")
        self.assertIsNotNone(graph)
        assert graph is not None
        types = {spec.key: spec.bl_idname for spec in graph.nodes}
        self.assertEqual(types["tex_coord"], "ShaderNodeTexCoord")
        self.assertEqual(types["gradient"], "ShaderNodeTexGradient")
        self.assertEqual(types["ramp"], "ShaderNodeValToRGB")
        self.assertEqual(types["emission"], "ShaderNodeEmission")
        self.assertEqual(types["output"], "ShaderNodeOutputLight")
        self.assertEqual(graph.gradient_type, "QUADRATIC_SPHERE")
        self.assertEqual(graph.mapping.location, presets.CENTER_MAPPING_LOCATION)
        self.assertEqual(graph.mapping.scale, presets.CENTER_MAPPING_SCALE)
        links = {(link.from_key, link.to_key, link.to_socket) for link in graph.links}
        self.assertIn(("tex_coord", "mapping", "Vector"), links)
        self.assertIn(("gradient", "ramp", "Fac"), links)
        self.assertIn(("ramp", "emission", "Color"), links)
        self.assertIn(("emission", "output", "Surface"), links)
        self.assertGreaterEqual(len(graph.ramp), 3)
        self.assertAlmostEqual(graph.ramp[0].color[0], 1.0)
        self.assertLess(graph.ramp[-1].color[0], 0.1)

    def test_strip_is_linear_octa_is_sphere(self) -> None:
        strip = presets.node_graph_for("STRIP")
        octa = presets.node_graph_for("OCTA")
        self.assertIsNotNone(strip)
        self.assertIsNotNone(octa)
        assert strip is not None and octa is not None
        self.assertEqual(strip.gradient_type, "LINEAR")
        self.assertEqual(strip.mapping.location, presets.IDENTITY_MAPPING_LOCATION)
        self.assertEqual(octa.gradient_type, "QUADRATIC_SPHERE")
        self.assertEqual(octa.mapping.location, presets.CENTER_MAPPING_LOCATION)
        self.assertEqual(presets.PRESETS["SOFTBOX_STRIP"].nodes, "STRIP")
        self.assertEqual(presets.PRESETS["RIM_EDGE"].nodes, "STRIP")
        self.assertEqual(presets.PRESETS["OCTA"].nodes, "OCTA")


class LightShapeWiringTests(unittest.TestCase):
    def test_apply_module_wires_the_spec(self) -> None:
        source = _read("behold/studio/light_shape.py")
        self.assertIn("apply_shape_props", source)
        self.assertIn("node_graph_for", source)
        self.assertIn("nodes.clear()", source)
        self.assertIn("tree.nodes.new", source)
        self.assertIn("gradient_type", source)
        self.assertIn("color_ramp", source)
        self.assertIn("elements.new", source)
        self.assertIn("ShaderNodeOutputLight", _read("behold/studio/light_presets.py"))
        self.assertIn("use_nodes = False", source)
        self.assertIn("create_if_missing", source)
        self.assertIn("add_extra_light", source)
        self.assertIn("get_active_behold_light", source)
        self.assertIn("product_frame", source)

    def test_operator_and_property(self) -> None:
        ops = _read("behold/studio/operators.py")
        props = _read("behold/properties.py")
        self.assertIn('bl_idname = "behold.apply_light_preset"', ops)
        self.assertIn("Apply to active", _read("behold/ui/panels.py"))
        self.assertIn("light_presets.preset_enum_items", ops)
        self.assertIn("apply_preset_in_scene", ops)
        self.assertIn("unknown_light_preset_message", ops)
        self.assertIn("NO_LIGHTS", ops)
        self.assertIn("light_shape_preset", props)
        self.assertIn("LIGHT_SHAPE_DEFAULT", props)
        self.assertIn("light_shape_enum_items", props)

    def test_panel_shape_row_stays_off_empty_state(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        body = _func_source(source, tree, "draw_lights_section")
        shape = _func_source(source, tree, "draw_lights_shape")
        self.assertIn("EMPTY_LIGHTS", body)
        self.assertIn("draw_empty_card", body)
        self.assertIn("draw_lights_shape", body)
        self.assertIn("light_shape_preset", shape)
        self.assertIn("behold.apply_light_preset", shape)
        self.assertIn('text="Apply to active"', shape)
        empty_idx = body.index("draw_empty_card")
        self.assertLess(empty_idx, body.index("draw_lights_shape"))
        self.assertIn("behold.add_light", body)
        self.assertIn("behold.light_draw", body)
        self.assertNotIn("Light Mixer", body)
        self.assertNotIn("key_power", body)
        self.assertNotIn("BEHOLD_PT_light_shape", source)


if __name__ == "__main__":
    unittest.main()
