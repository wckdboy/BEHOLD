# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply ground contact / shadow catcher after Build Studio."""

from __future__ import annotations

from typing import Any, Sequence

import bpy
from bpy.types import Context, Material, Node, NodeSocket, NodeTree, Object
from mathutils import Vector

from . import catcher as spec
from . import lights as light_lib
from .camera_ids import is_studio_mesh_name
from .fit import MIN_EXTENT, fit_from_aabb
from ..cad.material_assist import is_behold_product

_SocketKey = str | int


def _link_exclusive(obj: Object, coll: bpy.types.Collection) -> None:
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    if obj.name not in coll.objects:
        coll.objects.link(obj)


def probe_api(obj: object | None = None) -> dict[str, bool]:
    if obj is not None:
        return {"has_shadow_catcher": hasattr(obj, "is_shadow_catcher")}
    return {"has_shadow_catcher": hasattr(bpy.types.Object, "is_shadow_catcher")}


def _result(ok: bool, message: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "message": message}
    payload.update(extra)
    return payload


def _bounds_tuple(
    objects: Sequence[Object],
) -> tuple[tuple[float, float, float], tuple[float, float, float]] | None:
    if not objects:
        return None
    mins, maxs = light_lib.bounds_world(list(objects))
    return (float(mins.x), float(mins.y), float(mins.z)), (
        float(maxs.x),
        float(maxs.y),
        float(maxs.z),
    )


def product_contact_meshes(context: Context) -> list[Object]:
    """Tagged product first, else non-studio meshes — not the cyclorama."""
    tagged = [
        obj
        for obj in context.scene.objects
        if obj.type == "MESH" and is_behold_product(obj)
    ]
    if tagged:
        return tagged
    selected = [
        obj
        for obj in context.selected_objects
        if obj.type == "MESH" and not is_studio_mesh_name(obj.name)
    ]
    if selected:
        return selected
    return [
        obj
        for obj in context.scene.objects
        if obj.type == "MESH" and not is_studio_mesh_name(obj.name)
    ]


def _socket(node: Node, side: str, key: _SocketKey) -> NodeSocket:
    sockets = node.outputs if side == "output" else node.inputs
    return sockets[key]


def _wire_plan(
    tree: NodeTree,
    nodes: tuple[spec.NodeSpec, ...],
    links: tuple[spec.LinkSpec, ...],
) -> dict[str, Node]:
    tree.nodes.clear()
    created: dict[str, Node] = {}
    for item in nodes:
        node = tree.nodes.new(item.bl_idname)
        node.name = item.name
        node.label = item.name
        created[item.key] = node
    for link in links:
        src = created[link.from_key]
        dst = created[link.to_key]
        tree.links.new(
            _socket(src, "output", link.from_socket),
            _socket(dst, "input", link.to_socket),
        )
    return created


def _set_vector_input(node: Node, name: str, value: tuple[float, float, float]) -> None:
    try:
        node.inputs[name].default_value = value
    except (KeyError, TypeError):
        pass


def _apply_eevee_blend(mat: Material) -> None:
    if hasattr(mat, "surface_render_method"):
        try:
            mat.surface_render_method = "BLENDED"
        except (TypeError, ValueError):
            pass
    if hasattr(mat, "blend_method"):
        try:
            mat.blend_method = "BLEND"
        except (TypeError, ValueError):
            pass
    if hasattr(mat, "shadow_method"):
        try:
            mat.shadow_method = "NONE"
        except (TypeError, ValueError):
            pass
    if hasattr(mat, "use_transparency_overlap"):
        try:
            mat.use_transparency_overlap = True
        except (TypeError, ValueError):
            pass


