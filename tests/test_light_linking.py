# SPDX-License-Identifier: GPL-3.0-or-later
"""Light / shadow linking helpers + wiring (no Blender)."""

from __future__ import annotations

import ast
import unittest

from tests.support import ROOT, load_addon_module, load_module

linking = load_addon_module(
    "behold/studio/light_linking.py", "behold.studio.light_linking"
)
messages = load_addon_module("behold/ui/messages.py", "behold.ui.messages")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


def _func_source(source: str, tree: ast.Module, name: str) -> str:
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node) or ""
    raise AssertionError(f"missing function {name}")


class FakeLinking:
    def __init__(self, state: str = "INCLUDE") -> None:
        self.link_state = state


class FakeEntry:
    def __init__(self, name: str, state: str = "INCLUDE") -> None:
        self.name = name
        self.light_linking = FakeLinking(state)


class FakeObject:
    def __init__(self, name: str) -> None:
        self.name = name


class FakeCollection:
    def __init__(self, members: dict[str, str]) -> None:
        self.objects = [FakeObject(name) for name in members]
        self.collection_objects = {
            name: FakeEntry(name, state) for name, state in members.items()
        }


class KindAndCollectionTests(unittest.TestCase):
    def test_enum_and_rna_attr(self) -> None:
        items = linking.kind_enum_items()
        self.assertEqual([item[0] for item in items], ["LIGHT", "SHADOW"])
        self.assertEqual(linking.DEFAULT_KIND, "LIGHT")
        self.assertEqual(linking.collection_attr("LIGHT"), "receiver_collection")
        self.assertEqual(linking.collection_attr("SHADOW"), "blocker_collection")
        self.assertEqual(linking.kind_label("LIGHT"), "light")
        self.assertEqual(linking.kind_label("SHADOW"), "shadow")
        self.assertEqual(linking.normalize_kind(""), "LIGHT")
        self.assertEqual(linking.normalize_kind("SHADOW"), "SHADOW")
        self.assertEqual(linking.normalize_kind("nope"), "LIGHT")
        self.assertTrue(linking.is_kind("LIGHT"))
        self.assertFalse(linking.is_kind("BOTH"))

    def test_owned_collection_names(self) -> None:
        self.assertEqual(linking.collection_name("BEHOLD_Key", "LIGHT"), "BEHOLD_LL_Key")
        self.assertEqual(
            linking.collection_name("BEHOLD_Rim", "SHADOW"), "BEHOLD_SL_Rim"
        )
        self.assertTrue(linking.is_owned_collection_name("BEHOLD_LL_Key"))
        self.assertTrue(linking.is_owned_collection_name("BEHOLD_SL_Fill.001"))
        self.assertFalse(linking.is_owned_collection_name("BEHOLD_Studio"))
        self.assertFalse(linking.is_owned_collection_name("Light Linking for Key"))


class CapabilityTests(unittest.TestCase):
    def test_cycles_and_eevee_are_supported(self) -> None:
        self.assertTrue(linking.is_supported_engine("CYCLES"))
        self.assertTrue(linking.is_supported_engine("BLENDER_EEVEE_NEXT"))
        self.assertTrue(linking.is_supported_engine("blender_eevee"))
        self.assertFalse(linking.is_supported_engine("BLENDER_WORKBENCH"))
        self.assertFalse(linking.is_supported_engine(""))

    def test_missing_api_engine_and_shadow(self) -> None:
        self.assertEqual(
            linking.capability_problem(
                engine="CYCLES",
                has_light_linking=False,
                has_receiver=False,
                has_blocker=False,
                kind="LIGHT",
            ),
            linking.NO_LINKING_API,
        )
        self.assertEqual(
            linking.capability_problem(
                engine="BLENDER_WORKBENCH",
                has_light_linking=True,
                has_receiver=True,
                has_blocker=True,
                kind="LIGHT",
            ),
            linking.NO_LINKING_ENGINE,
        )
        self.assertEqual(
            linking.capability_problem(
                engine="CYCLES",
                has_light_linking=True,
                has_receiver=True,
                has_blocker=False,
                kind="SHADOW",
            ),
            linking.NO_SHADOW_API,
        )
        self.assertIsNone(
            linking.capability_problem(
                engine="CYCLES",
                has_light_linking=True,
                has_receiver=True,
                has_blocker=True,
                kind="LIGHT",
            )
        )
        self.assertIsNone(
            linking.capability_problem(
                engine="CYCLES",
                has_light_linking=True,
                has_receiver=True,
                has_blocker=True,
                kind="SHADOW",
            )
        )
        self.assertTrue(
            linking.linking_api_ok(has_light_linking=True, has_receiver=True)
        )
        self.assertFalse(
            linking.linking_api_ok(has_light_linking=True, has_receiver=False)
        )
        self.assertTrue(linking.shadow_api_ok(has_blocker=True))
        self.assertFalse(linking.shadow_api_ok(has_blocker=False))


