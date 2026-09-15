# SPDX-License-Identifier: GPL-3.0-or-later
"""First-ship N-panel chrome (Percival) — no Blender import."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module, load_module

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
        self.assertIn("BEHOLD_PT_lights", self.source)
        self.assertIn("BEHOLD_PT_cameras", self.source)
        self.assertIn("BEHOLD_PT_materials", self.source)
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
                "BEHOLD_PT_lights",
                "BEHOLD_PT_materials",
                "BEHOLD_PT_cameras",
                "BEHOLD_PT_shoot",
                "BEHOLD_PT_advanced",
            ],
        )
        flow = load_addon_module("behold/ui/flow.py", "behold.ui.flow")
        self.assertEqual(tuple(names[1:]), flow.PANEL_BL_IDNAMES)
        self.assertEqual(flow.PANEL_BL_IDNAMES, flow.N_PANEL_CLASS_ORDER[1:])

    def test_main_panel_has_hero_and_flow(self) -> None:
        body = _class_source(self.source, self.tree, "BEHOLD_PT_main")
        self.assertIn("draw_hero", body)
        self.assertIn("draw_update_notice", body)
        self.assertIn("draw_flow_strip", body)
        self.assertNotIn("Light Mixer", body)

    def test_child_panels_use_shoot_last_bl_order(self) -> None:
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
        expected = flow.CHILD_PANEL_BL_ORDER
        for name, order in expected.items():
            body = _class_source(self.source, self.tree, name)
            self.assertIn(f"bl_order = CHILD_PANEL_BL_ORDER[\"{name}\"]", body)
        self.assertLess(expected["BEHOLD_PT_import"], expected["BEHOLD_PT_studio"])
        self.assertLess(expected["BEHOLD_PT_studio"], expected["BEHOLD_PT_lights"])
        self.assertLess(expected["BEHOLD_PT_lights"], expected["BEHOLD_PT_materials"])
        self.assertLess(expected["BEHOLD_PT_materials"], expected["BEHOLD_PT_cameras"])
        self.assertLess(expected["BEHOLD_PT_cameras"], expected["BEHOLD_PT_shoot"])
        self.assertLess(expected["BEHOLD_PT_shoot"], expected["BEHOLD_PT_advanced"])

    def test_advanced_defaults_closed(self) -> None:
        advanced = _class_source(self.source, self.tree, "BEHOLD_PT_advanced")
        self.assertIn("DEFAULT_CLOSED", advanced)
        self.assertIn("draw_import_parked", advanced)
        self.assertIn("draw_studio_parked", advanced)
        self.assertIn("draw_materials_parked", advanced)
        self.assertIn("draw_light_draw_parked", advanced)
        self.assertIn("draw_shoot_parked", advanced)

    def test_import_first_ship_is_picker_plus_cad_status(self) -> None:
        body = _func_source(self.source, self.tree, "draw_import_first_ship")
        self.assertIn("behold.import_product", body)
        self.assertIn("draw_cad_status_line", body)
        self.assertIn("draw_import_tessellation", body)
        self.assertIn("draw_import_cleanup", body)
        self.assertIn("cad_status_for_draw", body)
        self.assertNotIn("cad_detect.cad_status()", body)
        self.assertNotIn("import_auto_studio", body)
        self.assertNotIn("import_auto_material_assist", body)
        self.assertNotIn("behold.import_step", body)
        self.assertNotIn("occ_import_step", body)
        status = _func_source(self.source, self.tree, "draw_cad_status_line")
        self.assertIn("import_panel_copy", status)
        self.assertIn("behold.open_stepper_install", status)
        self.assertNotIn("import_auto_studio", status)
        tess = _func_source(self.source, self.tree, "draw_import_tessellation")
        self.assertIn("behold.regenerate_cad", tess)
        self.assertIn("cad_quality", tess)
        self.assertIn("cad_deflection", tess)
        cleanup = _func_source(self.source, self.tree, "draw_import_cleanup")
        self.assertIn("cad_cleanup_fillets", cleanup)
        self.assertIn("cad_cleanup_chamfers", cleanup)
        self.assertIn("cad_cleanup_holes", cleanup)
        self.assertIn("cad_blend_mm", cleanup)
        self.assertIn("cad_hole_mm", cleanup)

    def test_studio_first_ship_is_tone_and_build(self) -> None:
        body = _func_source(self.source, self.tree, "draw_studio_first_ship")
        self.assertIn("draw_studio_hdri", body)
        self.assertIn("draw_studio_bake", body)
        self.assertIn("studio_backdrop_tone", body)
        self.assertIn('text="Build"', body)
        self.assertIn("behold.build_studio", body)
        self.assertNotIn("studio_margin", body)
        self.assertNotIn("Light Mixer", body)
        self.assertNotIn("key_power", body)
        self.assertNotIn("studio_light_rig", body)
        self.assertIn("include_shadow_catcher", body)
        self.assertIn('text="Catcher"', body)
        self.assertNotIn("refresh_lights", body)
        self.assertNotIn("add_light", body)
        self.assertNotIn("light_draw_target", body)

    def test_lights_section_has_inventory_and_draw_target(self) -> None:
        body = _func_source(self.source, self.tree, "draw_lights_section")
        self.assertIn("EMPTY_LIGHTS", body)
        self.assertIn("draw_empty_card", body)
        self.assertIn("behold.add_light", body)
        self.assertIn("behold.remove_light", body)
        self.assertIn("behold.set_active_light", body)
        self.assertIn("light_draw_target", body)
        self.assertIn("behold.light_draw", body)
        self.assertIn("new_light_energy", body)
        self.assertIn("light_shape_preset", body)
        self.assertIn("behold.apply_light_preset", body)
        self.assertIn('text="Apply to active"', body)
        self.assertIn("light_gobo_preset", body)
        self.assertIn("light_gobo_scale", body)
        self.assertIn("light_ies_filepath", body)
        self.assertIn("behold.load_ies", body)
        self.assertIn("behold.clear_ies", body)
        self.assertIn("behold.link_selected", body)
        self.assertIn("behold.unlink_selected", body)
        self.assertIn("behold.solo_product_link", body)
        self.assertIn("light_linking_kind", body)
        self.assertNotIn("Light Mixer", body)
        self.assertNotIn("key_power", body)

    def test_cameras_section_has_inventory_and_frame(self) -> None:
        body = _func_source(self.source, self.tree, "draw_cameras_section")
        self.assertIn("EMPTY_CAMERAS", body)
        self.assertIn("draw_empty_card", body)
        self.assertIn("behold.add_camera", body)
        self.assertIn("behold.remove_camera", body)
        self.assertIn("behold.set_active_camera", body)
        self.assertIn("behold.frame_camera", body)
        self.assertIn("behold.clear_cameras", body)
        self.assertIn("new_camera_lens", body)
        self.assertIn("draw_cameras_dof", body)
        self.assertNotIn("Light Mixer", body)
        self.assertNotIn("batch_angles", body)
        self.assertNotIn("turntable", body)
        dof = _func_source(self.source, self.tree, "draw_cameras_dof")
        self.assertIn("dof_enabled", dof)
        self.assertIn("dof_fstop", dof)
        self.assertIn("behold.focus_product", dof)
        self.assertIn("behold.focus_selected", dof)

    def test_materials_section_has_rack_assist_and_empty_state(self) -> None:
        body = _func_source(self.source, self.tree, "draw_materials_section")
        self.assertIn("EMPTY_NO_MESH", body)
        self.assertIn("EMPTY_MATERIALS", body)
        self.assertIn("draw_empty_card", body)
        self.assertIn("behold.apply_local_material", body)
        self.assertIn("behold.cad_material_assist", body)
        self.assertIn("behold.cad_auto_dress", body)
        self.assertNotIn("blenderkit_login", body)
        self.assertNotIn("blenderkit_search", body)
        self.assertNotIn("blenderkit_apply", body)
        self.assertNotIn("Light Mixer", body)
        self.assertNotIn("batch_angles", body)

    def test_shoot_first_ship_is_draft_final_look_shots_batch_and_turntable(self) -> None:
        body = _func_source(self.source, self.tree, "draw_shoot_first_ship")
        self.assertIn('"DRAFT"', body)
        self.assertIn('"FINAL"', body)
        self.assertIn("SHOOT_ENGINE_HINT", body)
        self.assertIn('text="Still"', body)
        self.assertIn('text="Render"', body)
        self.assertIn("draw_look_compact", body)
        self.assertIn("draw_resolution_compact", body)
        self.assertIn("draw_shots_compact", body)
        self.assertIn("draw_batch_compact", body)
        self.assertIn("draw_turntable_compact", body)
        self.assertLess(body.index("draw_shots_compact"), body.index("draw_batch_compact"))
        self.assertLess(body.index("draw_batch_compact"), body.index("draw_turntable_compact"))
        self.assertNotIn("bookmark_camera", body)
        self.assertNotIn("output_directory", body)
        self.assertNotIn("frame_camera", body)
        self.assertNotIn("clear_cameras", body)
        self.assertNotIn("bake_turntable", body)
        self.assertNotIn("behold.bake_hdri", body)
        self.assertNotIn("render_turntable", body)
        self.assertNotIn("behold.focus_product", body)
        self.assertNotIn("dof_enabled", body)
        look = _func_source(self.source, self.tree, "draw_look_compact")
        self.assertIn("exposure_ev", look)
        self.assertIn("white_balance_kelvin", look)
        self.assertIn("false_color", look)
        self.assertIn("look_preset", look)
        self.assertIn("look_enabled", look)
        self.assertNotIn("batch_angles", look)
        self.assertNotIn("bookmark_camera", look)
        self.assertNotIn("apply_look", look)

    def test_turntable_compact_has_setup_play_and_empty_state(self) -> None:
        body = _func_source(self.source, self.tree, "draw_turntable_compact")
        self.assertIn("behold.setup_turntable", body)
        self.assertIn("behold.play_turntable", body)
        self.assertIn("turntable_seconds", body)
        self.assertIn("EMPTY_NO_CAMERA", body)
        self.assertIn("EMPTY_NO_PRODUCT", body)
        self.assertIn("behold.build_studio", body)
        self.assertIn("behold.add_camera", body)
        self.assertIn("behold.import_product", body)
        self.assertNotIn("batch_angles", body)
        self.assertNotIn("exposure_ev", body)
        self.assertNotIn("bake_turntable", body)
        self.assertNotIn("render_turntable", body)
        self.assertNotIn("turntable_interpolation", body)

    def test_parked_draw_keeps_mixer_batch_and_materials(self) -> None:
        studio = _func_source(self.source, self.tree, "draw_studio_parked")
        shoot = _func_source(self.source, self.tree, "draw_shoot_parked")
        materials = _func_source(self.source, self.tree, "draw_materials_parked")
        parked_import = _func_source(self.source, self.tree, "draw_import_parked")
        self.assertIn("behold.regenerate_cad", parked_import)
        self.assertIn("Apply tessellation", parked_import)
        self.assertIn("cad_quality", parked_import)
        self.assertIn("cad_cleanup_fillets", parked_import)
        self.assertIn("cad_blend_mm", parked_import)
        self.assertIn("Light Mixer", studio)
        self.assertIn("studio_margin", studio)
        self.assertIn("behold.batch_angles", shoot)
        self.assertIn("behold.bake_turntable", shoot)
        self.assertIn("behold.clear_turntable", shoot)
        self.assertIn("behold.render_turntable", shoot)
        self.assertIn("turntable_interpolation", shoot)
        self.assertNotIn("behold.setup_turntable", shoot)
        self.assertNotIn("behold.play_turntable", shoot)
        self.assertIn("behold.apply_local_material", materials)
        self.assertIn("blenderkit", materials.lower())
        self.assertIn("exposure_ev", shoot)
        self.assertIn("look_preset", shoot)
        self.assertIn("look_enabled", shoot)
        self.assertIn("behold.apply_look", shoot)
        self.assertIn("behold.apply_exposure", shoot)
        self.assertIn("behold.focus_product", shoot)
        self.assertIn("behold.focus_selected", shoot)
        self.assertIn("behold.apply_camera_dof", shoot)
        self.assertIn("behold.apply_quality", shoot)
        self.assertIn("behold.apply_resolution", shoot)
        self.assertIn("resolution_aspect", shoot)
        self.assertIn("resolution_size", shoot)
        self.assertIn("behold.apply_catcher", studio)
        self.assertIn("include_shadow_catcher", studio)
        self.assertIn("dof_enabled", shoot)
        self.assertIn("dof_fstop", shoot)

    def test_backend_keeps_final_quality_and_backdrop_tones(self) -> None:
        shoot = (ROOT / "behold" / "shoot" / "quality.py").read_text(encoding="utf-8")
        setup = (ROOT / "behold" / "studio" / "setup.py").read_text(encoding="utf-8")
        props = (ROOT / "behold" / "properties.py").read_text(encoding="utf-8")
        tones = load_module("behold/studio/tones.py", "behold_studio_tones")
        self.assertIn('"FINAL": 256', shoot)
        self.assertIn("EEVEE", shoot)
        self.assertIn("Draft = EEVEE", shoot)
        self.assertIn("backdrop_tone_rgba", setup)
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
        self.assertIn("AMIRITE.studio", text)
        self.assertIn("0.5.0", text)
        self.assertIn("0.6.0", text)
        self.assertIn("0.7.0", text)
        self.assertIn("0.8.0", text)
        self.assertIn("0.9.0", text)
        self.assertIn("0.10.0", text)
        self.assertIn("0.11.0", text)
        self.assertIn("0.12.0", text)
        self.assertIn("0.13.0", text)
        self.assertIn("0.14.0", text)
        self.assertIn("0.15.0", text)
        self.assertIn("0.16.0", text)
        self.assertIn("0.17.0", text)
        self.assertIn("0.18.0", text)
        self.assertIn("0.19.0", text)
        self.assertIn("0.21.0", text)
        self.assertIn("0.20.0", text)
        self.assertIn("0.22.0", text)
        self.assertIn("0.23.0", text)
        self.assertIn("0.24.0", text)
        self.assertIn("0.25.0", text)
        self.assertIn("1.0.0", text)
        self.assertIn("1.1.0", text)
        self.assertIn("1.2.0", text)
        self.assertIn("1.3.0", text)
        self.assertIn("1.4.0", text)
        self.assertIn("1.5.0", text)
        self.assertIn("1.5.1", text)
        self.assertIn("Auto-dress", text)
        self.assertIn("Regenerate", text)
        self.assertIn("tessellation", text.lower())
        self.assertIn("Cleanup", text)
        self.assertIn("fillet", text.lower())
        self.assertIn("First stable", text)
        self.assertIn("Square 1:1", text)
        self.assertIn("Portrait 4:5", text)
        self.assertIn("Landscape 16:9", text)
        self.assertIn("Catcher", text)
        self.assertIn("ground contact", text.lower())
        self.assertIn("EEVEE", text)
        self.assertIn("Draft = EEVEE", text)
        self.assertIn("DoF", text)
        self.assertIn("f-stop", text)
        self.assertIn("Focus on product", text)
        self.assertIn("Catalog", text)
        self.assertIn("Dramatic", text)
        self.assertIn("Batch export", text)
        self.assertIn("Bake HDRI", text)
        self.assertIn("Shot Manager", text)
        self.assertIn("Softbox", text)
        self.assertIn("Link Selected", text)
        self.assertIn("Solo product", text)
        self.assertIn("light linking", text.lower())
        self.assertIn("False Color", text)
        self.assertIn("ROADMAP.md", text)
        self.assertIn("HDRI", text)
        self.assertIn("Check for updates", text)
        self.assertIn("Lights → Materials → Cameras → Shoot", text)
        self.assertIn("Shift+Alt+B", text)
        self.assertIn("5.2", text)
        self.assertIn("4.2.0", text)
        self.assertIn("Import Product", text)
        self.assertIn("Light Draw", text)
        self.assertIn("Cameras", text)
        self.assertIn("Active", text)
        self.assertIn("BlenderKit", text)
        self.assertIn("First-ship chrome", text)
        self.assertIn("gobos", text.lower())
        self.assertIn("Blinds", text)
        self.assertIn("IES", text)
        self.assertIn("turntable", text.lower())
        self.assertIn("STEP vertical", text)
        self.assertIn("STEPper NEXT ready", text)
        self.assertIn("smoke_step_vertical.py", text)
        self.assertIn("2026-09-14", text)
        self.assertIn("2026-09-15", text)
        self.assertIn("Galahad", text)
        self.assertIn("Percival", text)
        self.assertIn("live tessellation", text.lower())
        self.assertIn("Defeaturing", text)
        self.assertIn("auto-dress", text.lower())


if __name__ == "__main__":
    unittest.main()
