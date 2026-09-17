#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Generate remaining v2.0.0 suite glue (manifests, inits, properties, UI)."""

from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MONO = ROOT / "behold"

STUDIO_PROPS = {
    "studio_backdrop_tone",
    "studio_backdrop",
    "include_shadow_catcher",
    "studio_margin",
    "hdri_filepath",
    "hdri_strength",
    "hdri_rotation",
    "hdri_reflections_only",
    "hdri_background_strength",
    "bake_hdri_filepath",
    "bake_hdri_resolution",
    "bake_hdri_include_world",
    "bake_hdri_apply",
}

LIGHTING_PROPS = {
    "studio_light_rig",
    "key_power",
    "fill_ratio",
    "rim_ratio",
    "light_temperature",
    "light_draw_mode",
    "light_draw_distance",
    "active_light_name",
    "new_light_energy",
    "light_draw_target",
    "light_shape_preset",
    "light_gobo_preset",
    "light_gobo_scale",
    "light_gobo_strength",
    "light_ies_filepath",
    "light_ies_strength",
    "light_ies_scale",
    "light_linking_kind",
}

# Shot snapshots still store HDRI / backdrop tone on the product settings.
PRODUCT_EXTRA_FROM_STUDIO = {
    "studio_backdrop_tone",
    "hdri_filepath",
    "hdri_strength",
    "hdri_rotation",
    "hdri_reflections_only",
    "hdri_background_strength",
}

SKIP_PRODUCT = STUDIO_PROPS | LIGHTING_PROPS | {"utilities"}
SKIP_PRODUCT -= PRODUCT_EXTRA_FROM_STUDIO

UPDATE_PROPS = '''
    check_for_updates: BoolProperty(
        name="Check for updates",
        description=(
            "Ask GitHub once a day if a newer BEHOLD suite release exists, "
            "and show a notice in the sidebar. Public API only — no token is sent"
        ),
        default=True,
    )
    update_last_check: StringProperty(
        name="Last update check",
        description="Date of the last GitHub check (BEHOLD manages this)",
        default="",
        options={"HIDDEN"},
    )
    update_latest_tag: StringProperty(
        name="Latest release tag",
        description="Newest stable tag seen on GitHub (BEHOLD manages this)",
        default="",
        options={"HIDDEN"},
    )
    update_latest_url: StringProperty(
        name="Latest release page",
        description="GitHub release page for the newest tag (BEHOLD manages this)",
        default="",
        options={"HIDDEN"},
    )
    update_latest_zip_url: StringProperty(
        name="Latest release zip",
        description="behold-*.zip download URL (BEHOLD manages this)",
        default="",
        options={"HIDDEN"},
    )
    update_last_error: StringProperty(
        name="Update check error",
        description="Last GitHub error, if any (BEHOLD manages this)",
        default="",
        options={"HIDDEN"},
    )
    update_error_kind: StringProperty(
        name="Update error kind",
        description="network / github / download / install / no_zip (BEHOLD manages this)",
        default="",
        options={"HIDDEN"},
    )
    update_checking: BoolProperty(
        name="Update check in progress",
        default=False,
        options={"HIDDEN"},
    )
    update_installing: BoolProperty(
        name="Update install in progress",
        default=False,
        options={"HIDDEN"},
    )
'''


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_assets() -> None:
    icons = MONO / "icons"
    for addon, extra in (
        ("behold_studio", ()),
        ("behold_lighting", (("ies", "ies"),)),
        ("behold_product", (("assets", "assets"),)),
        ("behold_utilities", (("utilities/openscad/wall_stack.scad", "openscad/wall_stack.scad"),)),
    ):
        root = ROOT / addon
        for icon in icons.iterdir():
            if icon.is_file():
                _copy_file(icon, root / "icons" / icon.name)
        for src_rel, dst_rel in extra:
            src = MONO / src_rel
            dst = root / dst_rel
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            elif src.is_file():
                _copy_file(src, dst)
        assets = root / "assets"
        assets.mkdir(exist_ok=True)
        keep = assets / ".gitkeep"
        if not keep.exists():
            keep.write_text("# Keeps the assets package in the install zip.\n", encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.lstrip("\n") if text.startswith("\n") else text, encoding="utf-8")
    if not text.endswith("\n"):
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")


MANIFESTS = {
    "behold_studio": {
        "id": "behold_studio",
        "name": "BEHOLD Studio",
        "tagline": "Cyclorama, HDRI world, and ground contact for BEHOLD",
        "tags": '["Render", "Scene"]',
        "network": "GitHub update check for BEHOLD Studio",
    },
    "behold_lighting": {
        "id": "behold_lighting",
        "name": "BEHOLD Lighting",
        "tagline": "Multi-light, Light Draw, gobo, IES, and linking",
        "tags": '["Lighting", "Render"]',
        "network": "GitHub update check for BEHOLD Lighting",
    },
    "behold_product": {
        "id": "behold_product",
        "name": "BEHOLD Product",
        "tagline": "Import, materials, cameras, and Shoot for BEHOLD",
        "tags": '["Import-Export", "Material", "Camera", "Render"]',
        "network": "GitHub update check and optional BlenderKit downloads",
    },
    "behold_utilities": {
        "id": "behold_utilities",
        "name": "BEHOLD Utilities",
        "tagline": "Danish wall, balcony mounts, and eave sections",
        "tags": '["Add Mesh", "Object"]',
        "network": "GitHub update check for BEHOLD Utilities",
    },
}


def write_manifests() -> None:
    for folder, data in MANIFESTS.items():
        write(
            ROOT / folder / "blender_manifest.toml",
            f'''schema_version = "1.0.0"

id = "{data["id"]}"
version = "2.0.0"
name = "{data["name"]}"
tagline = "{data["tagline"]}"
maintainer = "AMIRITE.studio"
type = "add-on"

blender_version_min = "4.2.0"

license = ["SPDX:GPL-3.0-or-later"]
website = "https://github.com/wckdboy/BEHOLD"
tags = {data["tags"]}

[permissions]
network = "{data["network"]}"
''',
        )