class MemberActionTests(unittest.TestCase):
    def test_wrangler_cycle_is_include_exclude_remove(self) -> None:
        self.assertEqual(linking.cycle_link_state(None), "INCLUDE")
        self.assertEqual(linking.cycle_link_state("INCLUDE"), "EXCLUDE")
        self.assertIsNone(linking.cycle_link_state("EXCLUDE"))
        self.assertEqual(linking.cycle_link_state("weird"), "INCLUDE")

        members: dict[str, str] = {}
        members = linking.apply_member_action(members, ["Bottle"], "CYCLE")
        self.assertEqual(members, {"Bottle": "INCLUDE"})
        members = linking.apply_member_action(members, ["Bottle"], "CYCLE")
        self.assertEqual(members, {"Bottle": "EXCLUDE"})
        members = linking.apply_member_action(members, ["Bottle"], "CYCLE")
        self.assertEqual(members, {})

    def test_link_exclude_unlink_and_solo(self) -> None:
        members = linking.apply_member_action({}, ["A", "B"], "LINK")
        self.assertEqual(members, {"A": "INCLUDE", "B": "INCLUDE"})
        members = linking.apply_member_action(members, ["B"], "EXCLUDE")
        self.assertEqual(members["B"], "EXCLUDE")
        members = linking.apply_member_action(members, ["A"], "UNLINK")
        self.assertEqual(members, {"B": "EXCLUDE"})
        self.assertEqual(
            linking.solo_members(["Product", "BEHOLD_Cyclorama"]),
            {"Product": "INCLUDE", "BEHOLD_Cyclorama": "INCLUDE"},
        )
        self.assertEqual(linking.apply_member_action(members, ["Z"], "SOLO"), members)

    def test_collection_sync_plan(self) -> None:
        to_link, to_unlink, updates = linking.plan_collection_sync(
            {"Old": "INCLUDE", "Keep": "INCLUDE"},
            {"Keep": "EXCLUDE", "New": "INCLUDE"},
        )
        self.assertEqual(to_link, ("New",))
        self.assertEqual(to_unlink, ("Old",))
        self.assertEqual(updates, {"Keep": "EXCLUDE", "New": "INCLUDE"})


class TargetFilterTests(unittest.TestCase):
    def test_skips_emitter_and_lights(self) -> None:
        self.assertFalse(
            linking.is_link_target(
                name="BEHOLD_Key", ob_type="LIGHT", emitter_name="BEHOLD_Key"
            )
        )
        self.assertFalse(
            linking.is_link_target(
                name="Sun", ob_type="LIGHT", emitter_name="BEHOLD_Key"
            )
        )
        self.assertFalse(
            linking.is_link_target(
                name="BEHOLD_Camera", ob_type="CAMERA", emitter_name="BEHOLD_Key"
            )
        )
        self.assertTrue(
            linking.is_link_target(
                name="Bottle", ob_type="MESH", emitter_name="BEHOLD_Key"
            )
        )

    def test_selected_and_product_preference(self) -> None:
        rows = (
            linking.ObjectRow("BEHOLD_Key", "LIGHT", selected=True),
            linking.ObjectRow("Bottle", "MESH", selected=True),
            linking.ObjectRow("BEHOLD_Cyclorama", "MESH", selected=True),
            linking.ObjectRow("Cap", "MESH", tagged_product=True),
        )
        self.assertEqual(
            linking.selected_target_names(rows, emitter_name="BEHOLD_Key"),
            ("Bottle", "BEHOLD_Cyclorama"),
        )
        self.assertEqual(linking.product_target_names(rows), ("Bottle",))
        tagged_only = (
            linking.ObjectRow("BEHOLD_Cyclorama", "MESH"),
            linking.ObjectRow("Housing", "MESH", tagged_product=True),
        )
        self.assertEqual(linking.product_target_names(tagged_only), ("Housing",))
        scene_only = (
            linking.ObjectRow("BEHOLD_Cyclorama", "MESH"),
            linking.ObjectRow("BEHOLD_ShadowCatcher", "MESH"),
            linking.ObjectRow("Widget", "MESH"),
        )
        self.assertEqual(linking.product_target_names(scene_only), ("Widget",))
        self.assertEqual(linking.product_target_names(()), ())


class CollectionDuckTypeTests(unittest.TestCase):
    def test_read_and_write_link_state(self) -> None:
        coll = FakeCollection({"Bottle": "INCLUDE", "Sweep": "EXCLUDE"})
        self.assertEqual(
            linking.members_from_collection(coll),
            {"Bottle": "INCLUDE", "Sweep": "EXCLUDE"},
        )
        entry = linking.lookup_collection_entry(coll, "Sweep")
        self.assertIsNotNone(entry)
        self.assertEqual(linking.entry_state(entry), "EXCLUDE")
        self.assertTrue(linking.set_entry_state(entry, "INCLUDE"))
        self.assertEqual(linking.entry_state(entry), "INCLUDE")
        self.assertEqual(linking.members_from_collection(None), {})
        self.assertEqual(linking.entry_state(None), "INCLUDE")


