# SPDX-License-Identifier: GPL-3.0-or-later
"""Install-from-disk regressions: zip layout, manifest, register graph."""

from __future__ import annotations

import ast
import io
import tomllib
import unittest
import zipfile
from pathlib import Path

from tests.support import ADDONS, LIGHTING, PRODUCT, ROOT, STUDIO, UTILITIES

BUILD_SCRIPT = ROOT / "scripts" / "build_addon.sh"
SUITE = (
    (STUDIO, "behold_studio", "behold-studio"),
    (LIGHTING, "behold_lighting", "behold-lighting"),
    (PRODUCT, "behold_product", "behold-product"),
    (UTILITIES, "behold_utilities", "behold-utilities"),
)

TERSE_DESCRIPTION_MAX_LENGTH = 64
PERMISSION_KEYS = frozenset({"files", "network", "clipboard", "camera", "microphone"})
ADDON_TAGS = frozenset(
    {
        "3D View",
        "Add Curve",
        "Add Mesh",
        "Animation",
        "Bake",
        "Camera",
        "Compositing",
        "Development",
        "Game Engine",
        "Geometry Nodes",
        "Grease Pencil",
        "Import-Export",
        "Lighting",
        "Material",
        "Mesh",
        "Modeling",
        "Node",
        "Object",
        "Paint",
        "Pipeline",
        "Physics",
        "Render",
        "Rigging",
        "Scene",
        "Sculpt",
        "Sequencer",
        "System",
        "Text Editor",
        "Tracking",
        "User Interface",
        "UV",
    }
)
SKIP_DIRS = {"__pycache__"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".blend", ".blend1"}
SKIP_NAMES = {".DS_Store"}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _terse_description_error(value: str) -> str | None:
    if len(value) > TERSE_DESCRIPTION_MAX_LENGTH:
        return (
            f"a value no longer than {TERSE_DESCRIPTION_MAX_LENGTH} "
            f"characters expected, found {len(value)}"
        )
    stripped = value.strip()
    if not stripped:
        return "a non-empty string expected"
    if value != stripped:
        return "text without leading/trailing white space expected"
    if any(ord(char) < 32 for char in value):
        return "text without any control characters expected"
    last = value[-1]
    if last.isalnum() or last in {")", "]", "}"}:
        return None
    return "alphanumeric suffix expected, the string must not end with punctuation"


def _module_bound_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()

    def visit_stmt(stmt: ast.stmt) -> None:
        if isinstance(stmt, ast.ClassDef):
            names.add(stmt.name)
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(stmt.name)
        elif isinstance(stmt, ast.Assign):
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(stmt, ast.ImportFrom):
            for alias in stmt.names:
                names.add(alias.asname or alias.name)
        elif isinstance(stmt, ast.Try):
            for inner in stmt.body:
                visit_stmt(inner)
            for handler in stmt.handlers:
                for inner in handler.body:
                    visit_stmt(inner)
            for inner in stmt.orelse:
                visit_stmt(inner)
            for inner in stmt.finalbody:
                visit_stmt(inner)

    for stmt in tree.body:
        visit_stmt(stmt)
    return names


def _classes_tuple_names(tree: ast.Module) -> list[str] | None:
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "CLASSES" for target in node.targets):
            continue
        if not isinstance(node.value, ast.Tuple):
            return None
        names: list[str] = []
        for elt in node.value.elts:
            if not isinstance(elt, ast.Name):
                return None
            names.append(elt.id)
        return names
    return None


def _class_bl_idnames(class_node: ast.ClassDef) -> list[str]:
    found: list[str] = []
    for stmt in class_node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "bl_idname" for target in stmt.targets):
            continue
        if isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            found.append(stmt.value.value)
    return found


def _resolve_relative_import(addon: Path, addon_file: Path, node: ast.ImportFrom) -> list[Path]:
    package_parts = addon_file.parent.relative_to(addon).parts
    climb = node.level - 1
    if climb:
        package_parts = package_parts[:-climb]
    base = addon.joinpath(*package_parts) if package_parts else addon
    module = node.module or ""
    targets: list[Path] = []
    if module:
        dotted = base.joinpath(*module.split("."))
        as_file = dotted.with_suffix(".py")
        as_pkg = dotted / "__init__.py"
        if node.names and node.names[0].name != "*":
            for alias in node.names:
                child_file = dotted / f"{alias.name}.py"
                child_pkg = dotted / alias.name / "__init__.py"
                if child_file.is_file():
                    targets.append(child_file)
                elif child_pkg.is_file():
                    targets.append(child_pkg)
        if as_file.is_file():
            targets.append(as_file)
        elif as_pkg.is_file():
            targets.append(as_pkg)
        return targets
    for alias in node.names:
        child = base / alias.name
        as_file = child.with_suffix(".py")
        as_pkg = child / "__init__.py"
        if as_file.is_file():
            targets.append(as_file)
        elif as_pkg.is_file():
            targets.append(as_pkg)
    return targets


