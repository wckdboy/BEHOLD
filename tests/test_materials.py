# SPDX-License-Identifier: GPL-3.0-or-later
"""Local PBR rack + Material Assist (no Blender)."""

from __future__ import annotations

import unittest

from tests.support import ROOT, load_module

hints = load_module("behold/cad/hints.py", "behold_hints")
presets = load_module("behold/materials/presets.py", "behold_presets")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


class FakeSocket:
    def __init__(self, value: object = None) -> None:
        self.default_value = value


class PresetRackTests(unittest.TestCase):
    def test_rack_ids_and_labels(self) -> None:
        self.assertEqual(
            list(presets.PRESETS),
            ["METAL", "PLASTIC", "RUBBER", "GLASS", "PAINT"],
        )
        self.assertEqual(presets.PRESETS["METAL"]["label"], "Metal")
        self.assertEqual(presets.PRESETS["PLASTIC"]["label"], "Plastic")
        self.assertEqual(presets.PRESETS["RUBBER"]["label"], "Rubber")
        self.assertEqual(presets.PRESETS["GLASS"]["label"], "Glass")
        self.assertEqual(presets.PRESETS["PAINT"]["label"], "Paint")

    def test_product_shot_defaults(self) -> None:
        metal = presets.PRESETS["METAL"]
        self.assertEqual(metal["metallic"], 1.0)
        self.assertLess(metal["roughness"], 0.4)
        self.assertGreater(metal["roughness"], 0.05)

        plastic = presets.PRESETS["PLASTIC"]
        self.assertEqual(plastic["metallic"], 0.0)
        self.assertGreater(plastic["roughness"], 0.2)

        rubber = presets.PRESETS["RUBBER"]
        self.assertGreater(rubber["roughness"], 0.6)
        self.assertGreater(rubber["sheen"], 0.0)

        glass = presets.PRESETS["GLASS"]
        self.assertEqual(glass["transmission"], 1.0)
        self.assertLess(glass["roughness"], 0.05)
        self.assertAlmostEqual(glass["ior"], 1.5)

        paint = presets.PRESETS["PAINT"]
        self.assertGreaterEqual(paint["coat"], 0.8)
        self.assertLess(paint["coat_roughness"], 0.2)

    def test_material_names(self) -> None:
        self.assertEqual(presets.material_name_for("METAL"), "BEHOLD_Metal")
        self.assertEqual(presets.material_name_for("GLASS"), "BEHOLD_Glass")

    def test_studio_meshes_are_not_dressable(self) -> None:
        self.assertFalse(presets.is_dressable_mesh_name("BEHOLD_Cyclorama"))
        self.assertFalse(presets.is_dressable_mesh_name("BEHOLD_ShadowCatcher.001"))
        self.assertTrue(presets.is_dressable_mesh_name("housing_aluminum"))
        self.assertTrue(presets.is_dressable_mesh_name("BEHOLD_Camera"))

    def test_empty_state(self) -> None:
        self.assertEqual(
            presets.empty_state(has_product_mesh=False),
            presets.EMPTY_NO_MESH,
        )
        self.assertIsNone(presets.empty_state(has_product_mesh=True))
        self.assertIn("Import Product", presets.EMPTY_NO_MESH)
        self.assertIn("mesh selected", presets.EMPTY_NO_MESH.lower())


class SocketAliasTests(unittest.TestCase):
    def test_writes_blender_52_socket_names(self) -> None:
        inputs = {
            "Base Color": FakeSocket(),
            "Metallic": FakeSocket(),
            "Roughness": FakeSocket(),
            "IOR": FakeSocket(),
            "Transmission Weight": FakeSocket(0.0),
            "Transmission": FakeSocket(0.0),
            "Coat Weight": FakeSocket(0.0),
            "Clearcoat": FakeSocket(0.0),
            "Coat Roughness": FakeSocket(0.0),
            "Specular IOR Level": FakeSocket(),
            "Sheen Weight": FakeSocket(),
            "Alpha": FakeSocket(),
        }
        written = presets.apply_preset_to_sockets(inputs, presets.PRESETS["GLASS"])
        self.assertEqual(written["transmission"], "Transmission Weight")
        self.assertEqual(inputs["Transmission Weight"].default_value, 1.0)
        self.assertEqual(inputs["Transmission"].default_value, 0.0)
        self.assertEqual(written["metallic"], "Metallic")
        self.assertAlmostEqual(inputs["IOR"].default_value, 1.5)

    def test_falls_back_to_42_clearcoat_and_transmission(self) -> None:
        inputs = {
            "Base Color": FakeSocket(),
            "Metallic": FakeSocket(),
            "Roughness": FakeSocket(),
            "Transmission": FakeSocket(0.0),
            "Clearcoat": FakeSocket(0.0),
            "Clearcoat Roughness": FakeSocket(0.0),
            "Specular": FakeSocket(),
        }
        written = presets.apply_preset_to_sockets(inputs, presets.PRESETS["PAINT"])
        self.assertEqual(written["coat"], "Clearcoat")
        self.assertEqual(inputs["Clearcoat"].default_value, 1.0)
        self.assertEqual(written["coat_roughness"], "Clearcoat Roughness")
        self.assertEqual(written["specular"], "Specular")
        self.assertEqual(written["transmission"], "Transmission")
        self.assertEqual(inputs["Transmission"].default_value, 0.0)

    def test_skips_missing_sockets(self) -> None:
        inputs = {"Metallic": FakeSocket()}
        written = presets.apply_preset_to_sockets(inputs, presets.PRESETS["METAL"])
        self.assertEqual(written, {"metallic": "Metallic"})
        self.assertEqual(inputs["Metallic"].default_value, 1.0)