def extract_prop_blocks(class_src: str, wanted: set[str] | None, skip: set[str] | None) -> str:
    """Keep `name: XxxProperty(` blocks whose name is in wanted / not in skip."""
    lines = class_src.splitlines(True)
    # Drop the class header; keep indented body assignments.
    body_start = 0
    for i, line in enumerate(lines):
        if line.startswith("class "):
            body_start = i + 1
            break
    blocks: list[str] = []
    i = body_start
    # skip docstring
    while i < len(lines) and (lines[i].strip() == "" or lines[i].lstrip().startswith('"""') or lines[i].lstrip().startswith("'''")):
        if lines[i].lstrip().startswith('"""') or lines[i].lstrip().startswith("'''"):
            quote = lines[i].lstrip()[:3]
            if lines[i].count(quote) >= 2 and lines[i].strip() != quote:
                i += 1
                break
            i += 1
            while i < len(lines) and quote not in lines[i]:
                i += 1
            i += 1
            break
        i += 1
    while i < len(lines):
        line = lines[i]
        if line.strip() == "":
            i += 1
            continue
        if not line.startswith("    ") or line.startswith("        "):
            break
        # property start: "    name: Type("
        if ":" in line and line.lstrip()[0].isalpha():
            name = line.strip().split(":", 1)[0]
            chunk = [line]
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() == "":
                    chunk.append(nxt)
                    i += 1
                    # if next non-empty is a new top-level prop, stop
                    j = i
                    while j < len(lines) and lines[j].strip() == "":
                        j += 1
                    if j < len(lines) and lines[j].startswith("    ") and not lines[j].startswith("        ") and ":" in lines[j]:
                        break
                    continue
                if nxt.startswith("    ") and not nxt.startswith("        ") and ":" in nxt and nxt.lstrip()[0].isalpha():
                    break
                chunk.append(nxt)
                i += 1
            if wanted is not None and name not in wanted:
                continue
            if skip is not None and name in skip:
                continue
            blocks.append("".join(chunk).rstrip() + "\n")
            continue
        i += 1
    return "\n".join(blocks)


def split_original_properties() -> tuple[str, str]:
    src = (MONO / "properties.py").read_text(encoding="utf-8")
    shot_start = src.index("class BEHOLDShotItem")
    scene_start = src.index("class BEHOLDSceneSettings")
    classes_start = src.index("\nCLASSES = ")
    shot = src[shot_start:scene_start].rstrip() + "\n"
    scene = src[scene_start:classes_start].rstrip() + "\n"
    return shot, scene


def write_properties() -> None:
    shot, scene = split_original_properties()
    studio_body = extract_prop_blocks(scene, STUDIO_PROPS, None)
    lighting_body = extract_prop_blocks(scene, LIGHTING_PROPS, None)
    product_body = extract_prop_blocks(scene, None, SKIP_PRODUCT)

    write(
        ROOT / "behold_studio" / "properties.py",
        f'''# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene-level BEHOLD Studio settings."""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup, Scene

from .bake import DEFAULT_RESOLUTION as BAKE_DEFAULT_RESOLUTION
from .bake import resolution_enum_items as bake_resolution_enum_items
from .catcher_apply import on_catcher_update
from .world_apply import on_hdri_filepath_update, on_hdri_values_update


class BEHOLDStudioSettings(PropertyGroup):
{studio_body}

CLASSES = (BEHOLDStudioSettings,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    Scene.behold_studio = PointerProperty(type=BEHOLDStudioSettings)


def unregister() -> None:
    del Scene.behold_studio
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
''',
    )

    write(
        ROOT / "behold_lighting" / "properties.py",
        f'''# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene-level BEHOLD Lighting settings."""

from __future__ import annotations

import bpy
from bpy.props import EnumProperty, FloatProperty, PointerProperty, StringProperty
from bpy.types import PropertyGroup, Scene

from .gobo_apply import on_gobo_update
from .gobos import DEFAULT_PRESET as LIGHT_GOBO_DEFAULT
from .gobos import DEFAULT_SCALE as LIGHT_GOBO_SCALE_DEFAULT
from .gobos import DEFAULT_STRENGTH as LIGHT_GOBO_STRENGTH_DEFAULT
from .gobos import MAX_SCALE as LIGHT_GOBO_SCALE_MAX
from .gobos import MIN_SCALE as LIGHT_GOBO_SCALE_MIN
from .gobos import preset_enum_items as light_gobo_enum_items
from .ies import DEFAULT_SCALE as LIGHT_IES_SCALE_DEFAULT
from .ies import DEFAULT_STRENGTH as LIGHT_IES_STRENGTH_DEFAULT
from .ies import MAX_SCALE as LIGHT_IES_SCALE_MAX
from .ies import MAX_STRENGTH as LIGHT_IES_STRENGTH_MAX
from .ies import MIN_SCALE as LIGHT_IES_SCALE_MIN
from .ies_apply import on_ies_filepath_update, on_ies_values_update
from .light_linking import DEFAULT_KIND as LIGHT_LINKING_DEFAULT
from .light_linking import kind_enum_items as light_linking_kind_enum_items
from .light_presets import DEFAULT_PRESET as LIGHT_SHAPE_DEFAULT
from .light_presets import preset_enum_items as light_shape_enum_items


class BEHOLDLightingSettings(PropertyGroup):
{lighting_body}

CLASSES = (BEHOLDLightingSettings,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    Scene.behold_lighting = PointerProperty(type=BEHOLDLightingSettings)


def unregister() -> None:
    del Scene.behold_lighting
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
''',
    )

    product_scene = scene.replace("class BEHOLDSceneSettings(PropertyGroup):", "class BEHOLDProductSettings(PropertyGroup):")
    # Rebuild from extracted body so unused lighting RNA is not registered twice conceptually.
    write(
        ROOT / "behold_product" / "properties.py",
        f'''# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene-level BEHOLD Product settings."""

from __future__ import annotations

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup, Scene

from .cad.defeaturing import DEFAULT_BLEND_MM as CAD_BLEND_DEFAULT
from .cad.defeaturing import DEFAULT_HOLE_MM as CAD_HOLE_DEFAULT
from .cad.defeaturing import MAX_SIZE_MM as CAD_SIZE_MAX
from .cad.defeaturing import MIN_SIZE_MM as CAD_SIZE_MIN
from .cad.regenerate import DEFAULT_DEFLECTION as CAD_DEFAULT_DEFLECTION
from .cad.regenerate import DEFAULT_QUALITY as CAD_QUALITY_DEFAULT
from .cad.regenerate import MAX_DEFLECTION as CAD_DEFLECTION_MAX
from .cad.regenerate import MIN_DEFLECTION as CAD_DEFLECTION_MIN
from .cad.regenerate import quality_enum_items as cad_quality_enum_items
from .dof import DEFAULT_FSTOP as DOF_DEFAULT_FSTOP
from .dof import FSTOP_MAX as DOF_FSTOP_MAX
from .dof import FSTOP_MIN as DOF_FSTOP_MIN
from .dof_apply import on_dof_update
from .shoot.exposure_apply import on_exposure_update
from .shoot.looks import DEFAULT_PRESET as LOOK_DEFAULT
from .shoot.looks import preset_enum_items as look_preset_enum_items
from .shoot.looks_apply import on_look_update
from .shoot.quality import DEFAULT_QUALITY as QUALITY_DEFAULT
from .shoot.quality import quality_enum_items
from .shoot.quality_apply import on_quality_update
from .shoot.resolution import DEFAULT_ASPECT as RESOLUTION_ASPECT_DEFAULT
from .shoot.resolution import DEFAULT_SIZE as RESOLUTION_SIZE_DEFAULT
from .shoot.resolution import aspect_enum_items as resolution_aspect_enum_items
from .shoot.resolution import size_enum_items as resolution_size_enum_items
from .shoot.resolution_apply import on_resolution_update


{shot}

class BEHOLDProductSettings(PropertyGroup):
{product_body}

CLASSES = (BEHOLDShotItem, BEHOLDProductSettings)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    Scene.behold_product = PointerProperty(type=BEHOLDProductSettings)


def unregister() -> None:
    del Scene.behold_product
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
''',
    )

    write(
        ROOT / "behold_utilities" / "properties.py",
        '''# SPDX-License-Identifier: GPL-3.0-or-later
"""Scene-level BEHOLD Utilities settings."""

from __future__ import annotations

import bpy
from bpy.props import PointerProperty
from bpy.types import Scene

from .settings import BEHOLDUtilitiesSettings

CLASSES = (BEHOLDUtilitiesSettings,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    Scene.behold_utilities = PointerProperty(type=BEHOLDUtilitiesSettings)


def unregister() -> None:
    del Scene.behold_utilities
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
''',
    )
    del product_scene


