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
VERSION = (2, 0, 0)
SUITE_VERSION = "2.0.0"
DOCS_URL = "https://github.com/wckdboy/BEHOLD"
RELEASES_URL = f"{DOCS_URL}/releases"

_HERE = Path(__file__).resolve().parent
# Vendored as ``<addon>/common/brand.py``; repo source lives in ``behold_common/``.
if _HERE.name == "common":
    ADDON_DIR = _HERE.parent
else:
    ADDON_DIR = _HERE
ICONS_DIR = ADDON_DIR / "icons"
ICON_MARK_FILE = "behold_icon.png"
ICON_LOGO_FILE = "behold_logo.png"
ICON_MARK_PATH = ICONS_DIR / ICON_MARK_FILE
ICON_LOGO_PATH = ICONS_DIR / ICON_LOGO_FILE

_DOCS_CANDIDATES = (
    ADDON_DIR.parent / "docs" / "brand" / ICON_LOGO_FILE,
    ADDON_DIR.parent.parent / "docs" / "brand" / ICON_LOGO_FILE,
    ICONS_DIR / ICON_LOGO_FILE,
)
DOCS_LOGO_PATH = next((path for path in _DOCS_CANDIDATES if path.is_file()), _DOCS_CANDIDATES[-1])
ICON_MARK_ID = "behold_icon"
ICON_LOGO_ID = "behold_logo"

HERO_ICON = "RENDER_STILL"
PIE_MENU_ID = "BEHOLD_MT_pie"
PIE_HOTKEY_LABEL = "Shift+Alt+B"
PIE_KEY = "B"
HEADER_DRAW_FUNC = "draw_view3d_header"

PACKAGE_SLUGS = ("studio", "lighting", "product", "utilities")
ZIP_STEMS = tuple(f"behold-{slug}" for slug in PACKAGE_SLUGS)


def package_slug_from(package: str | None) -> str:
    """``studio`` / ``lighting`` / ``product`` / ``utilities`` from a module package."""
    parts = [part for part in (package or "").split(".") if part]
    for part in parts:
        if part.startswith("behold_") and part != "behold_common":
            slug = part.removeprefix("behold_")
            if slug in PACKAGE_SLUGS:
                return slug
    return "product"


def zip_stem_from(package: str | None) -> str:
    return f"behold-{package_slug_from(package)}"
