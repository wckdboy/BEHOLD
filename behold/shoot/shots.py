# SPDX-License-Identifier: GPL-3.0-or-later
"""Named shot presets — serialize / apply helpers (no Blender import).

A Shot is KeyShot-Studios-skinny: camera name, quality, turntable seconds,
HDRI path/strength/rotation (plus the cheap reflections-only knobs), backdrop
tone, and the output folder token template. It does not store meshes.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping, MutableMapping, Sequence

from ..studio.camera_ids import display_camera_name

SCHEMA_VERSION = 1
DEFAULT_SHOT_NAME = "Shot"
DEFAULT_QUALITY = "DRAFT"
DEFAULT_TONE = "WHITE"
DEFAULT_TURNTABLE_SECONDS = 6.0
DEFAULT_HDRI_STRENGTH = 1.0
DEFAULT_HDRI_ROTATION = 0.0
DEFAULT_HDRI_BACKGROUND = 0.0
DEFAULT_OUTPUT_DIRECTORY = "//behold_out/"

QUALITY_KEYS = ("DRAFT", "FINAL", "PRODUCT", "HERO")
TONE_KEYS = ("WHITE", "GREY", "BLACK")

EMPTY_NO_SHOTS_TITLE = "No shots yet"
EMPTY_NO_SHOTS_NEXT = "Add from the current camera, quality, and HDRI"
EMPTY_NO_SHOTS = f"{EMPTY_NO_SHOTS_TITLE} — {EMPTY_NO_SHOTS_NEXT}"
NO_SHOT_TO_APPLY = "No shot to apply — Add from the current setup"
NO_SHOT_TO_REMOVE = "No shot to remove — Add from the current setup"
NO_SHOT_TO_RENAME = "No shot to rename — Add from the current setup"
SHOT_NAME_EMPTY = "Shot needs a name — type a name and try again"

# Scene settings written on Apply. Never includes product mesh data.
SCENE_APPLY_KEYS = (
    "active_camera_name",
    "main_camera_name",
    "render_quality",
    "turntable_seconds",
    "hdri_strength",
    "hdri_rotation",
    "hdri_reflections_only",
    "hdri_background_strength",
    "hdri_filepath",
    "studio_backdrop_tone",
    "output_directory",
)

PAYLOAD_KEYS = (
    "schema",
    "name",
    "camera_name",
    "main_camera_name",
    "render_quality",
    "turntable_seconds",
    "hdri_filepath",
    "hdri_strength",
    "hdri_rotation",
    "hdri_reflections_only",
    "hdri_background_strength",
    "studio_backdrop_tone",
    "output_directory",
)


def sanitize_shot_name(name: str) -> str:
    cleaned = " ".join((name or "").split())
    return cleaned[:128]


def unique_shot_name(existing: Iterable[str], desired: str) -> str:
    """Return *desired* or *desired_001* so names stay unique."""
    base = sanitize_shot_name(desired) or DEFAULT_SHOT_NAME
    taken = {sanitize_shot_name(item) for item in existing if sanitize_shot_name(item)}
    if base not in taken:
        return base
    index = 1
    while True:
        candidate = f"{base}_{index:03d}"
        if candidate not in taken:
            return candidate
        index += 1


def default_shot_name(existing: Iterable[str], *, camera_name: str = "") -> str:
    """Prefer the camera's display name, else Shot / Shot_001."""
    raw = sanitize_shot_name(camera_name)
    base = display_camera_name(raw) if raw else DEFAULT_SHOT_NAME
    base = sanitize_shot_name(base) or DEFAULT_SHOT_NAME
    return unique_shot_name(existing, base)


def shot_name_taken(name: str) -> str:
    shown = sanitize_shot_name(name) or "that name"
    return f"Shot name “{shown}” is already used — pick another name"


def shot_saved_message(name: str) -> str:
    shown = sanitize_shot_name(name) or DEFAULT_SHOT_NAME
    return f"Shot saved: {shown}"


def shot_applied_message(name: str) -> str:
    shown = sanitize_shot_name(name) or DEFAULT_SHOT_NAME
    return f"Shot applied: {shown}"


def shot_renamed_message(old: str, new: str) -> str:
    return f"Shot renamed: {sanitize_shot_name(old)} → {sanitize_shot_name(new)}"


def shot_removed_message(name: str) -> str:
    shown = sanitize_shot_name(name) or DEFAULT_SHOT_NAME
    return f"Shot removed: {shown}"


def shot_has_hdri(payload: Mapping[str, Any]) -> bool:
    return bool(str(payload.get("hdri_filepath") or "").strip())


def empty_state(count: int) -> str | None:
    if count <= 0:
        return EMPTY_NO_SHOTS
    return None


