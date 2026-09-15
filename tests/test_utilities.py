# SPDX-License-Identifier: GPL-3.0-or-later
"""Utilities track: wall math, mount kits, eave sections, feature-flag gating (no bpy)."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module, load_module

flag = load_module("behold/utilities/flag.py", "behold_utilities_flag")
ids = load_module("behold/utilities/ids.py", "behold_utilities_ids")
messages = load_module("behold/utilities/messages.py", "behold_utilities_messages")
wall = load_addon_module("behold/utilities/wall.py", "behold.utilities.wall")
mounts = load_module("behold/utilities/mounts.py", "behold_utilities_mounts")
eaves = load_module("behold/utilities/eaves.py", "behold_utilities_eaves")
openscad = load_addon_module(
    "behold/utilities/openscad/__init__.py", "behold.utilities.openscad"
)
presets = load_module("behold/materials/presets.py", "behold_presets_utilities")
flow = load_addon_module("behold/ui/flow.py", "behold.ui.flow")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


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


def _panel_class_names(source: str, tree: ast.Module) -> list[str]:
    classes_assign = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "CLASSES" for t in node.targets)
    )
    return [
        elt.attr if isinstance(elt, ast.Attribute) else getattr(elt, "id", "")
        for elt in getattr(classes_assign.value, "elts", [])
    ]


class FeatureFlagTests(unittest.TestCase):
    def test_flag_defaults_off(self) -> None:
        self.assertFalse(flag.DEFAULT_ENABLE_UTILITIES)
        self.assertEqual(flag.PREF_ID, "enable_utilities")
        self.assertFalse(flag.show_utilities_panel(None))
        self.assertFalse(flag.show_utilities_panel(type("P", (), {})()))
        self.assertFalse(
            flag.show_utilities_panel(type("P", (), {"enable_utilities": False})())
        )
        self.assertTrue(
            flag.show_utilities_panel(type("P", (), {"enable_utilities": True})())
        )

    def test_gated_registration_ids(self) -> None:
        self.assertEqual(flag.gated_ui_ids(enabled=False), ())
        enabled = flag.gated_ui_ids(enabled=True)
        self.assertEqual(enabled[0], flag.PANEL_ID)
        self.assertIn(flag.OPERATOR_BUILD_WALL, enabled)
        self.assertIn(flag.OPERATOR_BUILD_LEGS, enabled)
        self.assertIn(flag.OPERATOR_BUILD_BRACKET, enabled)
        self.assertIn(flag.OPERATOR_BUILD_EAVE, enabled)
        self.assertIn(flag.OPERATOR_EXPORT_SCAD, enabled)
        self.assertNotIn(flag.PANEL_ID, flag.gated_ui_ids(enabled=False))

    def test_preference_rna_defaults_false(self) -> None:
        prefs = _read("behold/preferences.py")
        self.assertIn("enable_utilities", prefs)
        self.assertIn("default=False", prefs)
        self.assertIn("_on_enable_utilities", prefs)
        self.assertIn("utilities.sync_registration", prefs)
        chrome = _func_source(
            prefs, ast.parse(prefs), "_draw_chrome_toggles"
        )
        self.assertIn("enable_utilities", chrome)

    def test_first_ship_classes_exclude_utilities_panel(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        names = _panel_class_names(source, tree)
        self.assertNotIn(flag.PANEL_ID, names)
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
        self.assertEqual(list(flow.N_PANEL_CLASS_ORDER), names)
        self.assertNotIn(flag.PANEL_ID, flow.PANEL_BL_IDNAMES)
        self.assertNotIn(flag.PANEL_ID, source)

    def test_first_ship_draws_do_not_register_utility_operators(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        for name in (
            "draw_import_first_ship",
            "draw_studio_first_ship",
            "draw_lights_section",
            "draw_materials_section",
            "draw_cameras_section",
            "draw_shoot_first_ship",
            "draw_import_parked",
            "draw_studio_parked",
            "draw_materials_parked",
            "draw_light_draw_parked",
            "draw_shoot_parked",
        ):
            body = _func_source(source, tree, name)
            for operator_id in flag.OPERATOR_IDS:
                self.assertNotIn(operator_id, body, msg=f"{name} leaked {operator_id}")
        pie = _read("behold/ui/pie.py")
        for operator_id in flag.OPERATOR_IDS:
            self.assertNotIn(operator_id, pie)

    def test_utilities_panel_polls_flag_and_sorts_after_advanced(self) -> None:
        source = _read("behold/utilities/panel.py")
        tree = ast.parse(source, filename="panel.py")
        body = _class_source(source, tree, "BEHOLD_PT_utilities")
        self.assertIn("show_utilities_panel", body)
        self.assertIn("bl_order = 80", body)
        self.assertIn("BEHOLD_PT_main", body)
        self.assertIn("DEFAULT_CLOSED", body)
        self.assertGreater(80, flow.CHILD_PANEL_BL_ORDER["BEHOLD_PT_advanced"])
        self.assertIn("behold.build_danish_wall", body)
        self.assertIn("behold.build_balcony_legs", body)
        self.assertIn("behold.build_balcony_bracket", body)
        self.assertIn("behold.build_eave_section", body)
        self.assertIn("eave_section", body)

    def test_addon_registers_utilities_after_ui(self) -> None:
        init = _read("behold/__init__.py")
        self.assertIn("from . import utilities", init)
        self.assertLess(init.index("ui,"), init.index("utilities,"))
        self.assertIn('"version": (1, 5, 0)', init)
        brand = _read("behold/brand.py")
        self.assertIn("VERSION = (1, 5, 0)", brand)


class WallMathTests(unittest.TestCase):
    def test_storey_presets(self) -> None:
        self.assertEqual(wall.thickness_mm_for_storey("MID"), 480.0)
        self.assertEqual(wall.thickness_mm_for_storey("TOP"), 360.0)
        self.assertEqual(wall.thickness_mm_for_storey("FOUNDATION"), 700.0)
        self.assertEqual(
            wall.thickness_mm_for_storey("FOUNDATION", foundation_mm=650),
            650.0,
        )
        self.assertEqual(wall.clamp_foundation_mm(500), 600.0)
        self.assertEqual(wall.clamp_foundation_mm(800), 700.0)
        self.assertEqual(
            wall.thickness_mm_for_storey("FOUNDATION", foundation_mm=500),
            600.0,
        )
        with self.assertRaises(ValueError):
            wall.thickness_mm_for_storey("ATTIC")

    def test_layers_sum_to_total(self) -> None:
        for storey in ("FOUNDATION", "MID", "TOP"):
            layers = wall.resolve_layers(storey)
            total = wall.thickness_mm_for_storey(storey)
            self.assertAlmostEqual(layers.total_mm, total)
            self.assertGreater(layers.insulation_mm, 0.0)
            self.assertGreater(layers.exterior_mm, 0.0)
            self.assertGreater(layers.interior_mm, 0.0)
        custom = wall.resolve_layers("MID", exterior_mm=200.0, interior_mm=20.0)
        self.assertAlmostEqual(custom.total_mm, 480.0)
        self.assertAlmostEqual(custom.exterior_mm, 200.0)
        self.assertAlmostEqual(custom.interior_mm, 20.0)
        self.assertAlmostEqual(custom.insulation_mm, 260.0)
        squeezed = wall.resolve_layers("TOP", exterior_mm=300.0, interior_mm=200.0)
        self.assertAlmostEqual(squeezed.total_mm, 360.0)
        self.assertGreater(squeezed.insulation_mm, 0.0)

    def test_wall_boxes_and_door_cut(self) -> None:
        solid = wall.make_wall_spec("MID", width_m=4.0, height_m=2.8)
        boxes = wall.wall_boxes(solid)
        self.assertEqual(len(boxes), 3)
        self.assertEqual({box.layer for box in boxes}, {"exterior", "insulation", "interior"})
        volume = sum(b.size_xyz[0] * b.size_xyz[1] * b.size_xyz[2] for b in boxes)
        expected = 4.0 * solid.layers.total_m * 2.8
        self.assertAlmostEqual(volume, expected, places=6)
        for box in boxes:
            self.assertLess(box.min_xyz[1] + box.size_xyz[1], 1e-9)
            self.assertLessEqual(box.min_xyz[1] + box.size_xyz[1], 0.0)

        cut = wall.make_wall_spec(
            "MID",
            width_m=4.0,
            height_m=2.8,
            include_door=True,
            door_width_m=0.9,
            door_height_m=2.1,
        )
        self.assertTrue(cut.include_door)
        door_boxes = wall.wall_boxes(cut)
        self.assertGreater(len(door_boxes), 3)
        door_volume = sum(
            b.size_xyz[0] * b.size_xyz[1] * b.size_xyz[2] for b in door_boxes
        )
        opening = 0.9 * cut.layers.total_m * 2.1
        self.assertAlmostEqual(door_volume, expected - opening, places=5)


class MountKitTests(unittest.TestCase):
    def test_legs_and_bracket_parts(self) -> None:
        spec = mounts.make_mount_spec(
            "LEGS", width_m=3.0, depth_m=1.4, deck_z=2.5, ground_z=0.0
        )
        parts = mounts.mount_parts(spec)
        names = [part.name for part in parts]
        self.assertEqual(len(parts), 8)
        self.assertTrue(any(name.startswith("Leg_") for name in names))
        self.assertTrue(any(name.startswith("BasePlate_") for name in names))
        self.assertTrue(any(name.startswith("WallBracket_") for name in names))
        fronts = [part for part in parts if part.name.startswith("Leg_")]
        for post in fronts:
            self.assertGreater(post.center[1], 1.0)
        brackets = [part for part in parts if part.name.startswith("WallBracket_")]
        for bracket in brackets:
            self.assertLess(bracket.center[1], 0.2)

        lspec = mounts.make_mount_spec(
            "BRACKET", width_m=3.0, depth_m=1.4, deck_z=2.5
        )
        lparts = mounts.mount_parts(lspec)
        lnames = [part.name for part in lparts]
        self.assertEqual(len(lparts), 6)
        self.assertTrue(any(name.startswith("LVertical_") for name in lnames))
        self.assertTrue(any(name.startswith("LHorizontal_") for name in lnames))
        self.assertTrue(any(name.startswith("LBrace_") for name in lnames))
        braces = [part for part in lparts if part.name.startswith("LBrace_")]
        self.assertTrue(any(abs(part.rotation_euler[0]) > 0.1 for part in braces))
        with self.assertRaises(ValueError):
            mounts.make_mount_spec("CABLE", width_m=3.0, depth_m=1.4, deck_z=2.5)

    def test_bounds_choose_deck_height(self) -> None:
        floating = mounts.mount_spec_from_bounds(
            "LEGS", (-1.5, 0.0, 2.4), (1.5, 1.4, 3.4)
        )
        self.assertAlmostEqual(floating.deck_z, 2.4)
        self.assertAlmostEqual(floating.width_m, 3.0)
        floor = mounts.mount_spec_from_bounds(
            "BRACKET", (-1.0, 0.0, 0.0), (1.0, 1.0, 1.0), leg_height_m=2.8
        )
        self.assertGreaterEqual(floor.deck_z, mounts.MIN_LEG_HEIGHT_M)


class EaveSectionTests(unittest.TestCase):
    def test_presets_match_snit_variants(self) -> None:
        ids = (
            "UNDER_EAVE",
            "OVER_EAVE",
            "MURKRONE_REMOVED",
            "RECESSED_SKUNK",
            "ROOF_INCLUSION",
        )
        self.assertEqual(tuple(eaves.SECTION_LABELS), ids)
        for section in ids:
            spec = eaves.make_eave_spec(section, width_m=3.0, deck_z=2.8)
            parts = eaves.eave_parts(spec)
            names = [part.name for part in parts]
            self.assertIn("Deck", names)
            self.assertIn("Gutter", names)
            self.assertIn("Roof", names)
            roof = next(part for part in parts if part.name == "Roof")
            self.assertGreater(abs(roof.rotation_euler[0]), 0.5)
            gutter = next(part for part in parts if part.name == "Gutter")
            if spec.under_eaves:
                self.assertGreater(gutter.center[1], spec.projection_m)
            else:
                self.assertLess(gutter.center[1], 0.4)
                self.assertIn("BackWall", names)
        with self.assertRaises(ValueError):
            eaves.make_eave_spec("KVISTALTAN", width_m=3.0, deck_z=2.8)

    def test_murkrone_skunk_and_inclusion(self) -> None:
        under = eaves.make_eave_spec("UNDER_EAVE", width_m=4.0, deck_z=2.8)
        under_names = [part.name for part in eaves.eave_parts(under)]
        self.assertIn("Parapet", under_names)
        self.assertNotIn("Cheek_L", under_names)

        removed = eaves.make_eave_spec("MURKRONE_REMOVED", width_m=4.0, deck_z=2.8)
        removed_names = [part.name for part in eaves.eave_parts(removed)]
        self.assertNotIn("Parapet", removed_names)
        self.assertGreater(removed.headroom_m, under.headroom_m)
        self.assertTrue(removed.under_eaves)

        skunk = eaves.make_eave_spec("RECESSED_SKUNK", width_m=4.0, deck_z=2.8)
        back = next(part for part in eaves.eave_parts(skunk) if part.name == "BackWall")
        self.assertLess(back.center[1], 0.0)
        self.assertAlmostEqual(skunk.recess_m, eaves.RECESS_SKUNK_M)
        deck = next(part for part in eaves.eave_parts(skunk) if part.name == "Deck")
        self.assertGreater(deck.size[1], skunk.projection_m)

        inclusion = eaves.make_eave_spec("ROOF_INCLUSION", width_m=4.0, deck_z=2.8)
        names = [part.name for part in eaves.eave_parts(inclusion)]
        self.assertIn("Cheek_L", names)
        self.assertIn("Cheek_R", names)
        self.assertFalse(inclusion.under_eaves)

    def test_bounds_and_pitch_clamp(self) -> None:
        spec = eaves.eave_spec_from_bounds(
            "OVER_EAVE",
            (-1.5, 0.0, 2.4),
            (1.5, 1.2, 3.4),
            deck_z=2.8,
            pitch_deg=90.0,
        )
        self.assertAlmostEqual(spec.width_m, 3.0)
        self.assertAlmostEqual(spec.projection_m, 1.2)
        self.assertEqual(spec.pitch_deg, eaves.PITCH_MAX_DEG)
        self.assertEqual(eaves.clamp_pitch_deg(10.0), eaves.PITCH_MIN_DEG)
        enum_ids = [item[0] for item in eaves.section_enum_items()]
        self.assertEqual(enum_ids, list(eaves.SECTION_LABELS))


class OpenScadAndCopyTests(unittest.TestCase):
    def test_scad_export_uses_millimetres(self) -> None:
        spec = wall.make_wall_spec("MID", include_door=True)
        text = openscad.generate_wall_stack_scad(spec)
        self.assertIn("exterior = 108", text)
        self.assertIn("danish_wall()", text)
        self.assertIn("door = true", text)
        self.assertIn("MinAltan", text)
        self.assertEqual(openscad.suggest_scad_path(""), "")
        self.assertTrue(
            openscad.suggest_scad_path("/tmp/product.blend").endswith(
                "behold_danish_wall.scad"
            )
        )
        template = _read("behold/utilities/openscad/wall_stack.scad")
        self.assertIn("module danish_wall", template)

    def test_actionable_errors(self) -> None:
        self.assertIn("Build Wall", messages.NO_WALL)
        self.assertIn("import", messages.NO_PRODUCT.lower())
        self.assertIn("preferences", messages.NO_UTILITIES.lower())
        self.assertEqual(messages.report_type(messages.NO_WALL), "WARNING")
        self.assertIn("Legs", messages.mount_built_message("Legs"))
        self.assertIn("Under eaves", messages.eave_built_message("Under eaves"))
        self.assertIn("eave preset", messages.UNKNOWN_EAVE)


class ProductIsolationTests(unittest.TestCase):
    def test_utility_meshes_are_not_the_product(self) -> None:
        self.assertTrue(ids.is_utility_mesh_name("BEHOLD_Util_Wall"))
        self.assertTrue(ids.is_utility_mesh_name("BEHOLD_Util_Wall_Exterior.001"))
        self.assertTrue(ids.is_utility_mesh_name("BEHOLD_Util_Eave"))
        self.assertTrue(ids.is_utility_mesh_name("BEHOLD_Util_Roof"))
        self.assertFalse(ids.is_utility_mesh_name("housing"))
        self.assertFalse(ids.is_utility_mesh_name("BEHOLD_Cyclorama"))
        self.assertFalse(
            flow.product_present(
                mesh_names=("BEHOLD_Util_Wall",), tagged_product=False
            )
        )
        self.assertTrue(
            flow.product_present(mesh_names=("housing",), tagged_product=False)
        )
        self.assertFalse(presets.is_dressable_mesh_name("BEHOLD_Util_Wall"))
        self.assertFalse(presets.is_dressable_mesh_name("BEHOLD_Util_Mount_Legs"))
        self.assertFalse(presets.is_dressable_mesh_name("BEHOLD_Util_Eave"))
        self.assertFalse(presets.is_dressable_mesh_name("BEHOLD_Util_Roof"))
        self.assertTrue(presets.is_dressable_mesh_name("housing_aluminum"))


class DocsTests(unittest.TestCase):
    def test_utilities_doc_covers_flag_and_presets(self) -> None:
        text = _read("docs/UTILITIES.md")
        self.assertIn("enable_utilities", text)
        self.assertIn("600–700", text)
        self.assertIn("480 mm", text)
        self.assertIn("360 mm", text)
        self.assertIn("Legs", text)
        self.assertIn("L-bracket", text)
        self.assertIn("Under eaves", text)
        self.assertIn("Over eaves", text)
        self.assertIn("Altan under tagrende", text)
        self.assertIn("Altan over tagrende", text)
        self.assertIn("Murkrone fjernet", text)
        self.assertIn("Indraget skunk", text)
        self.assertIn("Inddragelse af tag", text)
        self.assertIn("vejledende", text)
        self.assertIn("not a product release", text.lower())
        self.assertIn("1.5.0", text)
        checkpoint = _read("CHECKPOINT.md")
        self.assertIn("eave", checkpoint.lower())
        self.assertIn("not a version bump", checkpoint.lower())
        roadmap = _read("ROADMAP.md")
        self.assertIn("eave", roadmap.lower())
        self.assertIn("Logo redo", roadmap)
        readme = _read("README.md")
        self.assertIn("docs/UTILITIES.md", readme)
        self.assertIn("Utilities panel", readme)
        self.assertIn("eave", readme.lower())


if __name__ == "__main__":
    unittest.main()
