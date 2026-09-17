# SPDX-License-Identifier: GPL-3.0-or-later
"""Catalog batch export planner — no Blender import.

0.19.0: one-click stills for standard product angles (front / ¾ / top)
and optional Shot Manager presets. Path tokens ``{angle}`` ``{camera}``
``{quality}`` are filled the same way still / turntable already did.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Literal, Sequence, Never

JobKind = Literal["angle", "shot"]
AngleId = Literal["front", "three_quarter", "top"]
PlanProblemKind = Literal[
    "nothing",
    "no_product",
    "no_camera",
    "no_shots",
]

DEFAULT_OUTPUT_DIRECTORY = "//behold_out/"
DEFAULT_ANGLE = "still"
DEFAULT_CAMERA = "camera"
DEFAULT_QUALITY = "draft"
OUTPUT_TOKENS = ("{angle}", "{camera}", "{quality}")
TOKEN_HINT = "Tokens: {angle} {camera} {quality}"

DISTANCE_FACTOR = 2.4
MIN_EXTENT = 0.1

# Camera offset as multiples of product extent (max AABB side).
# Matches the historic batch_angles framing.
ANGLE_OFFSETS: dict[str, tuple[float, float, float]] = {
    "front": (0.0, -DISTANCE_FACTOR, 0.35),
    "three_quarter": (DISTANCE_FACTOR * 0.75, -DISTANCE_FACTOR * 0.85, 0.45),
    "top": (0.0, -DISTANCE_FACTOR * 0.15, DISTANCE_FACTOR),
}

STANDARD_ANGLES: tuple[tuple[str, str], ...] = (
    ("front", "front"),
    ("three_quarter", "¾"),
    ("top", "top"),
)

_SLUG_RE = re.compile(r"[^\w.-]+", re.UNICODE)

BATCH_NOTHING = (
    "Nothing to export — enable Front / ¾ / Top or Saved shots"
)
BATCH_NO_MESH = "No product for batch — select the product or Import Product"
BATCH_NO_CAMERA = "No camera — Build Studio or Add Camera"
BATCH_NO_SHOTS = (
    "No shots to export — Add from the current setup, or turn off Saved shots"
)
BATCH_RENDER_FAILED = (
    "Batch render failed — check the camera and try Batch export again"
)


@dataclass(frozen=True)
class BatchJob:
    kind: JobKind
    slug: str
    label: str
    shot_name: str = ""

    @property
    def filename(self) -> str:
        return f"{self.slug}.png"


@dataclass(frozen=True)
class BatchPlan:
    jobs: tuple[BatchJob, ...]
    include_angles: bool
    include_shots: bool

    @property
    def total(self) -> int:
        return len(self.jobs)


def slugify(name: str) -> str:
    """Filesystem-safe token for ``{angle}`` and the PNG stem."""
    cleaned = _SLUG_RE.sub("_", (name or "").strip())
    cleaned = cleaned.strip("._")
    return cleaned or "shot"


def fill_output_tokens(
    template: str,
    *,
    angle: str = "",
    camera: str = "",
    quality: str = "",
) -> str:
    """Replace ``{angle}`` ``{camera}`` ``{quality}`` in an output folder template."""
    raw = (template or "").strip() or DEFAULT_OUTPUT_DIRECTORY
    quality_key = (quality or "").strip() or DEFAULT_QUALITY
    return (
        raw.replace("{angle}", (angle or DEFAULT_ANGLE))
        .replace("{camera}", (camera or "").strip() or DEFAULT_CAMERA)
        .replace("{quality}", quality_key.lower())
    )


def product_extent(
    mins: tuple[float, float, float],
    maxs: tuple[float, float, float],
) -> float:
    return max(
        maxs[0] - mins[0],
        maxs[1] - mins[1],
        maxs[2] - mins[2],
        MIN_EXTENT,
    )


def _as_angle(slug: str) -> AngleId | None:
    key = (slug or "").strip()
    if key == "front":
        return "front"
    if key == "three_quarter":
        return "three_quarter"
    if key == "top":
        return "top"
    return None


def angle_world_offset(slug: str, extent: float) -> tuple[float, float, float]:
    """World-space camera offset for a catalog angle."""
    key = _as_angle(slug)
    if key is None:
        raise RuntimeError(f"unhandled catalog angle: {slug or 'angle'}")
    span = max(float(extent), MIN_EXTENT)
    if key == "front":
        factors = ANGLE_OFFSETS["front"]
    elif key == "three_quarter":
        factors = ANGLE_OFFSETS["three_quarter"]
    elif key == "top":
        factors = ANGLE_OFFSETS["top"]
    else:
        unreachable: Never = key
        raise RuntimeError(f"unhandled catalog angle: {unreachable}")
    dx, dy, dz = factors
    return (dx * span, dy * span, dz * span)


def standard_angle_jobs() -> tuple[BatchJob, ...]:
    jobs = []
    for slug, label in STANDARD_ANGLES:
        jobs.append(BatchJob(kind="angle", slug=slug, label=label))
    return tuple(jobs)


def shot_jobs(names: Iterable[str]) -> tuple[BatchJob, ...]:
    jobs = []
    for raw in names:
        name = (raw or "").strip()
        if not name:
            continue
        slug = slugify(name)
        jobs.append(
            BatchJob(kind="shot", slug=slug, label=name, shot_name=name)
        )
    return tuple(jobs)


def plan_problem_message(kind: PlanProblemKind) -> str:
    if kind == "nothing":
        return BATCH_NOTHING
    if kind == "no_product":
        return BATCH_NO_MESH
    if kind == "no_camera":
        return BATCH_NO_CAMERA
    if kind == "no_shots":
        return BATCH_NO_SHOTS
    unreachable: Never = kind
    raise RuntimeError(f"unhandled batch plan problem: {unreachable}")


def classify_plan(
    *,
    include_angles: bool,
    include_shots: bool,
    shot_names: Sequence[str],
    has_product: bool,
    has_camera: bool,
) -> PlanProblemKind | None:
    want_angles = bool(include_angles)
    want_shots = bool(include_shots)
    if not want_angles and not want_shots:
        return "nothing"
    if want_angles and not has_product:
        return "no_product"
    if want_angles and not has_camera:
        return "no_camera"
    named = [name for name in shot_names if (name or "").strip()]
    if want_shots and not named:
        return "no_shots"
    return None


def plan_batch(
    *,
    include_angles: bool,
    include_shots: bool,
    shot_names: Sequence[str] = (),
    has_product: bool,
    has_camera: bool,
) -> tuple[BatchPlan | None, str | None]:
    problem = classify_plan(
        include_angles=include_angles,
        include_shots=include_shots,
        shot_names=shot_names,
        has_product=has_product,
        has_camera=has_camera,
    )
    if problem is not None:
        return None, plan_problem_message(problem)
    jobs: list[BatchJob] = []
    if include_angles:
        jobs.extend(standard_angle_jobs())
    if include_shots:
        jobs.extend(shot_jobs(shot_names))
    if not jobs:
        return None, plan_problem_message("nothing")
    return (
        BatchPlan(
            jobs=tuple(jobs),
            include_angles=bool(include_angles),
            include_shots=bool(include_shots),
        ),
        None,
    )


def progress_message(index: int, total: int, job: BatchJob) -> str:
    return f"Batch {index}/{total}: {job.label}"


def done_message(
    ok: int,
    total: int,
    last_dir: str = "",
    errors: Sequence[str] = (),
) -> str:
    if errors:
        first = (errors[0] or "").strip() or BATCH_RENDER_FAILED
        return f"Batch export {ok}/{total} — {first}"
    if last_dir:
        return f"Batch export {ok}/{total} → {last_dir}"
    return f"Batch export {ok}/{total}"
