# SPDX-License-Identifier: GPL-3.0-or-later
"""First-ship N-panel chrome (Percival) — no Blender import."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_module

PANELS = ROOT / "behold" / "ui" / "panels.py"
CHECKPOINT = ROOT / "CHECKPOINT.md"


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


def _class_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing class {name}")


class FirstShipUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PANELS.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source, filename=str(PANELS))

    def test_registered_panels_are_first_ship_plus_advanced(self) -> None:
        self.assertIn("BEHOLD_PT_advanced", self.source)
        self.assertIn("BEHOLD_PT_import", self.source)
        self.assertIn("BEHOLD_PT_studio", self.source)
        self.assertIn("BEHOLD_PT_shoot", self.source)
        self.assertNotIn("BEHOLD_PT_materials", self.source)
        self.assertNotIn("BEHOLD_PT_light_draw", self.source)
        classes_assign = next(
            node
            for node in self.tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "CLASSES" for t in node.targets)
        )
        names = [
            elt.attr if isinstance(elt, ast.Attribute) else getattr(elt, "id", "")
            for elt in getattr(classes_assign.value, "elts", [])
        ]
        self.assertEqual(
            names,
            [
                "BEHOLD_PT_main",
                "BEHOLD_PT_import",
                "BEHOLD_PT_studio",
                "BEHOLD_PT_shoot",
                "BEHOLD_PT_advanced",
            ],
        )

    def test_advanced_defaults_closed(self) -> None:
        advanced = _class_source(self.source, self.tree, "BEHOLD_PT_advanced")
        self.assertIn("DEFAULT_CLOSED", advanced)
        self.assertIn("draw_import_parked", advanced)
        self.assertIn("draw_studio_parked", advanced)
        self.assertIn("draw_materials_parked", advanced)
        self.assertIn("draw_light_draw_parked", advanced)
        self.assertIn("draw_shoot_parked", advanced)

    def test_import_first_ship_is_picker_only(self) -> None:
        body = _func_source(self.source, self.tree, "draw_import_first_ship")
        self.assertIn("behold.import_product", body)
        self.assertNotIn("CAD backend", body)
        self.assertNotIn("import_auto_studio", body)
        self.assertNotIn("import_auto_material_assist", body)
        self.assertNotIn("cad_status", body)
        self.assertNotIn("behold.import_step", body)

    def test_studio_first_ship_is_tone_and_build(self) -> None:
        body = _func_source(self.source, self.tree, "draw_studio_first_ship")
        self.assertIn("studio_backdrop_tone", body)
        self.assertIn('text="Build"', body)
        self.assertIn("behold.build_studio", body)
        self.assertNotIn("Light Mixer", body)
        self.assertNotIn("key_power", body)
        self.assertNotIn("studio_light_rig", body)
        self.assertNotIn("include_shadow_catcher", body)
        self.assertNotIn("refresh_lights", body)

    def test_shoot_first_ship_is_draft_final_still_render(self) -> None:
        body = _func_source(self.source, self.tree, "draw_shoot_first_ship")
        self.assertIn('"DRAFT"', body)
        self.assertIn('"FINAL"', body)
        self.assertIn('text="Still"', body)
        self.assertIn('text="Render"', body)
        self.assertNotIn("batch_angles", body)
        self.assertNotIn("turntable", body)
        self.assertNotIn("exposure_ev", body)
        self.assertNotIn("white_balance", body)
        self.assertNotIn("bookmark_camera", body)
        self.assertNotIn("output_directory", body)

    def test_parked_draw_keeps_mixer_batch_and_materials(self) -> None:
        studio = _func_source(self.source, self.tree, "draw_studio_parked")
        shoot = _func_source(self.source, self.tree, "draw_shoot_parked")
        materials = _func_source(self.source, self.tree, "draw_materials_parked")
        self.assertIn("Light Mixer", studio)
        self.assertIn("behold.batch_angles", shoot)
        self.assertIn("behold.setup_turntable", shoot)
        self.assertIn("behold.apply_local_material", materials)
        self.assertIn("blenderkit", materials.lower())

    def test_backend_keeps_final_quality_and_backdrop_tones(self) -> None:
        shoot = (ROOT / "behold" / "shoot" / "operators.py").read_text(encoding="utf-8")
        studio = (ROOT / "behold" / "studio" / "operators.py").read_text(encoding="utf-8")
        props = (ROOT / "behold" / "properties.py").read_text(encoding="utf-8")
        tones = load_module("behold/studio/tones.py", "behold_studio_tones")
        self.assertIn('"FINAL": 256', shoot)
        self.assertIn("backdrop_tone_rgba", studio)
        self.assertIn("studio_backdrop_tone", (ROOT / "behold" / "studio" / "tones.py").read_text(encoding="utf-8"))
        self.assertIn('("WHITE", "White"', props)
        self.assertIn('("GREY", "Grey"', props)
        self.assertIn('("BLACK", "Black"', props)
        self.assertEqual(
            tones.backdrop_tone_rgba(type("S", (), {"studio_backdrop_tone": "GREY"})()),
            tones.BACKDROP_TONES["GREY"],
        )
        self.assertEqual(
            tones.backdrop_tone_rgba(type("S", (), {})()),
            tones.BACKDROP_TONES["WHITE"],
        )

    def test_checkpoint_covers_mission_and_lanes(self) -> None:
        text = CHECKPOINT.read_text(encoding="utf-8")
        self.assertIn("KeyShot-simple OSS product renders in Blender", text)
        self.assertIn("0.3.0", text)
        self.assertIn("0.3.1", text)
        self.assertIn("0.3.2", text)
        self.assertIn("4.2.0", text)
        self.assertIn("Import Product", text)
        self.assertIn("Light Draw", text)
        self.assertIn("BlenderKit", text)
        self.assertIn("First-ship chrome", text)
        self.assertIn("STEP vertical", text)
        self.assertIn("smoke_step_vertical.py", text)
        self.assertIn("PR #5", text)
        self.assertIn("cursor/behold-multi-light-5f2a", text)
        self.assertIn("2026-09-13", text)
        self.assertIn("Galahad", text)
        self.assertIn("Percival", text)
        self.assertIn("live tessellation", text.lower())
        self.assertIn("Defeaturing", text)
        self.assertIn("auto-dress", text.lower())


if __name__ == "__main__":
    unittest.main()
