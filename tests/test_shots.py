# SPDX-License-Identifier: GPL-3.0-or-later
"""Shot Manager serialize / apply helpers and wiring — no Blender import."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module

shots = load_addon_module("behold/shoot/shots.py", "behold.shoot.shots")
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")
flow = load_addon_module("behold/ui/flow.py", "behold.ui.flow")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


def _hero_src() -> dict:
    return {
        "name": "Hero chrome",
        "active_camera_name": "BEHOLD_Camera",
        "main_camera_name": "BEHOLD_Camera",
        "render_quality": "HERO",
        "turntable_seconds": 8.0,
        "hdri_filepath": "/tmp/studio.hdr",
        "hdri_strength": 1.5,
        "hdri_rotation": 45.0,
        "hdri_reflections_only": True,
        "hdri_background_strength": 0.0,
        "studio_backdrop_tone": "BLACK",
        "output_directory": "//behold_out/{quality}/{camera}/",
    }


def _pack_src() -> dict:
    return {
        "name": "Pack shot",
        "camera_name": "BEHOLD_Camera_001",
        "main_camera_name": "BEHOLD_Camera_001",
        "render_quality": "FINAL",
        "turntable_seconds": 6.0,
        "hdri_filepath": "",
        "hdri_strength": 1.0,
        "hdri_rotation": 0.0,
        "hdri_reflections_only": False,
        "hdri_background_strength": 0.0,
        "studio_backdrop_tone": "WHITE",
        "output_directory": "//behold_out/",
    }


class ShotSerializeTests(unittest.TestCase):
    def test_snapshot_roundtrip_and_schema(self) -> None:
        payload = shots.snapshot_from_mapping(_hero_src(), name="Hero chrome")
        self.assertEqual(payload["schema"], shots.SCHEMA_VERSION)
        self.assertEqual(payload["name"], "Hero chrome")
        self.assertEqual(payload["camera_name"], "BEHOLD_Camera")
        self.assertEqual(payload["render_quality"], "HERO")
        self.assertEqual(payload["turntable_seconds"], 8.0)
        self.assertEqual(payload["hdri_filepath"], "/tmp/studio.hdr")
        self.assertEqual(payload["hdri_strength"], 1.5)
        self.assertEqual(payload["hdri_rotation"], 45.0)
        self.assertTrue(payload["hdri_reflections_only"])
        self.assertEqual(payload["studio_backdrop_tone"], "BLACK")
        self.assertEqual(payload["output_directory"], "//behold_out/{quality}/{camera}/")
        self.assertTrue(shots.shot_has_hdri(payload))
        again = shots.deserialize_shot(shots.serialize_shot(payload))
        self.assertEqual(again["camera_name"], payload["camera_name"])
        self.assertEqual(again["render_quality"], "HERO")

    def test_unknown_quality_and_tone_fall_back(self) -> None:
        payload = shots.deserialize_shot(
            {"render_quality": "ULTRA", "studio_backdrop_tone": "PINK"}
        )
        self.assertEqual(payload["render_quality"], "DRAFT")
        self.assertEqual(payload["studio_backdrop_tone"], "WHITE")

    def test_unique_and_default_names(self) -> None:
        self.assertEqual(shots.unique_shot_name([], "Hero"), "Hero")
        self.assertEqual(shots.unique_shot_name(["Hero"], "Hero"), "Hero_001")
        self.assertEqual(
            shots.unique_shot_name(["Hero", "Hero_001"], "Hero"),
            "Hero_002",
        )
        self.assertEqual(
            shots.default_shot_name([], camera_name="BEHOLD_Camera"),
            "Camera",
        )
        self.assertEqual(
            shots.default_shot_name(["Camera"], camera_name="BEHOLD_Camera"),
            "Camera_001",
        )
        self.assertEqual(shots.default_shot_name([]), "Shot")

    def test_add_apply_flip_does_not_touch_mesh(self) -> None:
        stored: list[dict] = []
        hero = shots.snapshot_from_mapping(_hero_src())
        pack = shots.snapshot_from_mapping(_pack_src())
        shots.add_shot(stored, hero)
        shots.add_shot(stored, pack)
        self.assertEqual([item["name"] for item in stored], ["Hero chrome", "Pack shot"])

        dest = {
            "mesh_name": "housing",
            "render_quality": "DRAFT",
            "active_camera_name": "",
            "main_camera_name": "",
            "turntable_seconds": 6.0,
            "hdri_filepath": "",
            "hdri_strength": 1.0,
            "hdri_rotation": 0.0,
            "hdri_reflections_only": False,
            "hdri_background_strength": 0.0,
            "studio_backdrop_tone": "GREY",
            "output_directory": "//behold_out/",
        }
        first = shots.apply_shot_to_mapping(stored[0], dest)
        self.assertTrue(first["ok"])
        self.assertEqual(dest["mesh_name"], "housing")
        self.assertEqual(dest["render_quality"], "HERO")
        self.assertEqual(dest["active_camera_name"], "BEHOLD_Camera")
        self.assertEqual(dest["studio_backdrop_tone"], "BLACK")
        self.assertEqual(dest["hdri_filepath"], "/tmp/studio.hdr")
        self.assertEqual(dest["output_directory"], "//behold_out/{quality}/{camera}/")
        self.assertTrue(first["has_hdri"])
        self.assertEqual(set(first["written"]), set(shots.SCENE_APPLY_KEYS))
        self.assertNotIn("mesh_name", first["written"])

        second = shots.apply_shot_to_mapping(stored[1], dest)
        self.assertTrue(second["ok"])
        self.assertEqual(dest["mesh_name"], "housing")
        self.assertEqual(dest["render_quality"], "FINAL")
        self.assertEqual(dest["active_camera_name"], "BEHOLD_Camera_001")
        self.assertEqual(dest["studio_backdrop_tone"], "WHITE")
        self.assertEqual(dest["hdri_filepath"], "")
        self.assertFalse(second["has_hdri"])

        third = shots.snapshot_from_mapping(_hero_src(), name="Hero chrome")
        shots.add_shot(stored, third)
        self.assertEqual(stored[2]["name"], "Hero chrome_001")

        renamed = shots.rename_shot(stored, "Pack shot", "Catalog")
        self.assertTrue(renamed["ok"])
        self.assertEqual(stored[1]["name"], "Catalog")
        clash = shots.rename_shot(stored, "Catalog", "Hero chrome")
        self.assertFalse(clash["ok"])
        self.assertIn("already used", clash["message"])
        removed = shots.remove_shot(stored, "Hero chrome_001")
        self.assertTrue(removed["ok"])
        self.assertEqual(len(stored), 2)

    def test_empty_state_and_index_clamp(self) -> None:
        self.assertEqual(shots.empty_state(0), shots.EMPTY_NO_SHOTS)
        self.assertIsNone(shots.empty_state(2))
        self.assertEqual(shots.clamp_active_index(0, 3), -1)
        self.assertEqual(shots.clamp_active_index(3, 9), 2)
        self.assertEqual(shots.clamp_active_index(3, -1), 0)


class ShotWiringTests(unittest.TestCase):
    def test_properties_persist_collection_on_scene(self) -> None:
        props = _read("behold/properties.py")
        self.assertIn("class BEHOLDShotItem", props)
        self.assertIn("CollectionProperty", props)
        self.assertIn("type=BEHOLDShotItem", props)
        self.assertIn("shots: CollectionProperty", props)
        self.assertIn("active_shot_index", props)
        self.assertIn("camera_name", props)
        self.assertIn("render_quality", props)
        self.assertIn("turntable_seconds", props)
        self.assertIn("hdri_filepath", props)
        self.assertIn("hdri_strength", props)
        self.assertIn("hdri_rotation", props)
        self.assertIn("studio_backdrop_tone", props)
        self.assertIn("output_directory", props)
        self.assertIn("CLASSES = (BEHOLDShotItem, BEHOLDSceneSettings)", props)

    def test_operators_register_crud(self) -> None:
        source = _read("behold/shoot/operators.py")
        for bl_id in (
            "behold.add_shot",
            "behold.apply_shot",
            "behold.remove_shot",
            "behold.rename_shot",
        ):
            self.assertIn(f'bl_idname = "{bl_id}"', source)
        self.assertIn("shots_apply.add_shot_from_scene", source)
        self.assertIn("shots_apply.apply_shot_to_scene", source)
        self.assertIn("shots_apply.remove_shot_from_scene", source)
        self.assertIn("shots_apply.rename_shot_on_scene", source)
        apply = _read("behold/shoot/shots_apply.py")
        self.assertIn("apply_shot_to_mapping", apply)
        self.assertIn("apply_payload_to_scene", apply)
        self.assertIn("set_active_behold_camera", apply)
        self.assertIn("apply_hdri_from_settings", apply)
        self.assertIn("setup_solid_world", apply)
        self.assertIn("backdrop_tone_rgba", apply)
        self.assertIn("BEHOLD_Sweep", apply)
        self.assertNotIn("bpy.data.meshes.remove", apply)
        self.assertNotIn("remove_studio_backdrops", apply)
        self.assertNotIn("build_studio", apply)

    def test_shoot_panel_keeps_compact_shot_list(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        shoot = _func_source(source, tree, "draw_shoot_first_ship")
        compact = _func_source(source, tree, "draw_shots_compact")
        self.assertIn("draw_look_compact", shoot)
        self.assertIn("draw_shots_compact", shoot)
        self.assertIn("draw_batch_compact", shoot)
        self.assertIn("draw_turntable_compact", shoot)
        self.assertIn('"DRAFT"', shoot)
        self.assertIn('"FINAL"', shoot)
        self.assertNotIn("batch_angles", shoot)
        self.assertNotIn("exposure_ev", compact)
        self.assertIn("EMPTY_SHOTS", compact)
        self.assertIn("behold.add_shot", compact)
        self.assertIn("behold.apply_shot", compact)
        self.assertIn("behold.remove_shot", compact)
        self.assertIn('text="Apply"', compact)
        self.assertIn('item, "name"', compact)
        self.assertNotIn("batch_angles", compact)
        self.assertNotIn("exposure_ev", compact)
        self.assertNotIn("BEHOLD_PT_shots", source)

    def test_messages_and_empty_card(self) -> None:
        self.assertEqual(messages.NO_SHOTS, shots.EMPTY_NO_SHOTS)
        self.assertEqual(flow.EMPTY_SHOTS.title, messages.NO_SHOTS_TITLE)
        self.assertEqual(flow.EMPTY_SHOTS.hint, messages.NO_SHOTS_NEXT)
        self.assertEqual(flow.EMPTY_SHOTS.operator, "behold.add_shot")
        self.assertEqual(messages.report_type(messages.NO_SHOTS), "WARNING")
        self.assertEqual(messages.report_type(messages.NO_SHOT_TO_APPLY), "WARNING")
        self.assertEqual(messages.report_type(messages.SHOT_NAME_EMPTY), "WARNING")
        self.assertEqual(
            messages.report_type(messages.shot_name_taken("Hero")),
            "WARNING",
        )
        self.assertEqual(
            messages.report_type(messages.shot_camera_missing("BEHOLD_Camera")),
            "WARNING",
        )
        self.assertIn("Hero chrome", messages.shot_applied_message("Hero chrome"))
        self.assertIn("Add from the current", messages.shot_not_found("Pack"))


if __name__ == "__main__":
    unittest.main()
