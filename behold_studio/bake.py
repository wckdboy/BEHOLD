# SPDX-License-Identifier: GPL-3.0-or-later
"""Bake studio lights to an equirectangular HDRI — no Blender import.

Planner for the 0.18.0 cut: path, 1K/2K resolution, optional world, apply
after. The Cycles panoramic render lives in ``bake_apply.py``.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Literal, Never

ResolutionId = Literal["1K", "2K"]
BakeProblemKind = Literal["empty", "unsupported"]
ImageFormatId = Literal["OPEN_EXR", "HDR"]

DEFAULT_FILENAME = "behold_studio.exr"
DEFAULT_RESOLUTION: ResolutionId = "1K"
PROBE_NAME = "BEHOLD_BakeProbe"
# Panoramic camera looks along local -Z; 90° X aims world -Y (Blender front).
PROBE_ROTATION_XYZ = (math.pi / 2.0, 0.0, 0.0)

BAKE_EXTENSIONS = frozenset({".hdr", ".exr"})
BAKE_FILTER_GLOB = "*.exr;*.hdr"

RESOLUTION_PIXELS: dict[ResolutionId, tuple[int, int]] = {
    "1K": (1024, 512),
    "2K": (2048, 1024),
}
RESOLUTION_SAMPLES: dict[ResolutionId, int] = {
    "1K": 64,
    "2K": 128,
}

NO_LIGHTS_TO_BAKE = "No BEHOLD lights yet — Build Studio or Add Light"
NO_BAKE_PATH = "No bake path — save the .blend or pick an .hdr / .exr file"
UNSUPPORTED_BAKE = "Unsupported bake format — use .hdr or .exr"
BAKE_FAILED = "Could not bake HDRI — check the path and try Bake HDRI again"
BAKE_RENDER_FAILED = "Bake render failed — switch to Cycles and try Bake HDRI again"

HIDE_OBJECT_TYPES = frozenset({"MESH"})


@dataclass(frozen=True)
class BakePathProblem:
    kind: BakeProblemKind
    detail: str = ""


@dataclass(frozen=True)
class BakePlan:
    filepath: str
    resolution: ResolutionId
    width: int
    height: int
    samples: int
    include_world: bool
    apply_after: bool
    image_format: ImageFormatId
    rotation_xyz: tuple[float, float, float]


def normalize_filepath(filepath: str) -> str:
    return (filepath or "").strip()


def bake_extension(filepath: str) -> str:
    return os.path.splitext(normalize_filepath(filepath))[1].lower()


def is_bake_extension(filepath: str) -> bool:
    return bake_extension(filepath) in BAKE_EXTENSIONS


def is_blender_relative(filepath: str) -> bool:
    return normalize_filepath(filepath).startswith("//")


def resolution_enum_items() -> tuple[tuple[str, str, str], ...]:
    return (
        ("1K", "1K", "1024 × 512 equirectangular"),
        ("2K", "2K", "2048 × 1024 equirectangular"),
    )


def normalize_resolution(preset: str) -> ResolutionId:
    key = (preset or "").strip().upper()
    if key == "2K":
        return "2K"
    return "1K"


def resolution_wh(preset: str) -> tuple[int, int]:
    key = normalize_resolution(preset)
    if key == "1K":
        return RESOLUTION_PIXELS["1K"]
    if key == "2K":
        return RESOLUTION_PIXELS["2K"]
    unreachable: Never = key
    raise RuntimeError(f"unhandled bake resolution: {unreachable}")


def samples_for(preset: str) -> int:
    key = normalize_resolution(preset)
    if key == "1K":
        return RESOLUTION_SAMPLES["1K"]
    if key == "2K":
        return RESOLUTION_SAMPLES["2K"]
    unreachable: Never = key
    raise RuntimeError(f"unhandled bake samples: {unreachable}")


def image_file_format(filepath: str) -> ImageFormatId:
    ext = bake_extension(filepath)
    if ext == ".hdr":
        return "HDR"
    if ext == ".exr":
        return "OPEN_EXR"
    raise RuntimeError(f"unhandled bake format: {ext or filepath}")


def should_hide_for_bake(ob_type: str) -> bool:
    """Meshes (product, cyclorama, catcher) must not land in the 360° map."""
    return (ob_type or "").upper() in HIDE_OBJECT_TYPES


def blend_directory(blend_filepath: str) -> str | None:
    raw = normalize_filepath(blend_filepath)
    if not raw:
        return None
    if is_blender_relative(raw):
        rest = raw[2:].replace("\\", "/")
        parent = os.path.dirname(rest)
        if parent in ("", "."):
            return "//"
        return "//" + parent.strip("/")
    parent = os.path.dirname(os.path.abspath(os.path.expanduser(raw)))
    return parent or None


def default_bake_filepath(
    blend_filepath: str,
    *,
    tempdir: str,
    filename: str = DEFAULT_FILENAME,
) -> str:
    """Next to the saved .blend, else ``tempdir`` / ``behold_studio.exr``."""
    name = (filename or DEFAULT_FILENAME).strip() or DEFAULT_FILENAME
    directory = blend_directory(blend_filepath)
    if directory is None:
        return os.path.join(os.path.abspath(os.path.expanduser(tempdir)), name)
    if is_blender_relative(directory):
        if directory.rstrip("/") in ("", "//"):
            return f"//{name}"
        return directory.rstrip("/") + "/" + name
    return os.path.join(directory, name)


def ensure_bake_filepath(
    filepath: str,
    *,
    blend_filepath: str,
    tempdir: str,
    is_dir: bool | None = None,
) -> str:
    """Fill empty / folder paths. Does not expand Blender ``//`` paths."""
    raw = normalize_filepath(filepath)
    if not raw:
        return default_bake_filepath(blend_filepath, tempdir=tempdir)
    expanded = os.path.expanduser(raw)
    directory = False if is_blender_relative(expanded) else (
        os.path.isdir(expanded) if is_dir is None else is_dir
    )
    if directory:
        return os.path.join(expanded, DEFAULT_FILENAME)
    if not bake_extension(expanded):
        return expanded + ".exr"
    return expanded