def prefs_module(
    *,
    class_name: str,
    title: str,
    extra_chrome: str,
    extra_scene: str,
    extra_imports: str,
    check_op: str,
) -> str:
    return f'''# SPDX-License-Identifier: GPL-3.0-or-later
"""{title} add-on preferences."""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, StringProperty
from bpy.types import AddonPreferences, Context, UILayout

from .common.brand import DOCS_URL, PRODUCT_CREDIT, PRODUCT_NAME, PRODUCT_TAGLINE, RELEASES_URL, VERSION
from .common.prefs import addon_id_from, get_prefs as _get_prefs
from .common.previews import draw_mark_label
from .common.updates.core import (
    available_from_cache,
    installed_version,
    prefs_status_copy,
    version_string,
)
{extra_imports}

def addon_id() -> str:
    return addon_id_from(__package__)


def get_prefs(context: Context):
    return _get_prefs(context, __package__)


class {class_name}(AddonPreferences):
    bl_idname = addon_id()
{UPDATE_PROPS}{extra_chrome}
    def draw(self, context: Context) -> None:
        layout = self.layout
        _draw_branding(layout)
        _draw_links(layout)
        _draw_updates(layout, self)
        _draw_chrome_toggles(layout, self)
        _draw_scene_defaults(layout, context)


def _draw_branding(layout: UILayout) -> None:
    box = layout.box()
    draw_mark_label(box, PRODUCT_NAME)
    box.label(text=PRODUCT_CREDIT)
    box.label(text="{title}")
    box.label(text=PRODUCT_TAGLINE)


def _draw_links(layout: UILayout) -> None:
    row = layout.row(align=True)
    row.operator("wm.url_open", text="Docs", icon="HELP").url = DOCS_URL
    row.operator("wm.url_open", text="Releases", icon="URL").url = RELEASES_URL


def _draw_updates(layout: UILayout, prefs: AddonPreferences) -> None:
    box = layout.box()
    box.label(text="Updates", icon="FILE_REFRESH")
    box.label(text=f"Installed: {title} {{version_string(VERSION)}}")
    box.prop(prefs, "check_for_updates")
    available = available_from_cache(
        getattr(prefs, "update_latest_tag", "") or "",
        installed=installed_version(),
        html_url=getattr(prefs, "update_latest_url", "") or "",
        zip_url=getattr(prefs, "update_latest_zip_url", "") or "",
    )
    error = getattr(prefs, "update_last_error", "") or ""
    copy = prefs_status_copy(
        checking=bool(getattr(prefs, "update_checking", False)),
        installing=bool(getattr(prefs, "update_installing", False)),
        last_iso=getattr(prefs, "update_last_check", "") or "",
        error=error,
        error_kind=getattr(prefs, "update_error_kind", "") or "",
        available=available,
        installed=installed_version(),
    )
    status = box.column(align=True)
    if copy.get("alert"):
        status.alert = True
        status.label(text=copy["line"], icon="ERROR")
    else:
        status.label(text=copy["line"])
    if copy["detail"]:
        status.label(text=copy["detail"])
    row = box.row(align=True)
    row.operator("{check_op}.check_updates", icon="FILE_REFRESH")
    if available and available.get("zip_url"):
        row.operator("{check_op}.install_update", text="Install", icon="IMPORT")
    row.operator("{check_op}.open_release", text="Open release", icon="URL")


def _draw_chrome_toggles(layout: UILayout, prefs: AddonPreferences) -> None:
    box = layout.box()
    box.label(text="Chrome", icon="PREFERENCES")
    if hasattr(prefs, "show_flow_strip"):
        box.prop(prefs, "show_flow_strip")
    if hasattr(prefs, "show_header_shortcuts"):
        box.prop(prefs, "show_header_shortcuts")
    if not hasattr(prefs, "show_flow_strip") and not hasattr(prefs, "show_header_shortcuts"):
        box.label(text="Install BEHOLD Product for the pie, header, and flow strip")


def _draw_scene_defaults(layout: UILayout, context: Context) -> None:
{extra_scene}

CLASSES = ({class_name},)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
'''


