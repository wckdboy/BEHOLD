# SPDX-License-Identifier: GPL-3.0-or-later
"""Product file format registry (no Blender import)."""

from __future__ import annotations

import os
from typing import Literal

Kind = Literal["cad", "mesh", "unknown"]

CAD_EXTENSIONS = frozenset({".step", ".stp", ".iges", ".igs", ".brep", ".brp"})

# Blender 4.2+ operator candidates, first match wins at runtime.
MESH_OPERATORS: dict[str, tuple[str, ...]] = {
    ".obj": ("wm.obj_import", "import_scene.obj"),
    ".fbx": ("import_scene.fbx",),
    ".stl": ("wm.stl_import", "import_mesh.stl"),
    ".glb": ("import_scene.gltf",),
    ".gltf": ("import_scene.gltf",),
    ".3mf": (
        "wm.threemf_import",
        "import_mesh.threemf",
        "import_scene.threemf",
    ),
}

MESH_EXTENSIONS = frozenset(MESH_OPERATORS)
ALL_PRODUCT_EXTENSIONS = CAD_EXTENSIONS | MESH_EXTENSIONS

FORMAT_LABELS: dict[str, str] = {
    ".obj": "OBJ",
    ".fbx": "FBX",
    ".stl": "STL",
    ".glb": "glTF / GLB",
    ".gltf": "glTF / GLB",
    ".3mf": "3MF",
    ".step": "STEP",
    ".stp": "STEP",
    ".iges": "IGES",
    ".igs": "IGES",
    ".brep": "BREP",
    ".brp": "BREP",
}


def extension_of(filepath: str) -> str:
    return os.path.splitext(filepath)[1].lower()


def classify_product_file(filepath: str) -> Kind:
    ext = extension_of(filepath)
    if ext in CAD_EXTENSIONS:
        return "cad"
    if ext in MESH_EXTENSIONS:
        return "mesh"
    return "unknown"


def mesh_operator_candidates(filepath: str) -> tuple[str, ...]:
    return MESH_OPERATORS.get(extension_of(filepath), ())


def import_filter_glob() -> str:
    return ";".join(f"*{ext}" for ext in sorted(ALL_PRODUCT_EXTENSIONS))


def mesh_format_summary() -> str:
    return "OBJ, FBX, STL, GLB/GLTF, 3MF"


def cad_format_summary() -> str:
    return "STEP, IGES, BREP"
