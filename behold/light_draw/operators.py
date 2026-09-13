# SPDX-License-Identifier: GPL-3.0-or-later
"""Modal light placement: Reflect, Direct, Orbit."""

from __future__ import annotations

from typing import Optional

import bpy
from bpy.types import Context, Event, Object, Operator, SpaceView3D
from bpy_extras import view3d_utils
from mathutils import Vector


PREFIX = "BEHOLD"
MODES = ("REFLECT", "DIRECT", "ORBIT")


def ray_cast(context: Context, event: Event) -> tuple[Optional[Vector], Optional[Vector]]:
    region = context.region
    rv3d = context.region_data
    if region is None or rv3d is None:
        return None, None

    coord = (event.mouse_region_x, event.mouse_region_y)
    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)
    depsgraph = context.evaluated_depsgraph_get()
    result, location, normal, _index, _obj, _matrix = context.scene.ray_cast(
        depsgraph, ray_origin, view_vector
    )
    if not result:
        return None, None
    return location.copy(), normal.normalized()


def studio_lights() -> list[Object]:
    lights = [
        obj
        for obj in bpy.data.objects
        if obj.type == "LIGHT" and obj.name.startswith(PREFIX)
    ]
    return lights or [obj for obj in bpy.data.objects if obj.type == "LIGHT"]


def active_light(context: Context) -> Optional[Object]:
    obj = context.active_object
    if obj is not None and obj.type == "LIGHT":
        return obj
    lights = studio_lights()
    return lights[0] if lights else None


def ensure_draw_light(context: Context) -> Object:
    light = active_light(context)
    if light is not None:
        return light

    coll = bpy.data.collections.get("BEHOLD_Studio")
    data = bpy.data.lights.new(name=f"{PREFIX}_DrawKey", type="AREA")
    data.shape = "RECTANGLE"
    data.size = 1.0
    data.size_y = 0.75
    data.energy = 200.0
    light = bpy.data.objects.new(f"{PREFIX}_DrawKey", data)
    if coll is not None:
        coll.objects.link(light)
    else:
        context.scene.collection.objects.link(light)
    context.view_layer.objects.active = light
    return light


def aim_light(light: Object, location: Vector, target: Vector) -> None:
    direction = target - location
    if direction.length < 1e-6:
        return
    light.location = location
    light.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def reflect_position(hit: Vector, normal: Vector, view_dir: Vector, distance: float) -> Vector:
    to_camera = (-view_dir).normalized()
    reflected = (2.0 * normal.dot(to_camera) * normal - to_camera).normalized()
    return hit + reflected * distance


def direct_position(hit: Vector, normal: Vector, distance: float) -> Vector:
    return hit + normal.normalized() * distance


def set_solo(light: Object, enabled: bool, cache: dict) -> None:
    if enabled:
        if "hide" not in cache:
            cache["hide"] = {}
            for obj in bpy.data.objects:
                if obj.type == "LIGHT" and obj != light:
                    cache["hide"][obj.name] = (obj.hide_viewport, obj.hide_render)
                    obj.hide_viewport = True
                    obj.hide_render = True
    else:
        for name, (hide_v, hide_r) in cache.pop("hide", {}).items():
            obj = bpy.data.objects.get(name)
            if obj is not None:
                obj.hide_viewport = hide_v
                obj.hide_render = hide_r


def adjust_energy(light: Object, factor: float) -> None:
    light.data.energy = max(0.01, light.data.energy * factor)


def adjust_size(light: Object, factor: float) -> None:
    data = light.data
    if hasattr(data, "size"):
        data.size = max(0.05, data.size * factor)
    if hasattr(data, "size_y"):
        data.size_y = max(0.05, data.size_y * factor)