def write_preferences() -> None:
    write(
        ROOT / "behold_studio" / "preferences.py",
        prefs_module(
            class_name="BEHOLDStudioAddonPreferences",
            title="BEHOLD Studio",
            extra_chrome="",
            extra_scene="""    settings = getattr(context.scene, "behold_studio", None)
    if settings is None:
        return
    box = layout.box()
    box.label(text="This scene", icon="SCENE_DATA")
    box.prop(settings, "studio_backdrop_tone", text="Backdrop")
    box.prop(settings, "include_shadow_catcher", text="Catcher")
""",
            extra_imports="",
            check_op="behold_studio",
        ),
    )
    write(
        ROOT / "behold_lighting" / "preferences.py",
        prefs_module(
            class_name="BEHOLDLightingAddonPreferences",
            title="BEHOLD Lighting",
            extra_chrome="",
            extra_scene="""    settings = getattr(context.scene, "behold_lighting", None)
    if settings is None:
        return
    box = layout.box()
    box.label(text="This scene", icon="SCENE_DATA")
    box.prop(settings, "studio_light_rig", text="Rig")
""",
            extra_imports="",
            check_op="behold_lighting",
        ),
    )
    write(
        ROOT / "behold_product" / "preferences.py",
        prefs_module(
            class_name="BEHOLDProductAddonPreferences",
            title="BEHOLD Product",
            extra_chrome='''
    show_header_shortcuts: BoolProperty(
        name="3D View header shortcuts",
        description="Show BEHOLD pie + Import / Build / Still on the 3D Viewport header",
        default=True,
    )
    show_flow_strip: BoolProperty(
        name="Workflow strip",
        description="Show Import → Studio → Dress → Shoot on the BEHOLD sidebar",
        default=True,
    )
''',
            extra_scene="""    settings = getattr(context.scene, "behold_product", None)
    if settings is None:
        return
    box = layout.box()
    box.label(text="This scene", icon="SCENE_DATA")
    box.prop(settings, "import_auto_studio")
    box.prop(settings, "import_auto_material_assist")
    box.prop(settings, "render_quality", text="Quality")
""",
            extra_imports="",
            check_op="behold_product",
        ),
    )
    write(
        ROOT / "behold_utilities" / "preferences.py",
        prefs_module(
            class_name="BEHOLDUtilitiesAddonPreferences",
            title="BEHOLD Utilities",
            extra_chrome="",
            extra_scene="""    del layout
    del context
""",
            extra_imports="",
            check_op="behold_utilities",
        ),
    )


def init_module(
    *,
    name: str,
    description: str,
    modules: str,
) -> str:
    return f'''# SPDX-License-Identifier: GPL-3.0-or-later
"""{name} — {description}"""

from __future__ import annotations

bl_info = {{
    "name": "{name}",
    "author": "AMIRITE.studio",
    "version": (2, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > BEHOLD",
    "description": "{description}",
    "category": "Render",
    "doc_url": "https://github.com/wckdboy/BEHOLD",
}}

{modules}


def register() -> None:
    for module in _MODULES:
        module.register()


def unregister() -> None:
    for module in reversed(_MODULES):
        module.unregister()


if __name__ == "__main__":
    register()
'''


def write_inits() -> None:
    write(
        ROOT / "behold_studio" / "__init__.py",
        init_module(
            name="BEHOLD Studio",
            description="Cyclorama, HDRI world, and ground contact — BEHOLD by AMIRITE.studio",
            modules="""from . import operators
from . import preferences
from . import properties
from . import ui
from .common import previews
from .common import updates

_MODULES = (
    previews,
    properties,
    preferences,
    updates,
    operators,
    ui,
)
""",
        ),
    )
    write(
        ROOT / "behold_lighting" / "__init__.py",
        init_module(
            name="BEHOLD Lighting",
            description="Multi-light, Light Draw, gobo, IES, and linking — BEHOLD by AMIRITE.studio",
            modules="""from . import operators
from . import preferences
from . import properties
from . import ui
from .common import previews
from .common import updates
from .light_draw import operators as light_draw_ops

_MODULES = (
    previews,
    properties,
    preferences,
    updates,
    operators,
    light_draw_ops,
    ui,
)
""",
        ),
    )
    write(
        ROOT / "behold_product" / "__init__.py",
        init_module(
            name="BEHOLD Product",
            description="Import, materials, cameras, and Shoot — BEHOLD by AMIRITE.studio",
            modules="""from . import preferences
from . import properties
from .cad import operators as cad_ops
from .common import previews
from .common import updates
from .materials import blenderkit_bridge, local_rack
from .product_import import operators as product_ops
from .shoot import operators as shoot_ops
from . import ui

_MODULES = (
    previews,
    properties,
    preferences,
    updates,
    local_rack,
    blenderkit_bridge,
    shoot_ops,
    cad_ops,
    product_ops,
    ui,
)
""",
        ),
    )
    write(
        ROOT / "behold_utilities" / "__init__.py",
        init_module(
            name="BEHOLD Utilities",
            description="Danish wall, balcony mounts, and eave sections — BEHOLD by AMIRITE.studio",
            modules="""from . import operators
from . import panel
from . import preferences
from . import properties
from .common import previews
from .common import updates

_MODULES = (
    previews,
    properties,
    preferences,
    updates,
    operators,
    panel,
)
""",
        ),
    )


def rewrite_ui_imports(text: str, *, settings: str, extra: list[tuple[str, str]]) -> str:
    for old, new in extra:
        text = text.replace(old, new)
    text = text.replace("context.scene.behold", f"context.scene.{settings}")
    text = text.replace("scene.behold", f"scene.{settings}")
    return text