def classify_bake_filepath(filepath: str) -> BakePathProblem | None:
    raw = normalize_filepath(filepath)
    if not raw:
        return BakePathProblem("empty")
    if not is_bake_extension(raw):
        return BakePathProblem("unsupported", bake_extension(raw) or raw)
    return None


def path_problem_message(problem: BakePathProblem) -> str:
    if problem.kind == "empty":
        return NO_BAKE_PATH
    if problem.kind == "unsupported":
        shown = problem.detail.strip() or "this file"
        return f"Unsupported bake format: {shown} — use .hdr or .exr"
    unreachable: Never = problem.kind
    raise RuntimeError(f"unhandled bake path problem: {unreachable}")


def probe_clip(size: float) -> tuple[float, float]:
    span = max(float(size), 0.1)
    start = max(span * 0.001, 0.01)
    end = max(span * 50.0, 100.0)
    return start, end


def plan_bake(
    *,
    filepath: str,
    blend_filepath: str,
    tempdir: str,
    resolution: str,
    include_world: bool,
    apply_after: bool,
    is_dir: bool | None = None,
) -> tuple[BakePlan | None, str | None]:
    path = ensure_bake_filepath(
        filepath,
        blend_filepath=blend_filepath,
        tempdir=tempdir,
        is_dir=is_dir,
    )
    problem = classify_bake_filepath(path)
    if problem is not None:
        return None, path_problem_message(problem)
    preset = normalize_resolution(resolution)
    width, height = resolution_wh(preset)
    return (
        BakePlan(
            filepath=path,
            resolution=preset,
            width=width,
            height=height,
            samples=samples_for(preset),
            include_world=bool(include_world),
            apply_after=bool(apply_after),
            image_format=image_file_format(path),
            rotation_xyz=PROBE_ROTATION_XYZ,
        ),
        None,
    )


def baked_message(filepath: str, *, applied: bool) -> str:
    name = os.path.basename(filepath) or filepath or "HDRI"
    if applied:
        return f"Baked studio HDRI: {name} — applied as world"
    return f"Baked studio HDRI: {name}"
