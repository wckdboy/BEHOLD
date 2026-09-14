# SPDX-License-Identifier: GPL-3.0-or-later
"""Product identity and shortcut ids — no Blender import."""

from __future__ import annotations

from pathlib import Path

PRODUCT_NAME = "BEHOLD"
PRODUCT_CREDIT = "by AMIRITE.studio"
PRODUCT_TAGLINE = "Best product-render suite for Blender"
PRODUCT_PITCH = (
    "KeyShot-simple product renders in Blender — lighting, cameras, "
    "and stills without the DCC tax."
)
VERSION = (0, 20, 0)
DOCS_URL = "https://github.com/wckdboy/BEHOLD"
RELEASES_URL = f"{DOCS_URL}/releases"

ADDON_DIR = Path(__file__).resolve().parent
ICONS_DIR = ADDON_DIR / "icons"
ICON_MARK_FILE = "behold_icon.png"
ICON_LOGO_FILE = "behold_logo.png"
ICON_MARK_PATH = ICONS_DIR / ICON_MARK_FILE
ICON_LOGO_PATH = ICONS_DIR / ICON_LOGO_FILE
DOCS_LOGO_PATH = ADDON_DIR.parent / "docs" / "brand" / "behold_logo.png"
ICON_MARK_ID = "behold_icon"
ICON_LOGO_ID = "behold_logo"

HERO_ICON = "RENDER_STILL"
PIE_MENU_ID = "BEHOLD_MT_pie"
PIE_HOTKEY_LABEL = "Shift+Alt+B"
PIE_KEY = "B"
HEADER_DRAW_FUNC = "draw_view3d_header"
