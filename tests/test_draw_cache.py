# SPDX-License-Identifier: GPL-3.0-or-later
"""Per-redraw draw cache and scene-flag reducer — no bpy."""

from __future__ import annotations

import unittest

from tests.support import ROOT, load_addon_module, load_module

draw_cache = load_module("behold/draw_cache.py", "behold_draw_cache")
scene_scan = load_addon_module("behold/ui/scene_scan.py", "behold.ui.scene_scan")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


class DrawOnceCacheTests(unittest.TestCase):
    def test_factory_runs_once_until_clear(self) -> None:
        cache = draw_cache.DrawOnceCache()
        calls = {"n": 0}

        def factory() -> int:
            calls["n"] += 1
            return calls["n"]

        self.assertEqual(cache.get_or_set("cad", factory), 1)
        self.assertEqual(cache.get_or_set("cad", factory), 1)
        self.assertEqual(cache.get_or_set("scene", factory), 2)
        cache.clear()
        self.assertEqual(cache.get_or_set("cad", factory), 3)
        self.assertEqual(calls["n"], 3)

    def test_arm_reset_registers_once_then_clears(self) -> None:
        cache = draw_cache.DrawOnceCache()
        scheduled: list[object] = []

        def register(callback: object) -> str:
            scheduled.append(callback)
            return "ok"

        self.assertTrue(cache.arm_reset(register))
        self.assertTrue(cache.arm_reset(register))
        self.assertEqual(len(scheduled), 1)
        cache.get_or_set("k", lambda: "v")
        scheduled[0]()
        self.assertFalse(cache.reset_armed)
        calls = {"n": 0}
        cache.get_or_set("k", lambda: calls.__setitem__("n", 1) or "x")
        self.assertEqual(calls["n"], 1)

    def test_arm_reset_failure_leaves_cache_unarmed(self) -> None:
        cache = draw_cache.DrawOnceCache()

        def boom(callback: object) -> None:
            del callback
            raise RuntimeError("no timers")

        self.assertFalse(cache.arm_reset(boom))
        self.assertFalse(cache.reset_armed)

    def test_memo_by_fingerprint_reuses_until_tag_changes(self) -> None:
        store: dict[str, object] = {}
        calls = {"n": 0}

        def factory() -> str:
            calls["n"] += 1
            return f"v{calls['n']}"

        self.assertEqual(draw_cache.memo_by_fingerprint(store, 2, factory), "v1")
        self.assertEqual(draw_cache.memo_by_fingerprint(store, 2, factory), "v1")
        self.assertEqual(draw_cache.memo_by_fingerprint(store, 3, factory), "v2")
        self.assertEqual(calls["n"], 2)


class SceneSnapTests(unittest.TestCase):
    def test_empty_scene(self) -> None:
        snap = scene_scan.snap_from_rows((), has_scene_camera=False)
        self.assertFalse(snap.has_product)
        self.assertFalse(snap.has_studio)
        self.assertFalse(snap.has_look)
        self.assertFalse(snap.has_camera)
        self.assertFalse(snap.has_selected_mesh)
        self.assertFalse(snap.has_imported_product)

    def test_studio_only_is_not_a_product(self) -> None:
        snap = scene_scan.snap_from_rows(
            (
                scene_scan.ObjectDrawRow(
                    name="BEHOLD_Cyclorama", ob_type="MESH"
                ),
                scene_scan.ObjectDrawRow(
                    name="BEHOLD_Key",
                    ob_type="LIGHT",
                    is_behold_light=True,
                ),
            ),
            has_scene_camera=False,
        )
        self.assertFalse(snap.has_product)
        self.assertTrue(snap.has_studio)
        self.assertFalse(snap.has_camera)

    def test_tagged_or_non_studio_mesh_is_product(self) -> None:
        tagged = scene_scan.snap_from_rows(
            (
                scene_scan.ObjectDrawRow(
                    name="BEHOLD_Cyclorama",
                    ob_type="MESH",
                    tagged_product=True,
                ),
            ),
            has_scene_camera=False,
        )
        self.assertTrue(tagged.has_product)
        self.assertTrue(tagged.has_tagged_product)
        housing = scene_scan.snap_from_rows(
            (scene_scan.ObjectDrawRow(name="housing", ob_type="MESH"),),
            has_scene_camera=True,
        )
        self.assertTrue(housing.has_product)
        self.assertTrue(housing.has_camera)
        self.assertFalse(housing.has_tagged_product)

    def test_look_selected_and_behold_camera(self) -> None:
        snap = scene_scan.snap_from_rows(
            (
                scene_scan.ObjectDrawRow(
                    name="housing",
                    ob_type="MESH",
                    has_look=True,
                    selected=True,
                ),
                scene_scan.ObjectDrawRow(
                    name="BEHOLD_Camera",
                    ob_type="CAMERA",
                    is_behold_camera=True,
                ),
            ),
            has_scene_camera=False,
        )
        self.assertTrue(snap.has_look)
        self.assertTrue(snap.has_selected_mesh)
        self.assertTrue(snap.has_camera)
        self.assertTrue(snap.has_product)
        self.assertFalse(snap.has_studio)


class DrawPathWiringTests(unittest.TestCase):
    def test_panels_use_draw_once_cad_and_scene_snap(self) -> None:
        panels = _read("behold/ui/panels.py")
        chrome = _read("behold/ui/chrome.py")
        detect = _read("behold/cad/detect.py")
        self.assertIn("cad_status_for_draw", panels)
        self.assertNotIn("cad_detect.cad_status()", panels)
        self.assertIn("scene_snap_from_context", panels)
        self.assertNotIn("product_targets(context)", panels)
        self.assertIn("scene_snap_from_context", chrome)
        self.assertIn("snap_from_rows", chrome)
        self.assertIn("draw_get", chrome)
        self.assertIn("CAD_STATUS_KEY", detect)
        self.assertIn("invalidate_cad_status_cache", detect)
        self.assertIn("addon_utils.modules", detect)
        self.assertIn("cad_status_for_draw", detect)

    def test_operators_still_probe_cad_status_fresh(self) -> None:
        ops = _read("behold/cad/operators.py")
        self.assertIn("detect.cad_status()", ops)
        self.assertIn("ensure_stepper_enabled", ops)
        self.assertNotIn("cad_status_for_draw", ops)


if __name__ == "__main__":
    unittest.main()
