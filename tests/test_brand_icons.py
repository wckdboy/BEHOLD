# SPDX-License-Identifier: GPL-3.0-or-later
"""Official mark files and preview wiring — no Blender import."""

from __future__ import annotations

import unittest

from tests.support import ROOT, load_module

brand = load_module("behold/brand.py", "behold.brand")


def _read(relpath: str) -> str:
    return (ROOT / relpath).read_text(encoding="utf-8")


class BrandIconTests(unittest.TestCase):
    def test_mark_and_wordmark_files_exist(self) -> None:
        self.assertTrue(brand.ICON_MARK_PATH.is_file(), brand.ICON_MARK_PATH)
        self.assertTrue(brand.ICON_LOGO_PATH.is_file(), brand.ICON_LOGO_PATH)
        self.assertTrue(brand.DOCS_LOGO_PATH.is_file(), brand.DOCS_LOGO_PATH)
        self.assertEqual(brand.ICON_MARK_PATH.name, "behold_icon.png")
        self.assertEqual(brand.ICON_LOGO_PATH.name, "behold_logo.png")
        self.assertEqual(
            brand.DOCS_LOGO_PATH.as_posix().endswith("docs/brand/behold_logo.png"),
            True,
        )
        for path in (brand.ICON_MARK_PATH, brand.ICON_LOGO_PATH, brand.DOCS_LOGO_PATH):
            header = path.read_bytes()[:8]
            self.assertEqual(header, b"\x89PNG\r\n\x1a\n", msg=path)

    def test_previews_module_loads_mark_on_register(self) -> None:
        source = _read("behold/previews.py")
        self.assertIn("bpy.utils.previews", source)
        self.assertIn("pcoll.load", source)
        self.assertIn("ICON_MARK_ID", source)
        self.assertIn("ICON_MARK_PATH", source)
        self.assertIn("def icon_id", source)
        self.assertIn("def mark_icon_kwargs", source)
        self.assertIn("def draw_mark_label", source)
        init = _read("behold/__init__.py")
        self.assertIn("from . import previews", init)
        self.assertLess(init.find("previews"), init.find("properties,"))
        self.assertIn("previews,", init)

    def test_ui_uses_mark_on_hero_prefs_pie(self) -> None:
        chrome = _read("behold/ui/chrome.py")
        prefs = _read("behold/preferences.py")
        pie = _read("behold/ui/pie.py")
        panels = _read("behold/ui/panels.py")
        self.assertIn("draw_mark_label", chrome)
        self.assertIn("draw_mark_label", prefs)
        self.assertIn("mark_icon_kwargs", pie)
        self.assertIn("wm.call_menu_pie", pie)
        self.assertIn("draw_header", panels)
        self.assertIn("mark_icon_kwargs", panels)

    def test_readme_lists_logo_paths(self) -> None:
        readme = _read("README.md")
        self.assertIn("docs/brand/behold_logo.png", readme)
        self.assertIn("behold/icons/behold_icon.png", readme)
        self.assertIn("behold/icons/behold_logo.png", readme)
        self.assertIn("AMIRITE.studio", readme)
        self.assertIn("best product-render suite for blender", readme.lower())
        self.assertIn("ROADMAP.md", readme)


if __name__ == "__main__":
    unittest.main()
