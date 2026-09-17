# SPDX-License-Identifier: GPL-3.0-or-later
"""Native mesh-importer kwargs and failure copy (no bpy).

Blender 4.2+ / 5.2 LTS operators disagree on filepath vs directory+files.
Try the known EXEC_DEFAULT patterns; report which operator failed and why.
"""

from __future__ import annotations

import os
from typing import Any


def mesh_import_kwarg_attempts(filepath: str) -> tuple[dict[str, Any], ...]:
    """Known EXEC_DEFAULT kwargs for wm.obj_import / stl / gltf / fbx / 3mf."""
    abs_path = os.path.abspath(filepath)
    directory = os.path.dirname(abs_path)
    basename = os.path.basename(abs_path)
    files = [{"name": basename}]
    return (
        {"filepath": abs_path},
        {"filepath": abs_path, "directory": directory, "files": files},
        {"filepath": abs_path, "files": files},
        {"directory": directory, "files": files},
    )


def format_mesh_import_failure(
    filepath: str,
    *,
    operator_id: str | None = None,
    errors: list[str] | None = None,
) -> str:
    name = os.path.basename(filepath) or filepath
    op = operator_id or "native importer"
    if errors:
        why = "; ".join(part for part in errors if part)
        if why:
            return f"{op} failed to import {name}: {why}"
    return f"{op} failed to import {name}"


def format_no_mesh_operator_message(ext: str, candidates: tuple[str, ...]) -> str:
    tried = ", ".join(candidates) if candidates else "no operator candidates"
    if ext == ".3mf":
        return (
            "This Blender has no 3MF importer. "
            f"Tried {tried}. Install a 3MF add-on (File → Import) or export "
            "OBJ / STL / GLB instead."
        )
    if ext == ".fbx":
        return (
            f"No FBX importer found (tried {tried}). "
            "On Blender 5.2 LTS enable the FBX add-on / extension in Preferences."
        )
    return (
        f"No native importer found for {ext or 'this file'} (tried {tried}). "
        "Enable the format's importer in Preferences if Blender 5.2 moved it "
        "to an extension."
    )


def format_empty_mesh_import_message(operator_id: str) -> str:
    return (
        f"Importer ran but produced no mesh objects ({operator_id}) — "
        "check the file or try OBJ / STL / GLB"
    )


def format_file_not_found_message(filepath: str) -> str:
    name = os.path.basename(filepath) or filepath or "that file"
    return f"File not found: {name} — choose an existing product file"


def format_unsupported_file_message(ext: str) -> str:
    shown = (ext or "").strip() or "this file"
    return (
        f"Unsupported file type: {shown} — "
        "use OBJ, FBX, STL, GLB, 3MF, or STEP/IGES"
    )