class AssistMappingTests(unittest.TestCase):
    def test_hint_queries_map_onto_the_rack(self) -> None:
        expected = {
            "brushed aluminum": "METAL",
            "titanium metal": "METAL",
            "brushed steel": "METAL",
            "abs plastic": "PLASTIC",
            "matte rubber": "RUBBER",
            "clear glass": "GLASS",
            "matte paint": "PAINT",
            "carbon fiber": "PLASTIC",
            "wood grain": "PAINT",
            "ceramic": "PAINT",
            "leather": "RUBBER",
            hints.DEFAULT_QUERY: "METAL",
        }
        for query, preset_id in expected.items():
            self.assertEqual(presets.preset_for_query(query), preset_id, query)

    def test_filename_hints_finish_on_a_rack_id(self) -> None:
        self.assertEqual(
            presets.preset_for_query(hints.suggest_query_for_path("housing_aluminum.step")),
            "METAL",
        )
        self.assertEqual(
            presets.preset_for_query(hints.suggest_query_for_path("cap_abs.stl")),
            "PLASTIC",
        )
        self.assertEqual(
            presets.preset_for_query(hints.suggest_query_for_path("lens_glass.obj")),
            "GLASS",
        )
        self.assertEqual(
            presets.preset_for_query(hints.suggest_query_for_path("gasket_tpu.3mf")),
            "RUBBER",
        )
        self.assertEqual(
            presets.preset_for_query(hints.suggest_query_for_path("anodized_cover.step")),
            "PAINT",
        )

    def test_raw_step_names_keyword_match(self) -> None:
        self.assertEqual(presets.preset_for_query("Al6061"), "METAL")
        self.assertEqual(presets.preset_for_query("PMMA_clear"), "GLASS")
        self.assertEqual(presets.preset_for_query(""), "METAL")

    def test_plan_always_applies_local_without_blenderkit(self) -> None:
        missing = presets.plan_assist("brushed aluminum", {"installed": False, "logged_in": False})
        self.assertTrue(missing.apply_local)
        self.assertFalse(missing.search_blenderkit)
        self.assertEqual(missing.preset_id, "METAL")

        enabled = presets.plan_assist("abs plastic", {"installed": True, "logged_in": False})
        self.assertTrue(enabled.apply_local)
        self.assertFalse(enabled.search_blenderkit)
        self.assertEqual(enabled.preset_id, "PLASTIC")

        signed = presets.plan_assist("clear glass", {"installed": True, "logged_in": True})
        self.assertTrue(signed.apply_local)
        self.assertTrue(signed.search_blenderkit)
        self.assertEqual(signed.preset_id, "GLASS")

    def test_assist_summary_mentions_local_path(self) -> None:
        plan = presets.plan_assist("abs plastic", {})
        text = presets.assist_summary(plan, applied=1, searched=False)
        self.assertIn("Plastic", text)
        self.assertIn("abs plastic", text)
        self.assertIn("no BlenderKit account needed", text)
        searched = presets.assist_summary(plan, applied=2, searched=True)
        self.assertIn("searched BlenderKit", searched)


class MaterialsWiringTests(unittest.TestCase):
    def test_apply_operator_and_helpers(self) -> None:
        source = _read("behold/materials/local_rack.py")
        self.assertIn('bl_idname = "behold.apply_local_material"', source)
        self.assertIn("def apply_to_objects", source)
        self.assertIn("def dressable_meshes", source)
        self.assertIn("apply_preset_to_sockets", source)
        self.assertIn("EMPTY_NO_MESH", source)
        self.assertIn("surface_render_method", source)
        self.assertIn("use_raytrace_refraction", source)
        self.assertIn("use_screen_refraction", source)
        self.assertIn("BSDF_PRINCIPLED", source)

    def test_assist_applies_local_before_optional_search(self) -> None:
        assist = _read("behold/cad/material_assist.py")
        self.assertIn("def run_material_assist", assist)
        self.assertIn("plan_assist", assist)
        self.assertIn("apply_to_objects", assist)
        self.assertIn("blenderkit_search", assist)
        ops = _read("behold/cad/operators.py")
        self.assertIn("run_material_assist", ops)
        self.assertIn('bl_idname = "behold.cad_material_assist"', ops)
        post = _read("behold/product_import/operators.py")
        self.assertIn("run_material_assist", post)
        self.assertNotIn("Material Assist query", post)

    def test_panel_registers_materials_section(self) -> None:
        source = _read("behold/ui/panels.py")
        self.assertIn("BEHOLD_PT_materials", source)
        self.assertIn("draw_materials_section", source)
        self.assertIn("behold.apply_local_material", source)
        self.assertIn("behold.cad_material_assist", source)
        self.assertIn("EMPTY_NO_MESH", source)
        self.assertIn("no BlenderKit account needed", source)
        self.assertIn("blenderkit_search", source)
        self.assertIn("blenderkit_apply", source)
        self.assertIn("blenderkit_login", source)

    def test_blenderkit_hooks_stay_registered(self) -> None:
        source = _read("behold/materials/blenderkit_bridge.py")
        for bl_id in (
            "behold.blenderkit_login",
            "behold.blenderkit_search",
            "behold.blenderkit_apply",
        ):
            self.assertIn(f'bl_idname = "{bl_id}"', source)


if __name__ == "__main__":
    unittest.main()
