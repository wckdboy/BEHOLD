# SPDX-License-Identifier: GPL-3.0-or-later
"""Seed Key / Fill / Rim when Build Studio runs (Lighting add-on)."""

from __future__ import annotations

import bpy
from bpy.types import Context
from mathutils import Vector

from . import lights as light_lib
from .common.fit import (
    FILL_OFFSET,
    KEY_OFFSET,
    RIM_OFFSET,
    fit_from_aabb,
)
from .common.geom import bounds_world, ensure_collection, selected_meshes
from .common.light_ids import PREFIX
from .common.scene import studio as studio_settings
from .common.tones import kelvin_to_rgb


def _remove_named_lights(names: tuple[str, ...]) -> None:
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is not None and obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)


def seed_studio_lights(context: Context) -> int:
    settings = context.scene.behold_lighting
    targets = selected_meshes(context)
    if not targets:
        return 0
    mins, maxs = bounds_world(targets)
    studio = studio_settings(context.scene)
    margin = float(getattr(studio, "studio_margin", 2.0) if studio is not None else 2.0)
    fit = fit_from_aabb(
        (mins.x, mins.y, mins.z),
        (maxs.x, maxs.y, maxs.z),
        margin=margin,
    )
    floor_center = Vector(((mins.x + maxs.x) * 0.5, (mins.y + maxs.y) * 0.5, mins.z))
    product_center = Vector(
        (floor_center.x, floor_center.y, mins.z + fit.height * 0.5)
    )
    rig_size = fit.rig_size
    coll = ensure_collection(context)
    color = kelvin_to_rgb(settings.light_temperature)
    key_energy = 250.0 * rig_size * settings.key_power
    _remove_named_lights((f"{PREFIX}_Key", f"{PREFIX}_Fill", f"{PREFIX}_Rim"))
    key_loc = product_center + Vector(fit.scaled_offset(KEY_OFFSET))
    fill_loc = product_center + Vector(fit.scaled_offset(FILL_OFFSET))
    rim_loc = product_center + Vector(fit.scaled_offset(RIM_OFFSET))
    created = 0
    if settings.studio_light_rig == "SOFTBOX":
        light_lib.make_area_light(
            f"{PREFIX}_Key", coll, key_loc, product_center, rig_size * 1.8, key_energy, color
        )
        light_lib.make_area_light(
            f"{PREFIX}_Fill",
            coll,
            fill_loc,
            product_center,
            rig_size * 1.4,
            key_energy * settings.fill_ratio,
            color,
        )
        created = 2
    else:
        light_lib.make_area_light(
            f"{PREFIX}_Key", coll, key_loc, product_center, rig_size * 1.1, key_energy, color
        )
        light_lib.make_area_light(
            f"{PREFIX}_Fill",
            coll,
            fill_loc,
            product_center,
            rig_size * 0.9,
            key_energy * settings.fill_ratio,
            color,
        )
        light_lib.make_area_light(
            f"{PREFIX}_Rim",
            coll,
            rim_loc,
            product_center,
            rig_size * 0.7,
            key_energy * settings.rim_ratio,
            color,
        )
        created = 3
    key = bpy.data.objects.get(f"{PREFIX}_Key")
    if key is not None and key.type == "LIGHT":
        light_lib.set_active_behold_light(context, key)
    return created


def refresh_light_mixer(context: Context) -> int:
    settings = context.scene.behold_lighting
    color = kelvin_to_rgb(settings.light_temperature)
    targets = selected_meshes(context)
    size = 1.0
    if targets:
        mins, maxs = bounds_world(targets)
        studio = studio_settings(context.scene)
        margin = float(getattr(studio, "studio_margin", 2.0) if studio is not None else 2.0)
        size = fit_from_aabb(
            (mins.x, mins.y, mins.z),
            (maxs.x, maxs.y, maxs.z),
            margin=margin,
        ).rig_size
    key_energy = 250.0 * size * settings.key_power
    mapping = {
        f"{PREFIX}_Key": key_energy,
        f"{PREFIX}_Fill": key_energy * settings.fill_ratio,
        f"{PREFIX}_Rim": key_energy * settings.rim_ratio,
    }
    updated = 0
    for name, energy in mapping.items():
        obj = bpy.data.objects.get(name)
        if obj is not None and obj.type == "LIGHT":
            obj.data.energy = energy
            obj.data.color = color
            updated += 1
    updated += light_lib.apply_temperature_to_extras(context)
    return updated