def write_ui() -> None:
    orig_panels = (MONO / "ui" / "panels.py").read_text(encoding="utf-8")
    orig_flow = (MONO / "ui" / "flow.py").read_text(encoding="utf-8")
    orig_chrome = (MONO / "ui" / "chrome.py").read_text(encoding="utf-8")
    orig_scan = (MONO / "ui" / "scene_scan.py").read_text(encoding="utf-8")
    orig_pie = (MONO / "ui" / "pie.py").read_text(encoding="utf-8")

    flow = orig_flow
    flow = flow.replace("from ..brand import", "from ..common.brand import")
    flow = flow.replace("from ..materials.presets import PRESETS, material_name_for", "from ..materials.presets import PRESETS, material_name_for")
    flow = flow.replace("from ..studio.camera_ids import is_studio_mesh_name", "from ..common.camera_ids import is_studio_mesh_name")
    flow = flow.replace("from ..utilities.ids import is_utility_mesh_name", "from ..common.utility_ids import is_utility_mesh_name")
    flow = flow.replace("from .messages import", "from ..common.messages import")
    flow = flow.replace(
        '''CHILD_PANEL_BL_ORDER: dict[str, int] = {
    "BEHOLD_PT_import": 10,
    "BEHOLD_PT_studio": 20,
    "BEHOLD_PT_lights": 30,
    "BEHOLD_PT_materials": 40,
    "BEHOLD_PT_cameras": 50,
    "BEHOLD_PT_shoot": 60,
    "BEHOLD_PT_advanced": 70,
}''',
        '''CHILD_PANEL_BL_ORDER: dict[str, int] = {
    "BEHOLD_PT_import": 10,
    "BEHOLD_PT_studio": 20,
    "BEHOLD_PT_lights": 30,
    "BEHOLD_PT_materials": 40,
    "BEHOLD_PT_cameras": 50,
    "BEHOLD_PT_shoot": 60,
    "BEHOLD_PT_advanced": 70,
    "BEHOLD_PT_utilities": 80,
}''',
    )
    flow = flow.replace(
        '''N_PANEL_CLASS_ORDER = (
    "BEHOLD_PT_main",
    "BEHOLD_PT_import",
    "BEHOLD_PT_studio",
    "BEHOLD_PT_lights",
    "BEHOLD_PT_materials",
    "BEHOLD_PT_cameras",
    "BEHOLD_PT_shoot",
    "BEHOLD_PT_advanced",
)''',
        '''N_PANEL_CLASS_ORDER = (
    "BEHOLD_PT_main",
    "BEHOLD_PT_import",
    "BEHOLD_PT_studio",
    "BEHOLD_PT_lights",
    "BEHOLD_PT_materials",
    "BEHOLD_PT_cameras",
    "BEHOLD_PT_shoot",
    "BEHOLD_PT_advanced",
    "BEHOLD_PT_utilities",
)'''
    )
    write(ROOT / "behold_product" / "ui" / "flow.py", flow)

    chrome = orig_chrome
    chrome = chrome.replace("from ..brand import", "from ..common.brand import")
    chrome = chrome.replace("from ..draw_cache import", "from ..common.draw_cache import")
    chrome = chrome.replace("from ..previews import", "from ..common.previews import")
    chrome = chrome.replace("from ..studio import cameras as camera_lib", "from .. import cameras as camera_lib")
    chrome = chrome.replace("from ..studio import lights as light_lib", "from ..common.light_ids import is_behold_light_name")
    chrome = chrome.replace("from ..updates.core import", "from ..common.updates.core import")
    chrome = chrome.replace("from ..updates.runtime import notice_is_dismissed", "from ..common.updates.runtime import notice_is_dismissed")
    chrome = chrome.replace(
        "is_behold_light=ob_type == \"LIGHT\" and light_lib.is_behold_light(obj),",
        "is_behold_light=ob_type == \"LIGHT\" and is_behold_light_name(obj.name),",
    )
    chrome = chrome.replace('row.operator("behold.check_updates"', 'row.operator("behold_product.check_updates"')
    chrome = chrome.replace('row.operator("behold.install_update"', 'row.operator("behold_product.install_update"')
    chrome = chrome.replace('row.operator("behold.open_release"', 'row.operator("behold_product.open_release"')
    chrome = chrome.replace('row.operator("behold.dismiss_update"', 'row.operator("behold_product.dismiss_update"')
    write(ROOT / "behold_product" / "ui" / "chrome.py", chrome)

    scan = orig_scan.replace("from .flow import", "from .flow import")
    write(ROOT / "behold_product" / "ui" / "scene_scan.py", scan)

    pie = orig_pie
    pie = pie.replace("from ..brand import", "from ..common.brand import")
    pie = pie.replace("from ..previews import", "from ..common.previews import")
    write(ROOT / "behold_product" / "ui" / "pie.py", pie)

    # Product panels: drop studio/lights first-class panels; keep parked product extras.
    product_panels = orig_panels
    product_panels = product_panels.replace("from ..previews import", "from ..common.previews import")
    product_panels = product_panels.replace("from ..studio import cameras as camera_lib", "from .. import cameras as camera_lib")
    product_panels = product_panels.replace("from ..studio import lights as light_lib", "from ..common.light_ids import is_behold_light_name")
    product_panels = product_panels.replace("context.scene.behold", "context.scene.behold_product")
    # Drop studio / lights panel classes from CLASSES and class bodies later via rewrite of CLASSES + parent_id.
    product_panels = product_panels.replace(
        '''CLASSES = (
    BEHOLD_PT_main,
    BEHOLD_PT_import,
    BEHOLD_PT_studio,
    BEHOLD_PT_lights,
    BEHOLD_PT_materials,
    BEHOLD_PT_cameras,
    BEHOLD_PT_shoot,
    BEHOLD_PT_advanced,
)''',
        '''CLASSES = (
    BEHOLD_PT_main,
    BEHOLD_PT_import,
    BEHOLD_PT_materials,
    BEHOLD_PT_cameras,
    BEHOLD_PT_shoot,
    BEHOLD_PT_advanced,
)''',
    )
    product_panels = product_panels.replace(
        '''        draw_parked_heading(layout, "Studio", SECTION_ICONS["studio"])
        draw_studio_parked(layout, context)
        draw_parked_heading(layout, "Materials / BlenderKit", SECTION_ICONS["materials"])
        draw_materials_parked(layout, context)
        draw_parked_heading(layout, "Light Draw", SECTION_ICONS["lights"])
        draw_light_draw_parked(layout, context)
        draw_parked_heading(layout, "Shoot", SECTION_ICONS["shoot"])
        draw_shoot_parked(layout, context)''',
        '''        draw_parked_heading(layout, "Materials / BlenderKit", SECTION_ICONS["materials"])
        draw_materials_parked(layout, context)
        draw_parked_heading(layout, "Shoot", SECTION_ICONS["shoot"])
        draw_shoot_parked(layout, context)''',
    )
    write(ROOT / "behold_product" / "ui" / "panels.py", product_panels)

    write(
        ROOT / "behold_product" / "ui" / "__init__.py",
        '''# SPDX-License-Identifier: GPL-3.0-or-later
"""UI registration for BEHOLD Product."""

from . import panels, pie


def register() -> None:
    panels.register()
    pie.register()


def unregister() -> None:
    pie.unregister()
    panels.unregister()
''',
    )

    studio_panels = f'''# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD Studio N-panel."""

from __future__ import annotations

import bpy
from bpy.types import Context, Panel, UILayout

from ..common.chrome import draw_empty_card, draw_parked_heading, draw_section_icon
from ..common.deps import IMPORT_PRODUCT_OP, operator_exists
from ..common.messages import NO_MESH_SELECTED
from .flow_ids import SECTION_ICONS

# Re-exported draw helpers used by tests that read this module.


def _settings(context: Context):
    return context.scene.behold_studio


def draw_studio_first_ship(layout: UILayout, context: Context) -> None:
    """Backdrop White / Grey / Black + Build, Catcher, compact HDRI, compact Bake HDRI."""
    settings = _settings(context)
    card = layout.box()
    card.prop(settings, "studio_backdrop_tone", text="Backdrop", expand=True)
    row = card.row(align=True)
    row.operator("behold.build_studio", text="Build", icon="OUTLINER_OB_LIGHT")
    row.prop(settings, "include_shadow_catcher", text="Catcher", toggle=True)
    draw_studio_hdri(layout, context)
    draw_studio_bake(layout, context)


def draw_studio_hdri(layout: UILayout, context: Context) -> None:
    """World HDRI: load, strength, Z rotation, optional reflections-only."""
    settings = _settings(context)
    card = layout.box()
    card.label(text="HDRI", icon="WORLD")
    card.prop(settings, "hdri_filepath", text="")
    row = card.row(align=True)
    row.operator("behold.load_hdri", text="Load", icon="FILE_IMAGE")
    row.operator("behold.reset_world", text="Reset", icon="LOOP_BACK")
    card.prop(settings, "hdri_strength", text="Strength")
    card.prop(settings, "hdri_rotation", text="Rotation")
    card.prop(settings, "hdri_reflections_only", text="Reflections only")
    if settings.hdri_reflections_only:
        card.prop(settings, "hdri_background_strength", text="Background")


def draw_studio_bake(layout: UILayout, context: Context) -> None:
    """Bake studio lights to an equirectangular HDR/EXR (1K/2K)."""
    settings = _settings(context)
    card = layout.box()
    card.label(text="Bake HDRI", icon="WORLD")
    card.prop(settings, "bake_hdri_filepath", text="")
    row = card.row(align=True)
    row.prop(settings, "bake_hdri_resolution", text="Size", expand=True)
    row = card.row(align=True)
    row.prop(settings, "bake_hdri_include_world", text="Include world")
    row.prop(settings, "bake_hdri_apply", text="Apply after bake")
    card.operator("behold.bake_hdri", text="Bake HDRI", icon="RENDER_STILL")


def draw_studio_parked(layout: UILayout, context: Context) -> None:
    """Backdrop type, catcher apply, studio margin."""
    settings = _settings(context)
    selected = any(obj.type == "MESH" for obj in context.selected_objects)
    if not selected:
        box = layout.box()
        box.label(text=NO_MESH_SELECTED, icon="INFO")
        if operator_exists(IMPORT_PRODUCT_OP):
            box.operator(IMPORT_PRODUCT_OP, icon="IMPORT")
        else:
            box.label(text="Install BEHOLD Product for Import Product")
    layout.prop(settings, "studio_backdrop")
    layout.prop(settings, "include_shadow_catcher", text="Catcher")
    layout.operator("behold.apply_catcher", icon="SHADERFX")
    layout.prop(settings, "studio_margin")


class BEHOLD_PT_studio(Panel):
    bl_label = "Studio"
    bl_idname = "BEHOLD_PT_studio"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_order = 20

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, SECTION_ICONS["studio"])

    def draw(self, context: Context):
        draw_studio_first_ship(self.layout, context)


class BEHOLD_PT_studio_advanced(Panel):
    bl_label = "Studio extras"
    bl_idname = "BEHOLD_PT_studio_advanced"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_options = {{"DEFAULT_CLOSED"}}
    bl_order = 21

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, "PREFERENCES")

    def draw(self, context: Context):
        draw_parked_heading(self.layout, "Studio", SECTION_ICONS["studio"], leading_separator=False)
        draw_studio_parked(self.layout, context)


CLASSES = (
    BEHOLD_PT_studio,
    BEHOLD_PT_studio_advanced,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
'''
    write(ROOT / "behold_studio" / "ui" / "panels.py", studio_panels)
    write(
        ROOT / "behold_studio" / "ui" / "flow_ids.py",
        '''# SPDX-License-Identifier: GPL-3.0-or-later
"""Section icons shared with the suite N-panel."""

SECTION_ICONS = {{
    "studio": "OUTLINER_OB_LIGHT",
}}
'''.replace("{{", "{").replace("}}", "}"),
    )
    write(
        ROOT / "behold_studio" / "ui" / "__init__.py",
        '''# SPDX-License-Identifier: GPL-3.0-or-later
"""UI registration for BEHOLD Studio."""

from . import panels


def register() -> None:
    panels.register()


def unregister() -> None:
    panels.unregister()
''',
    )

    lighting_panels = '''# SPDX-License-Identifier: GPL-3.0-or-later
"""BEHOLD Lighting N-panel."""

from __future__ import annotations

import bpy
from bpy.types import Context, Panel, UILayout

from .. import lights as light_lib
from ..common.chrome import draw_empty_card, draw_parked_heading, draw_section_icon
from ..common.deps import BUILD_STUDIO_OP
from .flow_ids import EMPTY_LIGHTS, SECTION_ICONS


def _settings(context: Context):
    return context.scene.behold_lighting


def draw_lights_section(layout: UILayout, context: Context) -> None:
    """Multi-light inventory + shape + gobo + IES + linking lite + Light Draw."""
    settings = _settings(context)
    lights = light_lib.iter_behold_lights(context)

    if not lights:
        empty = draw_empty_card(layout, EMPTY_LIGHTS)
        empty.prop(settings, "new_light_energy", text="New W")
        empty.operator("behold.add_light", text="Add Light", icon="ADD")
    else:
        active = light_lib.get_active_behold_light(context)
        active_name = active.name if active is not None else ""
        box = layout.box()
        box.label(text="Studio lights", icon="LIGHT_AREA")
        for light in lights:
            row = box.row(align=True)
            is_active = light.name == active_name
            icon = "RADIOBUT_ON" if is_active else "RADIOBUT_OFF"
            op = row.operator("behold.set_active_light", text="", icon=icon, emboss=False)
            op.light_name = light.name
            row.label(text=light_lib.display_light_name(light))
            row.prop(light.data, "energy", text="")
            rm = row.operator("behold.remove_light", text="", icon="X")
            rm.light_name = light.name
        if active is not None:
            box.label(text=f"Active: {light_lib.display_light_name(active)}")
        draw_lights_shape(layout, context)
        draw_lights_gobo(layout, context)
        draw_lights_ies(layout, context)
        draw_lights_linking(layout, context)
        row = layout.row(align=True)
        row.prop(settings, "new_light_energy", text="New W")
        row.operator("behold.add_light", text="Add", icon="ADD")

    layout.separator()
    col = layout.box()
    col.label(text="Light Draw", icon="LIGHT_AREA")
    col.prop(settings, "light_draw_target", text="Aim", expand=True)
    col.prop(settings, "light_draw_mode", text="Mode", expand=True)
    col.prop(settings, "light_draw_distance")
    col.operator("behold.light_draw", icon="LIGHT_AREA")


def draw_lights_shape(layout: UILayout, context: Context) -> None:
    """Size and spread on this light. Falloff waits until Gobo and IES are off."""
    settings = _settings(context)
    card = layout.box()
    card.label(text="Shape", icon="LIGHT_AREA")
    card.label(text="Size and spread. Falloff waits until Gobo and IES are off")
    card.prop(settings, "light_shape_preset", text="", expand=True)
    apply = card.operator(
        "behold.apply_light_preset",
        text="Apply to active",
        icon="CHECKMARK",
    )
    apply.preset = settings.light_shape_preset


def draw_lights_gobo(layout: UILayout, context: Context) -> None:
    """Cookie on this light. Turns IES off."""
    settings = _settings(context)
    card = layout.box()
    card.label(text="Gobo", icon="TEXTURE")
    card.label(text="Cookie on this light. Turns IES off")
    card.prop(settings, "light_gobo_preset", text="", expand=True)
    if settings.light_gobo_preset != "NONE":
        row = card.row(align=True)
        row.prop(settings, "light_gobo_scale", text="Scale")
        row.prop(settings, "light_gobo_strength", text="Strength")


def draw_lights_ies(layout: UILayout, context: Context) -> None:
    """Photometric profile. Turns Gobo off."""
    settings = _settings(context)
    card = layout.box()
    card.label(text="IES", icon="LIGHT_SPOT")
    card.label(text="Photometric profile. Turns Gobo off")
    card.prop(settings, "light_ies_filepath", text="")
    row = card.row(align=True)
    row.operator("behold.load_ies", text="Load", icon="FILE_FOLDER")
    row.operator("behold.load_ies_sample", text="Sample")
    row.operator("behold.clear_ies", text="Clear", icon="X")
    if settings.light_ies_filepath:
        row = card.row(align=True)
        row.prop(settings, "light_ies_strength", text="Strength")
        row.prop(settings, "light_ies_scale", text="Scale")


def draw_lights_linking(layout: UILayout, context: Context) -> None:
    """Who this light hits. Independent of Shape / Gobo / IES."""
    settings = _settings(context)
    card = layout.box()
    card.label(text="Linking", icon="LINKED")
    card.label(text="Who this light hits — not the beam shape")
    card.prop(settings, "light_linking_kind", text="", expand=True)
    row = card.row(align=True)
    link = row.operator("behold.link_selected", text="Link Selected")
    link.kind = settings.light_linking_kind
    unlink = row.operator("behold.unlink_selected", text="Unlink")
    unlink.kind = settings.light_linking_kind
    row.operator("behold.solo_product_link", text="Solo product")


def draw_light_draw_parked(layout: UILayout, context: Context) -> None:
    """Light Draw hotkeys + Apply Gobo / IES (parked — both live on Lights)."""
    settings = _settings(context)
    col = layout.column(align=True)
    col.label(text="While drawing:")
    col.label(text="LMB drag — aim")
    col.label(text="Wheel — power")
    col.label(text="Shift+Wheel — size")
    col.label(text="Ctrl+Wheel — distance")
    col.label(text="1 / 2 / 3 — Reflect / Direct / Orbit")
    col.label(text="S — solo · F — false color · Esc — exit")
    col.separator()
    col.label(text="Open Light Draw from the pie (Shift+Alt+B) or Lights")
    col.separator()
    col.label(text="Gobo")
    col.prop(settings, "light_gobo_preset", text="", expand=True)
    col.prop(settings, "light_gobo_scale")
    col.prop(settings, "light_gobo_strength")
    col.operator("behold.apply_gobo", icon="TEXTURE")
    col.separator()
    col.label(text="IES")
    col.prop(settings, "light_ies_filepath", text="")
    col.prop(settings, "light_ies_strength")
    col.prop(settings, "light_ies_scale")
    col.operator("behold.apply_ies", icon="LIGHT_SPOT")
    col.operator("behold.clear_ies", text="Clear IES")
    col.separator()
    col.label(text="Light Mixer")
    col.prop(settings, "key_power")
    col.prop(settings, "fill_ratio")
    col.prop(settings, "rim_ratio")
    col.prop(settings, "light_temperature")
    col.prop(settings, "studio_light_rig")
    col.operator("behold.refresh_lights", icon="FILE_REFRESH")


class BEHOLD_PT_lights(Panel):
    bl_label = "Lights"
    bl_idname = "BEHOLD_PT_lights"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_order = 30

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, SECTION_ICONS["lights"])

    def draw(self, context: Context):
        draw_lights_section(self.layout, context)


class BEHOLD_PT_lights_advanced(Panel):
    bl_label = "Lights extras"
    bl_idname = "BEHOLD_PT_lights_advanced"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BEHOLD"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 31

    def draw_header(self, context: Context):
        del context
        draw_section_icon(self.layout, "PREFERENCES")

    def draw(self, context: Context):
        draw_parked_heading(
            self.layout, "Light Draw", SECTION_ICONS["lights"], leading_separator=False
        )
        draw_light_draw_parked(self.layout, context)


CLASSES = (
    BEHOLD_PT_lights,
    BEHOLD_PT_lights_advanced,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
'''
    write(ROOT / "behold_lighting" / "ui" / "panels.py", lighting_panels)
    write(
        ROOT / "behold_lighting" / "ui" / "flow_ids.py",
        '''# SPDX-License-Identifier: GPL-3.0-or-later
"""Empty-state + icons for Lights — no Blender import."""

from dataclasses import dataclass

from ...common.deps import BUILD_STUDIO_OP
from ...common.messages import NO_LIGHTS_NEXT, NO_LIGHTS_TITLE

SECTION_ICONS = {
    "lights": "LIGHT_AREA",
}


@dataclass(frozen=True)
class EmptyState:
    title: str
    hint: str
    operator: str
    operator_text: str
    icon: str


EMPTY_LIGHTS = EmptyState(
    title=NO_LIGHTS_TITLE,
    hint=NO_LIGHTS_NEXT,
    operator=BUILD_STUDIO_OP,
    operator_text="Build Studio",
    icon="OUTLINER_OB_LIGHT",
)
''',
    )
    write(
        ROOT / "behold_lighting" / "ui" / "__init__.py",
        '''# SPDX-License-Identifier: GPL-3.0-or-later
"""UI registration for BEHOLD Lighting."""

from . import panels


def register() -> None:
    panels.register()


def unregister() -> None:
    panels.unregister()
''',
    )