def _apply_node_graph(mat: Material, graph: spec.NodeGraph) -> None:
    mat.use_nodes = True
    tree = mat.node_tree
    if tree is None:
        return
    created = _wire_plan(tree, graph.nodes, graph.links)
    mapping = created.get("mapping")
    if mapping is not None and graph.mapping is not None:
        _set_vector_input(mapping, "Location", graph.mapping.location)
        _set_vector_input(mapping, "Scale", graph.mapping.scale)
    gradient = created.get("gradient")
    if (
        gradient is not None
        and graph.gradient_type is not None
        and hasattr(gradient, "gradient_type")
    ):
        try:
            gradient.gradient_type = graph.gradient_type
        except (TypeError, ValueError):
            pass
    math_node = created.get("math")
    if math_node is not None:
        if graph.math_operation and hasattr(math_node, "operation"):
            try:
                math_node.operation = graph.math_operation
            except (TypeError, ValueError):
                pass
        try:
            math_node.inputs[1].default_value = graph.math_value
        except (KeyError, TypeError, IndexError):
            pass
    diffuse = created.get("diffuse")
    if diffuse is not None:
        try:
            diffuse.inputs["Color"].default_value = graph.diffuse_color
        except (KeyError, TypeError):
            pass
    _apply_eevee_blend(mat)


def _ensure_material(name: str, graph: spec.NodeGraph) -> Material:
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name=name)
    _apply_node_graph(mat, graph)
    return mat


def _assign_material(obj: Object, mat: Material) -> None:
    data = getattr(obj, "data", None)
    if data is None or not hasattr(data, "materials"):
        return
    data.materials.clear()
    data.materials.append(mat)


def _visibility(
    obj: Object,
    *,
    catcher: bool,
    camera: bool,
    shadow: bool,
    glossy: bool,
) -> None:
    if hasattr(obj, "is_shadow_catcher"):
        try:
            obj.is_shadow_catcher = catcher
        except (TypeError, AttributeError):
            pass
    for name, value in (
        ("visible_camera", camera),
        ("visible_shadow", shadow),
        ("visible_diffuse", True),
        ("visible_glossy", glossy),
        ("visible_transmission", False),
        ("visible_volume_scatter", False),
    ):
        if hasattr(obj, name):
            try:
                setattr(obj, name, value)
            except (TypeError, AttributeError):
                pass


def _remove_named(*names: str) -> None:
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)


def _make_plane(
    name: str,
    coll: bpy.types.Collection,
    center: Vector,
    size: float,
) -> Object:
    half = max(float(size), spec.MIN_EXTENT) * 0.5
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(
        (
            (-half, -half, 0.0),
            (half, -half, 0.0),
            (half, half, 0.0),
            (-half, half, 0.0),
        ),
        (),
        ((0, 1, 2, 3),),
    )
    mesh.update()
    plane = bpy.data.objects.new(name, mesh)
    plane.location = (center.x, center.y, center.z)
    _link_exclusive(plane, coll)
    return plane


def _write_light_contact(context: Context, contact: spec.LightContact) -> int:
    updated = 0
    for light in light_lib.iter_behold_lights(context):
        data = light.data
        if not hasattr(data, "use_contact_shadow"):
            continue
        try:
            data.use_contact_shadow = contact.use_contact_shadow
        except (TypeError, AttributeError):
            continue
        if contact.use_contact_shadow:
            for name, value in (
                ("contact_shadow_distance", contact.distance),
                ("contact_shadow_bias", contact.bias),
                ("contact_shadow_thickness", contact.thickness),
            ):
                if hasattr(data, name):
                    try:
                        setattr(data, name, value)
                    except (TypeError, AttributeError):
                        pass
        updated += 1
    return updated