def _get(src: Any, key: str, default: Any = "") -> Any:
    if isinstance(src, Mapping):
        return src.get(key, default)
    return getattr(src, key, default)


def _set(dest: Any, key: str, value: Any) -> None:
    if isinstance(dest, MutableMapping):
        dest[key] = value
        return
    setattr(dest, key, value)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _normalize_quality(value: Any) -> str:
    key = str(value or "").strip().upper()
    if key in QUALITY_KEYS:
        return key
    return DEFAULT_QUALITY


def _normalize_tone(value: Any) -> str:
    key = str(value or "").strip().upper()
    if key in TONE_KEYS:
        return key
    return DEFAULT_TONE


def deserialize_shot(data: Mapping[str, Any] | None) -> dict[str, Any]:
    """Coerce a mapping into a complete shot payload."""
    src = data or {}
    camera = str(_get(src, "camera_name") or _get(src, "active_camera_name") or "").strip()
    main = str(_get(src, "main_camera_name") or camera).strip()
    seconds = _get(src, "turntable_seconds", DEFAULT_TURNTABLE_SECONDS)
    try:
        seconds_f = float(seconds)
    except (TypeError, ValueError):
        seconds_f = DEFAULT_TURNTABLE_SECONDS
    strength = _get(src, "hdri_strength", DEFAULT_HDRI_STRENGTH)
    rotation = _get(src, "hdri_rotation", DEFAULT_HDRI_ROTATION)
    background = _get(src, "hdri_background_strength", DEFAULT_HDRI_BACKGROUND)
    try:
        strength_f = float(strength)
    except (TypeError, ValueError):
        strength_f = DEFAULT_HDRI_STRENGTH
    try:
        rotation_f = float(rotation)
    except (TypeError, ValueError):
        rotation_f = DEFAULT_HDRI_ROTATION
    try:
        background_f = float(background)
    except (TypeError, ValueError):
        background_f = DEFAULT_HDRI_BACKGROUND
    output = str(_get(src, "output_directory", DEFAULT_OUTPUT_DIRECTORY) or "").strip()
    name = sanitize_shot_name(str(_get(src, "name") or ""))
    return {
        "schema": SCHEMA_VERSION,
        "name": name,
        "camera_name": camera,
        "main_camera_name": main or camera,
        "render_quality": _normalize_quality(_get(src, "render_quality", DEFAULT_QUALITY)),
        "turntable_seconds": _clamp(seconds_f, 1.0, 60.0),
        "hdri_filepath": str(_get(src, "hdri_filepath") or "").strip(),
        "hdri_strength": _clamp(strength_f, 0.0, 100.0),
        "hdri_rotation": _clamp(rotation_f, -360.0, 360.0),
        "hdri_reflections_only": _as_bool(_get(src, "hdri_reflections_only", False)),
        "hdri_background_strength": _clamp(background_f, 0.0, 100.0),
        "studio_backdrop_tone": _normalize_tone(
            _get(src, "studio_backdrop_tone", DEFAULT_TONE)
        ),
        "output_directory": output or DEFAULT_OUTPUT_DIRECTORY,
    }


def serialize_shot(payload: Mapping[str, Any]) -> dict[str, Any]:
    """JSON-safe dict with a stable key order."""
    data = deserialize_shot(payload)
    return {key: data[key] for key in PAYLOAD_KEYS}


def snapshot_from_mapping(
    src: Any,
    *,
    name: str = "",
    camera_name: str | None = None,
) -> dict[str, Any]:
    """Capture a shot from scene settings or a shot item."""
    captured = {
        "name": name or _get(src, "name") or "",
        "camera_name": (
            camera_name
            if camera_name is not None
            else (_get(src, "camera_name") or _get(src, "active_camera_name") or "")
        ),
        "main_camera_name": _get(src, "main_camera_name") or "",
        "render_quality": _get(src, "render_quality", DEFAULT_QUALITY),
        "turntable_seconds": _get(src, "turntable_seconds", DEFAULT_TURNTABLE_SECONDS),
        "hdri_filepath": _get(src, "hdri_filepath") or "",
        "hdri_strength": _get(src, "hdri_strength", DEFAULT_HDRI_STRENGTH),
        "hdri_rotation": _get(src, "hdri_rotation", DEFAULT_HDRI_ROTATION),
        "hdri_reflections_only": _get(src, "hdri_reflections_only", False),
        "hdri_background_strength": _get(
            src, "hdri_background_strength", DEFAULT_HDRI_BACKGROUND
        ),
        "studio_backdrop_tone": _get(src, "studio_backdrop_tone", DEFAULT_TONE),
        "output_directory": _get(src, "output_directory", DEFAULT_OUTPUT_DIRECTORY),
    }
    return serialize_shot(captured)