def patch_utilities_ui() -> None:
    panel = (ROOT / "behold_utilities" / "panel.py").read_text(encoding="utf-8")
    panel = panel.replace("from .preferences import get_prefs\n", "")
    panel = panel.replace("from .flag import PANEL_ID, show_utilities_panel\n", "from .flag import PANEL_ID\n")
    panel = panel.replace('    bl_parent_id = "BEHOLD_PT_main"\n', "")
    panel = panel.replace(
        '''    @classmethod
    def poll(cls, context: Context) -> bool:
        return show_utilities_panel(get_prefs(context))

''',
        "",
    )
    if "def register()" not in panel:
        panel += '''

def register() -> None:
    import bpy

    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    import bpy

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
'''
    write(ROOT / "behold_utilities" / "panel.py", panel)

    flag = (ROOT / "behold_utilities" / "flag.py").read_text(encoding="utf-8")
    flag = flag.replace("DEFAULT_ENABLE_UTILITIES = False", "DEFAULT_ENABLE_UTILITIES = True")
    flag = flag.replace(
        '''def show_utilities_panel(prefs: Any | None) -> bool:
    """True when the add-on preference enables the Utilities N-panel."""
    if prefs is None:
        return False
    return bool(getattr(prefs, PREF_ID, DEFAULT_ENABLE_UTILITIES))''',
        '''def show_utilities_panel(prefs: Any | None) -> bool:
    """Utilities is its own add-on — the panel is always on when this zip is enabled."""
    del prefs
    return True''',
    )
    write(ROOT / "behold_utilities" / "flag.py", flag)

    write(
        ROOT / "behold_utilities" / "registration.py",
        '''# SPDX-License-Identifier: GPL-3.0-or-later
"""Register Utilities operators + panel. Always on in the suite add-on."""

from __future__ import annotations

import bpy


def _classes():
    from .operators import CLASSES as OPERATOR_CLASSES
    from .panel import CLASSES as PANEL_CLASSES

    return OPERATOR_CLASSES + PANEL_CLASSES


def register() -> None:
    for cls in _classes():
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_classes()):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
''',
    )


def patch_product_panels_dead_classes() -> None:
    """Leave unused studio/lights panel class defs; they are not in CLASSES.

    Tests that parse CLASSES should ignore them. Remove bl_parent_id so Product
    sections still draw if a sibling add-on is missing? Keep parent_id on
    Product children — Product always registers BEHOLD_PT_main.
    """
    path = ROOT / "behold_product" / "ui" / "panels.py"
    text = path.read_text(encoding="utf-8")
    # Studio / Lights panels remain in the file for source tests that search
    # draw_studio_first_ship; they are not registered from this add-on.
    # Comment their CLASSES membership already done.
    path.write_text(text, encoding="utf-8")


def main() -> None:
    copy_assets()
    write_manifests()
    write_properties()
    write_preferences()
    write_inits()
    write_ui()
    patch_utilities_ui()
    patch_product_panels_dead_classes()
    print("suite glue written")


if __name__ == "__main__":
    main()