class BEHOLD_OT_light_draw(Operator):
    bl_idname = "behold.light_draw"
    bl_label = "Light Draw"
    bl_description = "Place and aim lights by pointing: Reflect, Direct, or Orbit"
    bl_options = {"REGISTER", "UNDO"}

    def invoke(self, context: Context, _event: Event):
        if context.space_data is None or not isinstance(context.space_data, SpaceView3D):
            self.report({"ERROR"}, "Light Draw needs a 3D Viewport")
            return {"CANCELLED"}

        settings = context.scene.behold
        self._mode = settings.light_draw_mode
        self._distance = max(0.2, settings.light_draw_distance)
        self._solo = False
        self._solo_cache: dict = {}
        self._orbit_center: Optional[Vector] = None
        self._orbit_radius = self._distance
        self._dragging = False
        self._light = ensure_draw_light(context)
        self._timer = context.window_manager.event_timer_add(0.05, window=context.window)
        context.window_manager.modal_handler_add(self)
        self.report(
            {"INFO"},
            "Light Draw — LMB drag aim | Wheel power | Shift+Wheel size | "
            "Ctrl+Wheel distance | 1/2/3 mode | S solo | F false color | Esc exit",
        )
        return {"RUNNING_MODAL"}

    def modal(self, context: Context, event: Event):
        light = getattr(self, "_light", None)
        if light is None or light.name not in bpy.data.objects:
            self._cleanup(context)
            self.report({"WARNING"}, "Light Draw cancelled — light missing")
            return {"CANCELLED"}

        settings = context.scene.behold

        if event.type in {"ESC", "RIGHTMOUSE"} and event.value == "PRESS":
            self._cleanup(context)
            self.report({"INFO"}, "Light Draw finished")
            return {"FINISHED"}

        if event.type == "ONE" and event.value == "PRESS":
            self._mode = "REFLECT"
            settings.light_draw_mode = "REFLECT"
            self.report({"INFO"}, "Mode: Reflect")
            return {"RUNNING_MODAL"}
        if event.type == "TWO" and event.value == "PRESS":
            self._mode = "DIRECT"
            settings.light_draw_mode = "DIRECT"
            self.report({"INFO"}, "Mode: Direct")
            return {"RUNNING_MODAL"}
        if event.type == "THREE" and event.value == "PRESS":
            self._mode = "ORBIT"
            settings.light_draw_mode = "ORBIT"
            hit, _normal = ray_cast(context, event)
            if hit is not None:
                self._orbit_center = hit
                self._orbit_radius = max(0.2, (light.location - hit).length)
            self.report({"INFO"}, "Mode: Orbit")
            return {"RUNNING_MODAL"}

        if event.type == "S" and event.value == "PRESS":
            self._solo = not self._solo
            set_solo(light, self._solo, self._solo_cache)
            self.report({"INFO"}, "Solo ON" if self._solo else "Solo OFF")
            return {"RUNNING_MODAL"}

        if event.type == "F" and event.value == "PRESS":
            settings.false_color = not settings.false_color
            try:
                bpy.ops.behold.apply_exposure()
            except Exception:  # noqa: BLE001
                pass
            return {"RUNNING_MODAL"}

        if event.type == "WHEELUPMOUSE":
            if event.ctrl:
                self._distance *= 1.1
                settings.light_draw_distance = self._distance
            elif event.shift:
                adjust_size(light, 1.1)
            else:
                adjust_energy(light, 1.15)
            return {"RUNNING_MODAL"}
        if event.type == "WHEELDOWNMOUSE":
            if event.ctrl:
                self._distance = max(0.1, self._distance / 1.1)
                settings.light_draw_distance = self._distance
            elif event.shift:
                adjust_size(light, 1 / 1.1)
            else:
                adjust_energy(light, 1 / 1.15)
            return {"RUNNING_MODAL"}

        if event.type == "LEFTMOUSE" and event.value == "PRESS":
            self._dragging = True
            self._update_aim(context, event, light)
            return {"RUNNING_MODAL"}
        if event.type == "LEFTMOUSE" and event.value == "RELEASE":
            self._dragging = False
            return {"RUNNING_MODAL"}

        if self._dragging and event.type in {"MOUSEMOVE", "INBETWEEN_MOUSEMOVE", "TIMER"}:
            self._update_aim(context, event, light)
            return {"RUNNING_MODAL"}

        return {"PASS_THROUGH"}

    def _update_aim(self, context: Context, event: Event, light: Object) -> None:
        region = context.region
        rv3d = context.region_data
        if region is None or rv3d is None:
            return

        hit, normal = ray_cast(context, event)
        if hit is None or normal is None:
            return

        coord = (event.mouse_region_x, event.mouse_region_y)
        view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)

        if self._mode == "REFLECT":
            location = reflect_position(hit, normal, view_vector, self._distance)
            aim_light(light, location, hit)
            return

        if self._mode == "DIRECT":
            location = direct_position(hit, normal, self._distance)
            aim_light(light, location, hit)
            return

        center = self._orbit_center or hit
        self._orbit_center = center
        offset = hit - center
        flat = Vector((offset.x, offset.y, 0.0))
        if flat.length < 1e-4:
            flat = Vector((light.location.x - center.x, light.location.y - center.y, 0.0))
        if flat.length < 1e-4:
            flat = Vector((1.0, 0.0, 0.0))
        direction = flat.normalized()
        radius = self._orbit_radius or self._distance
        elev = light.location.z - center.z
        if abs(elev) < 1e-3:
            elev = radius * 0.35
        location = center + direction * radius
        location.z = center.z + elev
        aim_light(light, location, center)

    def _cleanup(self, context: Context) -> None:
        if getattr(self, "_solo", False):
            set_solo(self._light, False, self._solo_cache)
            self._solo = False
        timer = getattr(self, "_timer", None)
        if timer is not None:
            context.window_manager.event_timer_remove(timer)
            self._timer = None


class BEHOLD_OT_light_draw_cycle_mode(Operator):
    bl_idname = "behold.light_draw_cycle_mode"
    bl_label = "Cycle Light Draw Mode"
    bl_description = "Cycle Reflect → Direct → Orbit"
    bl_options = {"REGISTER"}

    def execute(self, context: Context):
        settings = context.scene.behold
        order = list(MODES)
        idx = order.index(settings.light_draw_mode) if settings.light_draw_mode in order else 0
        settings.light_draw_mode = order[(idx + 1) % len(order)]
        self.report({"INFO"}, f"Light Draw mode: {settings.light_draw_mode.title()}")
        return {"FINISHED"}


CLASSES = (
    BEHOLD_OT_light_draw,
    BEHOLD_OT_light_draw_cycle_mode,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
