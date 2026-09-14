# SPDX-License-Identifier: GPL-3.0-or-later
"""Multi-light inventory + Light Draw Active/New (no Blender)."""

from __future__ import annotations

import unittest

from tests.support import ROOT, load_module

light_ids = load_module("behold/studio/light_ids.py", "behold_light_ids")
tones = load_module("behold/studio/tones.py", "behold_studio_tones")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


class LightIdTests(unittest.TestCase):
    def test_display_strips_prefix(self) -> None:
        self.assertEqual(light_ids.display_light_name("BEHOLD_Key"), "Key")
        self.assertEqual(light_ids.display_light_name("BEHOLD_Light_001"), "Light_001")
        self.assertEqual(light_ids.display_light_name("Key"), "Key")

    def test_behold_light_name(self) -> None:
        self.assertTrue(light_ids.is_behold_light_name("BEHOLD_Key"))
        self.assertTrue(light_ids.is_behold_light_name("BEHOLD_Draw_002"))
        self.assertFalse(light_ids.is_behold_light_name("Sun"))
        self.assertFalse(light_ids.is_behold_light_name("Key"))

    def test_next_indexed_names(self) -> None:
        self.assertEqual(
            light_ids.next_indexed_name([], "Light"),
            "BEHOLD_Light_001",
        )
        self.assertEqual(
            light_ids.next_indexed_name(
                ["BEHOLD_Key", "BEHOLD_Light_001", "BEHOLD_Light_003"],
                "Light",
            ),
            "BEHOLD_Light_004",
        )
        self.assertEqual(
            light_ids.next_indexed_name(["BEHOLD_Draw_002"], "Draw"),
            "BEHOLD_Draw_003",
        )

    def test_unknown_kind_raises(self) -> None:
        with self.assertRaises(ValueError):
            light_ids.next_indexed_name([], "Spot")

    def test_reserved_rig_names(self) -> None:
        self.assertEqual(
            light_ids.RESERVED_RIG,
            ("BEHOLD_Key", "BEHOLD_Fill", "BEHOLD_Rim"),
        )


class KelvinTests(unittest.TestCase):
    def test_daylight_near_white(self) -> None:
        r, g, b = tones.kelvin_to_rgb(6500.0)
        self.assertAlmostEqual(r, 1.0, places=3)
        self.assertGreater(g, 0.9)
        self.assertGreater(b, 0.9)

    def test_warm_is_redder_than_cool(self) -> None:
        warm = tones.kelvin_to_rgb(2700.0)
        cool = tones.kelvin_to_rgb(9000.0)
        self.assertGreater(warm[0], warm[2])
        self.assertLess(warm[2], cool[2])


class MultiLightWiringTests(unittest.TestCase):
    def test_operators_register_crud(self) -> None:
        source = _read("behold/studio/operators.py")
        for bl_id in (
            "behold.build_studio",
            "behold.refresh_lights",
            "behold.add_light",
            "behold.remove_light",
            "behold.set_active_light",
        ):
            self.assertIn(f'bl_idname = "{bl_id}"', source)

    def test_properties_expose_active_new_and_target(self) -> None:
        source = _read("behold/properties.py")
        self.assertIn("active_light_name", source)
        self.assertIn("new_light_energy", source)
        self.assertIn("light_draw_target", source)
        self.assertIn('("ACTIVE", "Active"', source)
        self.assertIn('("NEW", "New"', source)

    def test_light_draw_resolves_active_vs_new(self) -> None:
        source = _read("behold/light_draw/draw_core.py")
        self.assertIn("def ensure_draw_light", source)
        self.assertIn('target == "NEW"', source)
        self.assertIn('target != "ACTIVE"', source)
        self.assertIn("add_draw_light", source)
        self.assertIn("get_active_behold_light", source)

    def test_build_studio_sets_active_key(self) -> None:
        source = _read("behold/studio/setup.py")
        self.assertIn("backdrop_tone_rgba", source)
        self.assertIn("set_active_behold_light", source)
        self.assertIn("apply_temperature_to_extras", source)
        self.assertIn("set_active_behold_camera", source)

    def test_mixer_empty_state_cancels(self) -> None:
        source = _read("behold/studio/operators.py")
        self.assertIn("No BEHOLD lights", source)
        self.assertIn("iter_behold_lights", source)


if __name__ == "__main__":
    unittest.main()