def _plan_from_context(
    context: Context,
    *,
    enabled: bool | None = None,
    floor_center: Vector | None = None,
    fit=None,
) -> tuple[spec.CatcherPlan, Vector, bpy.types.Collection] | dict[str, Any]:
    settings = getattr(context.scene, "behold", None)
    wanted = bool(enabled) if enabled is not None else bool(
        getattr(settings, "include_shadow_catcher", spec.DEFAULT_ENABLED)
    )
    backdrop = str(getattr(settings, "studio_backdrop", spec.DEFAULT_BACKDROP))
    coll = light_lib.ensure_collection(context)

    if fit is not None and floor_center is not None:
        plan = spec.plan_catcher(
            enabled=wanted,
            backdrop=backdrop,
            width=fit.width,
            depth=fit.depth,
            height=fit.height,
            floor_size=fit.catcher_size,
            has_shadow_catcher=probe_api()["has_shadow_catcher"],
        )
        if isinstance(plan, str):
            return _result(False, plan)
        return plan, floor_center, coll

    meshes = product_contact_meshes(context)
    bounds = _bounds_tuple(meshes)
    if bounds is None:
        if not wanted:
            dummy = spec.plan_catcher(
                enabled=False,
                backdrop=backdrop,
                width=MIN_EXTENT,
                depth=MIN_EXTENT,
                height=MIN_EXTENT,
                floor_size=MIN_EXTENT,
                has_shadow_catcher=probe_api()["has_shadow_catcher"],
            )
            if isinstance(dummy, str):
                return _result(False, dummy)
            return dummy, Vector((0.0, 0.0, 0.0)), coll
        return _result(False, spec.NO_PRODUCT_FOR_CATCHER)

    mins, maxs = bounds
    computed = fit_from_aabb(mins, maxs, margin=float(getattr(settings, "studio_margin", 2.0)))
    center = Vector(((mins[0] + maxs[0]) * 0.5, (mins[1] + maxs[1]) * 0.5, mins[2]))
    plan = spec.plan_catcher(
        enabled=wanted,
        backdrop=backdrop,
        width=computed.width,
        depth=computed.depth,
        height=computed.height,
        floor_size=computed.catcher_size,
        has_shadow_catcher=probe_api()["has_shadow_catcher"],
    )
    if isinstance(plan, str):
        return _result(False, plan)
    return plan, center, coll


def apply_ground_contact(
    context: Context,
    *,
    enabled: bool | None = None,
    coll: bpy.types.Collection | None = None,
    floor_center: Vector | None = None,
    fit=None,
) -> dict[str, Any]:
    """Build or tear down catcher plane / contact disc and light contact shadows."""
    prepared = _plan_from_context(
        context,
        enabled=enabled,
        floor_center=floor_center,
        fit=fit,
    )
    if isinstance(prepared, dict):
        return prepared
    plan, center, resolved_coll = prepared
    kit = coll if coll is not None else resolved_coll

    _remove_named(spec.CATCHER_OBJECT, spec.CONTACT_OBJECT)

    if not plan.enabled:
        _write_light_contact(context, plan.light_contact)
        return _result(True, spec.apply_message(plan), plan=plan)

    try:
        if plan.kind == "PLANE":
            plane_z = float(center.z)
            plane = _make_plane(
                spec.CATCHER_OBJECT,
                kit,
                Vector((center.x, center.y, plane_z)),
                plan.catcher_size,
            )
            _visibility(
                plane,
                catcher=plan.use_cycles_catcher,
                camera=True,
                shadow=True,
                glossy=False,
            )
            if plan.use_eevee_fallback:
                mat = _ensure_material(spec.FALLBACK_MATERIAL, spec.fallback_graph())
                _assign_material(plane, mat)
        elif plan.kind == "CONTACT":
            pass
        elif plan.kind == "NONE":
            pass
        else:
            unreachable = plan.kind
            raise RuntimeError(f"unhandled catcher kind: {unreachable}")

        if plan.use_contact:
            disc_z = float(center.z) + plan.contact_offset
            disc = _make_plane(
                spec.CONTACT_OBJECT,
                kit,
                Vector((center.x, center.y, disc_z)),
                plan.contact_size,
            )
            _visibility(
                disc,
                catcher=False,
                camera=True,
                shadow=False,
                glossy=False,
            )
            mat = _ensure_material(
                spec.CONTACT_MATERIAL,
                spec.contact_graph(plan.contact_strength),
            )
            _assign_material(disc, mat)

        _write_light_contact(context, plan.light_contact)
    except (RuntimeError, AttributeError, TypeError, ValueError):
        return _result(False, spec.CATCHER_FAILED, plan=plan)

    return _result(True, spec.apply_message(plan), plan=plan)


def on_catcher_update(settings, context: Context) -> None:
    """RNA update: Catcher toggle writes ground contact live."""
    del settings
    if context is None or getattr(context, "scene", None) is None:
        return
    apply_ground_contact(context)
