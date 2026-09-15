# SPDX-License-Identifier: GPL-3.0-or-later
"""Install-from-disk regressions: zip layout, manifest, register graph."""

from __future__ import annotations

import ast
import io
import tomllib
import unittest
import zipfile
from pathlib import Path

from tests.support import ROOT

ADDON = ROOT / "behold"
BUILD_SCRIPT = ROOT / "scripts" / "build_addon.sh"

# Blender 5.2 blender_ext.py: tagline / permission reasons.
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


def _resolve_relative_import(addon_file: Path, node: ast.ImportFrom) -> list[Path]:
    package_parts = addon_file.parent.relative_to(ADDON).parts
    climb = node.level - 1
    if climb:
        package_parts = package_parts[:-climb]
    base = ADDON.joinpath(*package_parts) if package_parts else ADDON
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


def _zip_source_files() -> list[Path]:
    files: list[Path] = []
    for path in ADDON.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name in SKIP_NAMES or path.suffix in SKIP_SUFFIXES:
            continue
        files.append(path)
    return files


class ManifestTests(unittest.TestCase):
    def test_manifest_passes_blender_52_strict_rules(self) -> None:
        data = tomllib.loads(_read(ADDON / "blender_manifest.toml"))
        self.assertEqual(data["schema_version"], "1.0.0")
        self.assertEqual(data["id"], "behold")
        self.assertEqual(data["version"], "1.5.1")
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
    def test_build_script_zips_behold_folder(self) -> None:
        script = _read(BUILD_SCRIPT)
        self.assertIn('zip -r -q "${OUT}" behold', script)
        self.assertIn("blender_manifest.toml", script)
        self.assertIn('OUT="${DIST}/behold-${VERSION}.zip"', script)

    def test_zip_payload_has_manifest_and_init(self) -> None:
        files = {path.relative_to(ADDON).as_posix() for path in _zip_source_files()}
        self.assertIn("blender_manifest.toml", files)
        self.assertIn("__init__.py", files)
        self.assertIn("cad/operators.py", files)
        self.assertIn("utilities/settings.py", files)
        self.assertIn("utilities/eaves.py", files)
        self.assertTrue((ADDON / "icons" / "behold_icon.png").is_file())

    def test_staged_zip_is_single_behold_root(self) -> None:
        """Blender 5.2 Install from Disk accepts one folder with blender_manifest.toml."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            for path in _zip_source_files():
                archive.write(path, arcname="behold/" + path.relative_to(ADDON).as_posix())
        with zipfile.ZipFile(buffer) as archive:
            names = archive.namelist()
        roots = {name.split("/", 1)[0] for name in names if name}
        self.assertEqual(roots, {"behold"})
        self.assertIn("behold/blender_manifest.toml", names)
        self.assertIn("behold/__init__.py", names)
        self.assertIn("behold/cad/operators.py", names)
        self.assertTrue(any(name.endswith("behold/utilities/eaves.py") for name in names))


class RegisterImportGraphTests(unittest.TestCase):
    def test_init_relative_imports_resolve(self) -> None:
        init_path = ADDON / "__init__.py"
        tree = ast.parse(_read(init_path), filename=str(init_path))
        missing: list[str] = []
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or node.level < 1:
                continue
            resolved = _resolve_relative_import(init_path, node)
            if not resolved:
                missing.append(ast.dump(node))
        self.assertEqual(missing, [])

    def test_classes_tuples_bind_to_names_in_the_same_module(self) -> None:
        failures: list[str] = []
        for path in ADDON.rglob("*.py"):
            tree = ast.parse(_read(path), filename=str(path))
            names = _classes_tuple_names(tree)
            if not names:
                continue
            bound = _module_bound_names(tree)
            for name in names:
                if name not in bound:
                    failures.append(f"{path.relative_to(ROOT)}: CLASSES name {name} is not defined")
        self.assertEqual(failures, [])

    def test_operator_classes_have_one_bl_idname(self) -> None:
        failures: list[str] = []
        seen: dict[str, str] = {}
        for path in ADDON.rglob("*.py"):
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
                    failures.append(f"duplicate bl_idname {ids[0]} in {previous} and {rel}:{node.name}")
                seen[ids[0]] = f"{rel}:{node.name}"
        self.assertEqual(failures, [])

    def test_cad_auto_dress_did_not_swallow_build_studio(self) -> None:
        source = _read(ADDON / "cad" / "operators.py")
        tree = ast.parse(source, filename="operators.py")
        by_name = {
            node.name: node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
        }
        self.assertIn("BEHOLD_OT_cad_auto_dress", by_name)
        self.assertIn("BEHOLD_OT_cad_build_studio", by_name)
        self.assertEqual(
            _class_bl_idnames(by_name["BEHOLD_OT_cad_auto_dress"]),
            ["behold.cad_auto_dress"],
        )
        self.assertEqual(
            _class_bl_idnames(by_name["BEHOLD_OT_cad_build_studio"]),
            ["behold.cad_build_studio"],
        )
        names = _classes_tuple_names(tree)
        self.assertIsNotNone(names)
        assert names is not None
        self.assertIn("BEHOLD_OT_cad_auto_dress", names)
        self.assertIn("BEHOLD_OT_cad_build_studio", names)


class UtilitiesEnablePathTests(unittest.TestCase):
    """v1.5.1 does not refactor this graph. Follow-up: Utilities off the enable path."""

    def test_utilities_still_loads_on_addon_import(self) -> None:
        init = _read(ADDON / "__init__.py")
        self.assertIn("from . import utilities", init)
        self.assertIn("utilities,", init)
        props = _read(ADDON / "properties.py")
        self.assertIn("from .utilities.settings import BEHOLDUtilitiesSettings", props)
        registration = _read(ADDON / "utilities" / "registration.py")
        header = registration.split("def ", 1)[0]
        self.assertIn("from .operators import CLASSES", header)
        self.assertIn("from .panel import CLASSES", header)


if __name__ == "__main__":
    unittest.main()
