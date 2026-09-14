# SPDX-License-Identifier: GPL-3.0-or-later
"""Studio chrome: flow strip, pie, header, preferences — no Blender import."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module, load_module

flow = load_addon_module("behold/ui/flow.py", "behold.ui.flow")
brand = load_module("behold/brand.py", "behold.brand")
presets = load_module("behold/materials/presets.py", "behold_presets_chrome")
camera_ids = load_module("behold/studio/camera_ids.py", "behold_camera_ids_chrome")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _class_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing class {name}")


class FlowStripTests(unittest.TestCase):
    def test_steps_are_import_studio_dress_shoot(self) -> None:
        self.assertEqual(
            [step.id for step in flow.FLOW_STEPS],
            ["import", "studio", "dress", "shoot"],
        )
        self.assertEqual(
            flow.PANEL_BL_IDNAMES,
            (
                "BEHOLD_PT_import",
                "BEHOLD_PT_studio",
                "BEHOLD_PT_lights",
                "BEHOLD_PT_materials",
                "BEHOLD_PT_cameras",
                "BEHOLD_PT_shoot",
                "BEHOLD_PT_advanced",
            ),
        )
        self.assertLess(
            flow.PANEL_BL_IDNAMES.index("BEHOLD_PT_materials"),
            flow.PANEL_BL_IDNAMES.index("BEHOLD_PT_cameras"),
        )
        self.assertLess(
            flow.PANEL_BL_IDNAMES.index("BEHOLD_PT_cameras"),
            flow.PANEL_BL_IDNAMES.index("BEHOLD_PT_shoot"),
        )

    def test_empty_scene_starts_at_import(self) -> None:
        done = flow.flow_completed(
            has_product=False,
            has_studio=False,
            has_look=False,
            has_camera=False,
        )
        self.assertEqual(
            done,
            {
                "import": False,
                "studio": False,
                "dress": False,
                "shoot": False,
            },
        )
        self.assertEqual(flow.next_step(done), "import")
        cta = flow.cta_for_step("import")
        self.assertEqual(cta.operator, "behold.import_product")

    def test_three_click_path_advances_import_studio_shoot(self) -> None:
        after_import = flow.flow_completed(
            has_product=True,
            has_studio=False,
            has_look=False,
            has_camera=False,
        )
        self.assertEqual(flow.next_step(after_import), "studio")
        self.assertEqual(
            flow.cta_for_step("studio").operator,
            "behold.build_studio",
        )

        after_studio = flow.flow_completed(
            has_product=True,
            has_studio=True,
            has_look=False,
            has_camera=True,
        )
        self.assertEqual(flow.next_step(after_studio), "dress")
        self.assertEqual(
            flow.cta_for_step("dress").operator,
            "behold.cad_material_assist",
        )
        self.assertEqual(flow.cta_for_step("dress").label, "Assist")

        ready = flow.flow_completed(
            has_product=True,
            has_studio=True,
            has_look=True,
            has_camera=True,
        )
        self.assertIsNone(flow.next_step(ready))
        self.assertEqual(flow.cta_for_step("shoot").operator, "behold.render_still")

    def test_look_material_names_match_rack(self) -> None:
        expected = {presets.material_name_for(key) for key in presets.PRESETS}
        self.assertEqual(flow.LOOK_MATERIAL_NAMES, expected)
        self.assertTrue(flow.is_look_material_name("BEHOLD_Metal"))
        self.assertTrue(flow.is_look_material_name("BEHOLD_Glass.001"))
        self.assertFalse(flow.is_look_material_name("Principled"))

    def test_product_and_studio_presence_from_names(self) -> None:
        self.assertFalse(
            flow.product_present(mesh_names=("BEHOLD_Cyclorama",), tagged_product=False)
        )
        self.assertTrue(
            flow.product_present(mesh_names=("housing",), tagged_product=False)
        )
        self.assertTrue(
            flow.product_present(mesh_names=(), tagged_product=True)
        )
        self.assertTrue(
            flow.studio_present(
                mesh_names=("BEHOLD_Cyclorama",),
                has_behold_light=False,
            )
        )
        self.assertTrue(
            flow.studio_present(mesh_names=(), has_behold_light=True)
        )
        self.assertFalse(
            flow.studio_present(mesh_names=("housing",), has_behold_light=False)
        )
        self.assertTrue(camera_ids.is_studio_mesh_name("BEHOLD_ShadowCatcher"))
        self.assertTrue(camera_ids.is_studio_mesh_name("BEHOLD_ContactShadow"))

    def test_empty_states_have_one_primary_cta(self) -> None:
        self.assertEqual(flow.EMPTY_LIGHTS.title, "No BEHOLD lights yet")
        self.assertEqual(flow.EMPTY_LIGHTS.hint, "Build Studio or Add Light")
        self.assertEqual(flow.EMPTY_LIGHTS.operator, "behold.build_studio")
        self.assertEqual(flow.EMPTY_CAMERAS.title, "No BEHOLD cameras yet")
        self.assertEqual(flow.EMPTY_CAMERAS.hint, "Build Studio or Add Camera")
        self.assertEqual(flow.EMPTY_CAMERAS.operator, "behold.build_studio")
        self.assertEqual(flow.EMPTY_MATERIALS.title, presets.EMPTY_NO_MESH)
        self.assertEqual(flow.EMPTY_MATERIALS.operator, "behold.import_product")
        self.assertEqual(flow.EMPTY_MATERIALS.hint, presets.EMPTY_NO_MESH_HINT)
        self.assertEqual(flow.EMPTY_SHOTS.title, "No shots yet")
        self.assertEqual(flow.EMPTY_SHOTS.hint, "Add from the current camera, quality, and HDRI")
        self.assertEqual(flow.EMPTY_SHOTS.operator, "behold.add_shot")


class PieHeaderPrefsTests(unittest.TestCase):
    def test_pie_menu_and_keymap_are_registered(self) -> None:
        pie = _read("behold/ui/pie.py")
        self.assertIn("class BEHOLD_MT_pie", pie)
        self.assertIn("bl_idname = PIE_MENU_ID", pie)
        self.assertIn("behold.import_product", pie)
        self.assertIn("behold.build_studio", pie)
        self.assertIn("behold.light_draw", pie)
        self.assertIn("behold.render_still", pie)
        self.assertIn("behold.setup_turntable", pie)
        self.assertIn("wm.call_menu_pie", pie)
        self.assertIn('shift=True, alt=True', pie)
        self.assertIn("VIEW3D_HT_header", pie)
        self.assertIn("def draw_view3d_header", pie)
        self.assertEqual(flow.CHROME_IDS["pie_menu_id"], "BEHOLD_MT_pie")
        self.assertEqual(flow.CHROME_IDS["pie_hotkey"], "Shift+Alt+B")
        self.assertEqual(brand.PIE_MENU_ID, "BEHOLD_MT_pie")
        self.assertEqual(brand.PIE_HOTKEY_LABEL, "Shift+Alt+B")

    def test_ui_package_registers_pie(self) -> None:
        init = _read("behold/ui/__init__.py")
        self.assertIn("from . import panels, pie", init)
        self.assertIn("pie.register()", init)
        self.assertIn("pie.unregister()", init)

    def test_preferences_branding_and_scene_toggles(self) -> None:
        prefs = _read("behold/preferences.py")
        self.assertIn("class BEHOLDAddonPreferences", prefs)
        self.assertIn("AddonPreferences", prefs)
        self.assertIn("show_header_shortcuts", prefs)
        self.assertIn("show_flow_strip", prefs)
        self.assertIn("import_auto_studio", prefs)
        self.assertIn("render_quality", prefs)
        self.assertIn("PRODUCT_CREDIT", prefs)
        self.assertIn("DOCS_URL", prefs)
        self.assertIn("RELEASES_URL", prefs)
        self.assertIn("check_for_updates", prefs)
        self.assertIn("behold.check_updates", prefs)
        self.assertIn("behold.install_update", prefs)
        self.assertIn("AMIRITE.studio", _read("behold/brand.py"))
        self.assertIn("github.com/wckdboy/BEHOLD", _read("behold/brand.py"))
        self.assertIn("/releases", _read("behold/brand.py"))
        init = _read("behold/__init__.py")
        self.assertIn("preferences", init)
        self.assertIn('"version": (1, 0, 0)', init)

    def test_panels_have_hero_flow_and_section_icons(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        main = _class_source(source, tree, "BEHOLD_PT_main")
        self.assertIn("draw_hero", main)
        self.assertIn("draw_update_notice", main)
        self.assertIn("draw_flow_strip", main)
        for name in (
            "BEHOLD_PT_import",
            "BEHOLD_PT_studio",
            "BEHOLD_PT_lights",
            "BEHOLD_PT_materials",
            "BEHOLD_PT_cameras",
            "BEHOLD_PT_shoot",
            "BEHOLD_PT_advanced",
        ):
            body = _class_source(source, tree, name)
            self.assertIn("draw_header", body)
            self.assertIn("SECTION_ICONS", body)
        self.assertIn("draw_empty_card", source)
        self.assertIn("EMPTY_LIGHTS", source)
        self.assertIn("EMPTY_CAMERAS", source)
        self.assertIn("EMPTY_MATERIALS", source)
        self.assertIn("EMPTY_SHOTS", source)
        self.assertNotIn("bpy.types.HTML", source)
        self.assertNotIn("http.server", source)


if __name__ == "__main__":
    unittest.main()