def _zip_source_files(addon: Path) -> list[Path]:
    files: list[Path] = []
    for path in addon.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_NAMES or path.suffix in SKIP_SUFFIXES:
            continue
        files.append(path)
    return files


class ManifestTests(unittest.TestCase):
    def test_each_suite_manifest_passes_blender_52_strict_rules(self) -> None:
        for addon, addon_id, _stem in SUITE:
            with self.subTest(addon=addon_id):
                data = tomllib.loads(_read(addon / "blender_manifest.toml"))
                self.assertEqual(data["schema_version"], "1.0.0")
                self.assertEqual(data["id"], addon_id)
                self.assertEqual(data["version"], "2.0.0")
                self.assertEqual(data["type"], "add-on")
                self.assertTrue(data["id"].isidentifier())
                self.assertNotIn("__", data["id"])
                self.assertFalse(data["id"].startswith("_"))
                self.assertFalse(data["id"].endswith("_"))
                tagline_error = _terse_description_error(data["tagline"])
                self.assertIsNone(tagline_error, tagline_error)
                self.assertEqual(data["blender_version_min"].count("."), 2)
                self.assertTrue(data["license"])
                for tag in data.get("tags", []):
                    self.assertIn(tag, ADDON_TAGS)
                permissions = data.get("permissions", {})
                self.assertIsInstance(permissions, dict)
                for key, reason in permissions.items():
                    self.assertIn(key, PERMISSION_KEYS)
                    perm_error = _terse_description_error(reason)
                    self.assertIsNone(perm_error, f"{key}: {perm_error}")


class ZipLayoutTests(unittest.TestCase):
    def test_build_script_zips_each_suite_folder(self) -> None:
        script = _read(BUILD_SCRIPT)
        self.assertIn('zip -r -q "${OUT}" "${addon}"', script)
        self.assertIn("blender_manifest.toml", script)
        self.assertIn("behold-${slug}-${VERSION}.zip", script)
        self.assertIn("Install from Disk", script)
        self.assertIn("extension build", script)
        self.assertIn("behold_studio", script)
        self.assertIn("behold_lighting", script)
        self.assertIn("behold_product", script)
        self.assertIn("behold_utilities", script)

    def test_zip_payload_has_manifest_and_init(self) -> None:
        expected = {
            STUDIO: {"blender_manifest.toml", "__init__.py", "setup.py", "operators.py"},
            LIGHTING: {"blender_manifest.toml", "__init__.py", "lights.py", "ies/sample_spot.ies"},
            PRODUCT: {"blender_manifest.toml", "__init__.py", "cad/operators.py", "shoot/operators.py"},
            UTILITIES: {"blender_manifest.toml", "__init__.py", "eaves.py", "settings.py"},
        }
        for addon, files in expected.items():
            payload = {path.relative_to(addon).as_posix() for path in _zip_source_files(addon)}
            for name in files:
                self.assertIn(name, payload, msg=addon.name)
            self.assertTrue((addon / "icons" / "behold_icon.png").is_file(), addon.name)
            self.assertTrue((addon / "common" / "brand.py").is_file(), addon.name)

    def test_staged_zip_is_single_addon_root(self) -> None:
        """Blender 5.2 Install from Disk accepts one folder with blender_manifest.toml."""
        for addon, addon_id, _stem in SUITE:
            with self.subTest(addon=addon_id):
                buffer = io.BytesIO()
                with zipfile.ZipFile(buffer, "w") as archive:
                    for path in _zip_source_files(addon):
                        archive.write(path, arcname=f"{addon_id}/" + path.relative_to(addon).as_posix())
                with zipfile.ZipFile(buffer) as archive:
                    names = archive.namelist()
                roots = {name.split("/", 1)[0] for name in names if name}
                self.assertEqual(roots, {addon_id})
                self.assertIn(f"{addon_id}/blender_manifest.toml", names)
                self.assertIn(f"{addon_id}/__init__.py", names)


