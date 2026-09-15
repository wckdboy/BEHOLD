# SPDX-License-Identifier: GPL-3.0-or-later
"""Light & shadow linking lite — Cycles receiver / blocker collections.

No Blender import. Light Wrangler uses L / Shift+L in a modal (add →
exclude → remove). This cut is selection + three Lights buttons: Link
Selected (same cycle), Unlink, Solo product. Shadow linking uses the
stable 5.2 ``blocker_collection`` API when present. Procedural gobos are
1.1.0; IES libraries stay out of scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Mapping, Never, Sequence

from .camera_ids import is_studio_mesh_name
from .light_ids import display_light_name

KindId = Literal["LIGHT", "SHADOW"]
LinkState = Literal["INCLUDE", "EXCLUDE"]
ActionId = Literal["LINK", "EXCLUDE", "UNLINK", "CYCLE", "SOLO"]

DEFAULT_KIND: KindId = "LIGHT"
INCLUDE: LinkState = "INCLUDE"
EXCLUDE: LinkState = "EXCLUDE"

COLLECTION_PREFIX = {
    "LIGHT": "BEHOLD_LL",
    "SHADOW": "BEHOLD_SL",
}

SUPPORTED_ENGINES = frozenset(
    {
        "CYCLES",
        "BLENDER_EEVEE",
        "BLENDER_EEVEE_NEXT",
    }
)
SKIP_OBJECT_TYPES = frozenset({"LIGHT", "CAMERA", "SPEAKER"})

NO_LINKING_API = (
    "Light linking needs Blender 4.2+ with Cycles collections — "
    "update Blender, then Link Selected"
)
NO_LINKING_ENGINE = (
    "Light linking needs Cycles or EEVEE — switch the render engine, then Link Selected"
)
NO_SHADOW_API = (
    "Shadow linking is not on this Blender — update to 5.2, then try Shadows"
)
NO_SELECTION = "No objects selected — select meshes to link, or Solo product"
NO_PRODUCT_TO_SOLO = "No product to solo — select the mesh or Import Product"
LINKING_FAILED = (
    "Could not update light linking — check the collection and try Link Selected again"
)
UNKNOWN_KIND = "Unknown linking kind — pick Light or Shadow"


@dataclass(frozen=True)
class ObjectRow:
    name: str
    ob_type: str
    tagged_product: bool = False
    selected: bool = False


def kind_enum_items() -> tuple[tuple[str, str, str], ...]:
    return (
        ("LIGHT", "Light", "Receiver collection — which objects this light illuminates"),
        ("SHADOW", "Shadow", "Blocker collection — which objects cast shadows from this light"),
    )


def is_kind(value: str) -> bool:
    return value in ("LIGHT", "SHADOW")


def normalize_kind(value: str, default: KindId = DEFAULT_KIND) -> KindId:
    raw = (value or "").strip()
    if raw == "LIGHT":
        return "LIGHT"
    if raw == "SHADOW":
        return "SHADOW"
    if raw == "":
        return default
    return default


def kind_label(kind: KindId) -> str:
    if kind == "LIGHT":
        return "light"
    if kind == "SHADOW":
        return "shadow"
    unreachable: Never = kind
    raise RuntimeError(f"unhandled linking kind: {unreachable}")


def collection_attr(kind: KindId) -> str:
    if kind == "LIGHT":
        return "receiver_collection"
    if kind == "SHADOW":
        return "blocker_collection"
    unreachable: Never = kind
    raise RuntimeError(f"unhandled linking kind: {unreachable}")


def collection_prefix(kind: KindId) -> str:
    if kind == "LIGHT":
        return COLLECTION_PREFIX["LIGHT"]
    if kind == "SHADOW":
        return COLLECTION_PREFIX["SHADOW"]
    unreachable: Never = kind
    raise RuntimeError(f"unhandled linking kind: {unreachable}")


def collection_name(light_name: str, kind: KindId) -> str:
    display = display_light_name(light_name).replace(" ", "_") or "Light"
    return f"{collection_prefix(kind)}_{display}"


def is_owned_collection_name(name: str) -> bool:
    base = (name or "").split(".", 1)[0]
    return base.startswith(COLLECTION_PREFIX["LIGHT"] + "_") or base.startswith(
        COLLECTION_PREFIX["SHADOW"] + "_"
    )


def is_supported_engine(engine: str) -> bool:
    return (engine or "").strip().upper() in SUPPORTED_ENGINES


def linking_api_ok(*, has_light_linking: bool, has_receiver: bool) -> bool:
    return bool(has_light_linking and has_receiver)


def shadow_api_ok(*, has_blocker: bool) -> bool:
    return bool(has_blocker)


def capability_problem(
    *,
    engine: str,
    has_light_linking: bool,
    has_receiver: bool,
    has_blocker: bool,
    kind: KindId,
) -> str | None:
    if not linking_api_ok(has_light_linking=has_light_linking, has_receiver=has_receiver):
        return NO_LINKING_API
    if not is_supported_engine(engine):
        return NO_LINKING_ENGINE
    if kind == "LIGHT":
        return None
    if kind == "SHADOW":
        if not shadow_api_ok(has_blocker=has_blocker):
            return NO_SHADOW_API
        return None
    unreachable: Never = kind
    raise RuntimeError(f"unhandled linking kind: {unreachable}")


def normalize_state(value: str | None) -> LinkState | None:
    if value is None:
        return None
    raw = (value or "").strip().upper()
    if raw == INCLUDE:
        return INCLUDE
    if raw == EXCLUDE:
        return EXCLUDE
    return None


def cycle_link_state(current: str | None) -> LinkState | None:
    """Wrangler L: missing → include → exclude → remove."""
    state = normalize_state(current)
    if state is None:
        return INCLUDE
    if state == INCLUDE:
        return EXCLUDE
    if state == EXCLUDE:
        return None
    unreachable: Never = state
    raise RuntimeError(f"unhandled link state: {unreachable}")


def apply_member_action(
    members: Mapping[str, str],
    names: Sequence[str],
    action: ActionId,
) -> dict[str, str]:
    result = {key: value for key, value in members.items() if normalize_state(value)}
    if action == "SOLO":
        return result
    for name in names:
        key = (name or "").strip()
        if not key:
            continue
        if action == "LINK":
            result[key] = INCLUDE
        elif action == "EXCLUDE":
            result[key] = EXCLUDE
        elif action == "UNLINK":
            result.pop(key, None)
        elif action == "CYCLE":
            nxt = cycle_link_state(result.get(key))
            if nxt is None:
                result.pop(key, None)
            else:
                result[key] = nxt
        elif action == "SOLO":
            continue
        else:
            unreachable: Never = action
            raise RuntimeError(f"unhandled linking action: {unreachable}")
    return result


def solo_members(product_names: Sequence[str]) -> dict[str, str]:
    return {name: INCLUDE for name in product_names if (name or "").strip()}


def plan_collection_sync(
    current: Mapping[str, str],
    desired: Mapping[str, str],
) -> tuple[tuple[str, ...], tuple[str, ...], dict[str, str]]:
    """Names to link, names to unlink, and per-object INCLUDE/EXCLUDE writes."""
    current_names = set(current)
    desired_names = set(desired)
    to_link = tuple(sorted(desired_names - current_names))
    to_unlink = tuple(sorted(current_names - desired_names))
    state_updates = {
        name: desired[name]
        for name in sorted(desired_names)
        if current.get(name) != desired[name]
    }
    return to_link, to_unlink, state_updates


def is_link_target(*, name: str, ob_type: str, emitter_name: str) -> bool:
    if not (name or "").strip():
        return False
    if name == emitter_name:
        return False
    if ob_type in SKIP_OBJECT_TYPES:
        return False
    return True


def selected_target_names(
    rows: Iterable[ObjectRow],
    *,
    emitter_name: str,
) -> tuple[str, ...]:
    return tuple(
        row.name
        for row in rows
        if row.selected
        and is_link_target(
            name=row.name, ob_type=row.ob_type, emitter_name=emitter_name
        )
    )


def product_target_names(rows: Iterable[ObjectRow]) -> tuple[str, ...]:
    """Same preference as studio cameras: selection, tagged import, else non-studio."""
    items = list(rows)
    selected = tuple(
        row.name
        for row in items
        if row.selected
        and row.ob_type == "MESH"
        and not is_studio_mesh_name(row.name)
    )
    if selected:
        return selected
    tagged = tuple(
        row.name for row in items if row.tagged_product and row.ob_type == "MESH"
    )
    if tagged:
        return tagged
    return tuple(
        row.name
        for row in items
        if row.ob_type == "MESH" and not is_studio_mesh_name(row.name)
    )


def lookup_collection_entry(collection: object, name: str) -> object | None:
    """Duck-typed Collection.collection_objects[name] (Blender 4.2 / 5.2)."""
    entries = getattr(collection, "collection_objects", None)
    if entries is None:
        return None
    try:
        return entries[name]
    except (KeyError, TypeError, AttributeError, IndexError):
        pass
    try:
        getter = getattr(entries, "get", None)
        if callable(getter):
            found = getter(name)
            if found is not None:
                return found
    except (TypeError, AttributeError):
        pass
    try:
        iterator = list(entries)
    except TypeError:
        return None
    for entry in iterator:
        entry_name = getattr(entry, "name", None)
        if entry_name == name:
            return entry
        obj = getattr(entry, "object", None)
        if getattr(obj, "name", None) == name:
            return entry
    return None


def entry_state(entry: object | None) -> LinkState:
    if entry is None:
        return INCLUDE
    linking = getattr(entry, "light_linking", None)
    if linking is None:
        return INCLUDE
    return normalize_state(getattr(linking, "link_state", None)) or INCLUDE


def set_entry_state(entry: object, state: LinkState) -> bool:
    linking = getattr(entry, "light_linking", None)
    if linking is None or not hasattr(linking, "link_state"):
        return False
    linking.link_state = state
    return True


def members_from_collection(collection: object | None) -> dict[str, str]:
    if collection is None:
        return {}
    objects = getattr(collection, "objects", None)
    if objects is None:
        return {}
    members: dict[str, str] = {}
    try:
        iterator = list(objects)
    except TypeError:
        return {}
    for obj in iterator:
        name = getattr(obj, "name", "")
        if not name:
            continue
        members[name] = entry_state(lookup_collection_entry(collection, name))
    return members


def linked_message(
    kind: KindId,
    light_name: str,
    count: int,
    state: LinkState,
) -> str:
    display = display_light_name(light_name)
    label = kind_label(kind)
    if state == INCLUDE:
        return f"Linked {count} object(s) to {display} ({label})"
    if state == EXCLUDE:
        return f"Excluded {count} object(s) from {display} ({label})"
    unreachable: Never = state
    raise RuntimeError(f"unhandled link state: {unreachable}")


def cycled_message(kind: KindId, light_name: str, desired: Mapping[str, str]) -> str:
    display = display_light_name(light_name)
    label = kind_label(kind)
    if not desired:
        return f"Unlinked selected objects from {display} ({label})"
    included = sum(1 for state in desired.values() if state == INCLUDE)
    excluded = sum(1 for state in desired.values() if state == EXCLUDE)
    parts: list[str] = []
    if included:
        parts.append(f"{included} included")
    if excluded:
        parts.append(f"{excluded} excluded")
    detail = ", ".join(parts) or "updated"
    return f"Linking on {display} ({label}): {detail}"


def unlinked_message(
    kind: KindId,
    light_name: str,
    count: int,
    *,
    cleared: bool,
) -> str:
    display = display_light_name(light_name)
    label = kind_label(kind)
    if cleared:
        return f"Cleared {label} linking on {display}"
    return f"Unlinked {count} object(s) from {display} ({label})"


def solo_message(
    light_name: str,
    count: int,
    *,
    kinds: Sequence[KindId],
) -> str:
    display = display_light_name(light_name)
    labels = " + ".join(kind_label(kind) for kind in kinds)
    return f"Solo {count} product object(s) on {display} ({labels})"