class CopyTests(unittest.TestCase):
    def test_sentence_plus_next_step(self) -> None:
        self.assertIn(" — ", linking.NO_LINKING_API)
        self.assertIn("Link Selected", linking.NO_LINKING_API)
        self.assertIn("Cycles", linking.NO_LINKING_ENGINE)
        self.assertIn("5.2", linking.NO_SHADOW_API)
        self.assertIn("Solo product", linking.NO_SELECTION)
        self.assertIn("Import Product", linking.NO_PRODUCT_TO_SOLO)
        self.assertEqual(messages.NO_LINKING_API, linking.NO_LINKING_API)
        self.assertEqual(messages.NO_SELECTION, linking.NO_SELECTION)
        self.assertEqual(messages.report_type(linking.NO_LINKING_ENGINE), "WARNING")
        self.assertEqual(messages.report_type(linking.NO_SHADOW_API), "WARNING")
        self.assertEqual(messages.report_type(linking.NO_PRODUCT_TO_SOLO), "WARNING")
        self.assertEqual(messages.report_type(linking.LINKING_FAILED), "ERROR")
        self.assertEqual(
            linking.linked_message("LIGHT", "BEHOLD_Key", 2, "INCLUDE"),
            "Linked 2 object(s) to Key (light)",
        )
        self.assertEqual(
            linking.linked_message("SHADOW", "BEHOLD_Rim", 1, "EXCLUDE"),
            "Excluded 1 object(s) from Rim (shadow)",
        )
        self.assertEqual(
            linking.unlinked_message("LIGHT", "BEHOLD_Key", 0, cleared=True),
            "Cleared light linking on Key",
        )
        self.assertEqual(
            linking.unlinked_message("LIGHT", "BEHOLD_Key", 2, cleared=False),
            "Unlinked 2 object(s) from Key (light)",
        )
        self.assertEqual(
            linking.solo_message("BEHOLD_Key", 1, kinds=("LIGHT", "SHADOW")),
            "Solo 1 product object(s) on Key (light + shadow)",
        )
        self.assertIn("excluded", linking.cycled_message("LIGHT", "BEHOLD_Key", {"A": "EXCLUDE"}))
        self.assertIn(
            "Unlinked selected",
            linking.cycled_message("LIGHT", "BEHOLD_Key", {}),
        )


class WiringTests(unittest.TestCase):
    def test_operators_and_property(self) -> None:
        ops = _read("behold/studio/operators.py")
        props = _read("behold/properties.py")
        apply = _read("behold/studio/light_linking_apply.py")
        spec = _read("behold/studio/light_linking.py")
        self.assertIn('bl_idname = "behold.link_selected"', ops)
        self.assertIn('bl_idname = "behold.exclude_selected"', ops)
        self.assertIn('bl_idname = "behold.unlink_selected"', ops)
        self.assertIn('bl_idname = "behold.solo_product_link"', ops)
        self.assertIn("light_linking_apply.link_selected", ops)
        self.assertIn("light_linking_apply.exclude_selected", ops)
        self.assertIn("light_linking_apply.unlink_selected", ops)
        self.assertIn("light_linking_apply.solo_product", ops)
        self.assertIn("light_linking_kind", props)
        self.assertIn("LIGHT_LINKING_DEFAULT", props)
        self.assertIn("receiver_collection", spec)
        self.assertIn("blocker_collection", spec)
        self.assertIn("collection_objects", spec)
        self.assertIn("link_state", spec)
        self.assertIn("NO_LINKING_API", spec)
        self.assertIn("NO_SHADOW_API", spec)
        self.assertIn("NO_LINKING_ENGINE", spec)
        self.assertIn("product_targets", apply)
        self.assertIn("lookup_collection_entry", apply)

    def test_lights_card_stays_off_empty_state(self) -> None:
        source = _read("behold/ui/panels.py")
        tree = ast.parse(source, filename="panels.py")
        body = _func_source(source, tree, "draw_lights_section")
        self.assertIn("EMPTY_LIGHTS", body)
        self.assertIn("draw_empty_card", body)
        self.assertIn("behold.link_selected", body)
        self.assertIn("behold.unlink_selected", body)
        self.assertIn("behold.solo_product_link", body)
        self.assertIn('text="Link Selected"', body)
        self.assertIn('text="Unlink"', body)
        self.assertIn('text="Solo product"', body)
        self.assertIn("light_linking_kind", body)
        self.assertNotIn("behold.exclude_selected", body)
        empty_idx = body.index("draw_empty_card")
        link_idx = body.index("behold.link_selected")
        self.assertLess(empty_idx, link_idx)
        self.assertLess(body.index("light_shape_preset"), link_idx)
        self.assertLess(body.index("light_gobo_preset"), link_idx)
        self.assertGreater(body.index("light_gobo_preset"), body.index("light_shape_preset"))
        self.assertLess(body.index("light_ies_filepath"), link_idx)
        self.assertGreater(body.index("light_ies_filepath"), body.index("light_gobo_preset"))
        self.assertNotIn("BEHOLD_PT_light_linking", source)


if __name__ == "__main__":
    unittest.main()