def scene_values(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Fields written onto ``scene.behold``. Camera objects are applied separately."""
    data = deserialize_shot(payload)
    camera = data["camera_name"]
    main = data["main_camera_name"] or camera
    return {
        "active_camera_name": camera,
        "main_camera_name": main,
        "render_quality": data["render_quality"],
        "turntable_seconds": data["turntable_seconds"],
        "hdri_strength": data["hdri_strength"],
        "hdri_rotation": data["hdri_rotation"],
        "hdri_reflections_only": data["hdri_reflections_only"],
        "hdri_background_strength": data["hdri_background_strength"],
        "hdri_filepath": data["hdri_filepath"],
        "studio_backdrop_tone": data["studio_backdrop_tone"],
        "output_directory": data["output_directory"],
    }


def item_values(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Fields stored on a CollectionProperty shot item."""
    data = deserialize_shot(payload)
    return {
        "name": data["name"],
        "camera_name": data["camera_name"],
        "main_camera_name": data["main_camera_name"],
        "render_quality": data["render_quality"],
        "turntable_seconds": data["turntable_seconds"],
        "hdri_filepath": data["hdri_filepath"],
        "hdri_strength": data["hdri_strength"],
        "hdri_rotation": data["hdri_rotation"],
        "hdri_reflections_only": data["hdri_reflections_only"],
        "hdri_background_strength": data["hdri_background_strength"],
        "studio_backdrop_tone": data["studio_backdrop_tone"],
        "output_directory": data["output_directory"],
    }


def apply_shot_to_mapping(shot: Mapping[str, Any], dest: Any) -> dict[str, Any]:
    """Write shot fields onto a mapping / settings object. Leaves other keys alone."""
    payload = deserialize_shot(shot)
    written = scene_values(payload)
    for key in SCENE_APPLY_KEYS:
        _set(dest, key, written[key])
    if isinstance(dest, MutableMapping):
        if "camera_name" in dest:
            dest["camera_name"] = payload["camera_name"]
    elif hasattr(dest, "camera_name"):
        setattr(dest, "camera_name", payload["camera_name"])
    return {
        "ok": True,
        "payload": payload,
        "written": written,
        "has_hdri": shot_has_hdri(payload),
        "camera_name": payload["camera_name"],
    }


def find_shot_index(shots: Sequence[Mapping[str, Any]], name: str) -> int:
    needle = sanitize_shot_name(name)
    if not needle:
        return -1
    for index, item in enumerate(shots):
        if sanitize_shot_name(str(_get(item, "name") or "")) == needle:
            return index
    return -1


def add_shot(
    shots: list[dict[str, Any]],
    payload: Mapping[str, Any],
    *,
    name: str = "",
) -> dict[str, Any]:
    """Append a uniquified copy of *payload* onto a list of shot dicts."""
    existing = [str(_get(item, "name") or "") for item in shots]
    data = deserialize_shot(payload)
    desired = sanitize_shot_name(name) or data["name"] or default_shot_name(
        existing, camera_name=data["camera_name"]
    )
    data["name"] = unique_shot_name(existing, desired)
    stored = serialize_shot(data)
    shots.append(stored)
    return {"ok": True, "shot": stored, "index": len(shots) - 1, "name": stored["name"]}


def remove_shot(shots: list[dict[str, Any]], name: str) -> dict[str, Any]:
    index = find_shot_index(shots, name)
    if index < 0:
        return {"ok": False, "message": NO_SHOT_TO_REMOVE}
    removed = shots.pop(index)
    return {"ok": True, "shot": removed, "index": index, "name": removed["name"]}


def rename_shot(shots: list[dict[str, Any]], name: str, new_name: str) -> dict[str, Any]:
    index = find_shot_index(shots, name)
    if index < 0:
        return {"ok": False, "message": NO_SHOT_TO_RENAME}
    desired = sanitize_shot_name(new_name)
    if not desired:
        return {"ok": False, "message": SHOT_NAME_EMPTY}
    others = [
        str(_get(item, "name") or "")
        for i, item in enumerate(shots)
        if i != index
    ]
    if sanitize_shot_name(desired) in {sanitize_shot_name(item) for item in others}:
        return {"ok": False, "message": shot_name_taken(desired)}
    old = str(shots[index]["name"])
    shots[index] = serialize_shot({**shots[index], "name": desired})
    return {
        "ok": True,
        "shot": shots[index],
        "index": index,
        "old_name": old,
        "name": desired,
    }


def clamp_active_index(count: int, index: int) -> int:
    if count <= 0:
        return -1
    if index < 0:
        return 0
    if index >= count:
        return count - 1
    return index