class RegisterImportGraphTests(unittest.TestCase):
    def test_init_relative_imports_resolve(self) -> None:
        for addon, addon_id, _stem in SUITE:
            with self.subTest(addon=addon_id):
                init_path = addon / "__init__.py"
                tree = ast.parse(_read(init_path), filename=str(init_path))
                missing: list[str] = []
                for node in tree.body:
                    if not isinstance(node, ast.ImportFrom) or node.level < 1:
                        continue
                    resolved = _resolve_relative_import(addon, init_path, node)
                    if not resolved:
                        missing.append(ast.dump(node))
                self.assertEqual(missing, [])

    def test_classes_tuples_bind_to_names_in_the_same_module(self) -> None:
        failures: list[str] = []
        for addon in ADDONS:
            for path in addon.rglob("*.py"):
                tree = ast.parse(_read(path), filename=str(path))
                names = _classes_tuple_names(tree)
                if not names:
                    continue
                bound = _module_bound_names(tree)
                if len(names) != len(set(names)):
                    failures.append(f"{path.relative_to(ROOT)}: CLASSES has duplicate names")
                for name in names:
                    if name not in bound:
                        failures.append(f"{path.relative_to(ROOT)}: CLASSES name {name} is not defined")
        self.assertEqual(failures, [])

    def test_operator_classes_have_one_bl_idname(self) -> None:
        failures: list[str] = []
        seen: dict[str, str] = {}
        for addon in ADDONS:
            for path in addon.rglob("*.py"):
                tree = ast.parse(_read(path), filename=str(path))
                for node in tree.body:
                    if not isinstance(node, ast.ClassDef):
                        continue
                    ids = _class_bl_idnames(node)
                    if not ids:
                        continue
                    rel = str(path.relative_to(ROOT))
                    if len(ids) != 1:
                        failures.append(f"{rel}:{node.name} has bl_idname {ids}")
                        continue
                    previous = seen.get(ids[0])
                    if previous:
                        failures.append(
                            f"duplicate bl_idname {ids[0]} in {previous} and {rel}:{node.name}"
                        )
                    seen[ids[0]] = f"{rel}:{node.name}"
        self.assertEqual(failures, [])

    def test_cad_auto_dress_did_not_swallow_build_studio(self) -> None:
        source = _read(PRODUCT / "cad" / "operators.py")
        tree = ast.parse(source, filename="operators.py")
        by_name = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
        }
        self.assertIn("BEHOLD_OT_cad_auto_dress", by_name)
        self.assertIn("BEHOLD_OT_cad_build_studio", by_name)
        self.assertIn("BEHOLD_OT_cleanup_cad", by_name)
        self.assertEqual(
            _class_bl_idnames(by_name["BEHOLD_OT_cad_auto_dress"]),
            ["behold.cad_auto_dress"],
        )
        self.assertEqual(
            _class_bl_idnames(by_name["BEHOLD_OT_cad_build_studio"]),
            ["behold.cad_build_studio"],
        )
        self.assertEqual(
            _class_bl_idnames(by_name["BEHOLD_OT_cleanup_cad"]),
            ["behold.cleanup_cad"],
        )
        names = _classes_tuple_names(tree)
        self.assertIsNotNone(names)
        assert names is not None
        self.assertIn("BEHOLD_OT_cad_auto_dress", names)
        self.assertIn("BEHOLD_OT_cad_build_studio", names)
        self.assertIn("BEHOLD_OT_cleanup_cad", names)
        self.assertEqual(len(names), len(set(names)))


class SuitePackageTests(unittest.TestCase):
    """Each zip is its own add-on. Product does not import utilities."""

    def test_product_modules_do_not_include_utilities(self) -> None:
        init = _read(PRODUCT / "__init__.py")
        tree = ast.parse(init, filename="__init__.py")
        modules: list[str] = []
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if not any(
                isinstance(target, ast.Name) and target.id == "_MODULES"
                for target in node.targets
            ):
                continue
            if not isinstance(node.value, ast.Tuple):
                self.fail("_MODULES is not a tuple")
            for elt in node.value.elts:
                if isinstance(elt, ast.Name):
                    modules.append(elt.id)
        self.assertIn("ui", modules)
        self.assertIn("cad_ops", modules)
        self.assertNotIn("utilities", modules)
        self.assertEqual(len(modules), len(set(modules)))

    def test_product_does_not_import_sibling_addons(self) -> None:
        init = _read(PRODUCT / "__init__.py")
        self.assertNotIn("behold_studio", init)
        self.assertNotIn("behold_lighting", init)
        self.assertNotIn("behold_utilities", init)
        self.assertNotIn("def _sync_utilities", init)

    def test_utilities_is_its_own_enable_path(self) -> None:
        init = _read(UTILITIES / "__init__.py")
        self.assertIn("from . import operators", init)
        self.assertIn("from . import panel", init)
        self.assertIn('"version": (2, 0, 0)', init)
        props = _read(UTILITIES / "properties.py")
        self.assertIn("BEHOLDUtilitiesSettings", props)
        self.assertNotIn("utilities.operators", props)
        self.assertNotIn("from .operators", props)

    def test_studio_and_lighting_seed_ops_are_split(self) -> None:
        studio_ops = _read(STUDIO / "operators.py")
        lighting_ops = _read(LIGHTING / "operators.py")
        product_ops = _read(PRODUCT / "shoot" / "operators.py")
        self.assertIn('bl_idname = "behold.build_studio"', studio_ops)
        self.assertIn('bl_idname = "behold.seed_studio_lights"', lighting_ops)
        self.assertIn('bl_idname = "behold.seed_studio_camera"', product_ops)


if __name__ == "__main__":
    unittest.main()
