# SPDX-License-Identifier: GPL-3.0-or-later
"""Apply defeaturing lite with optional OCP / OpenCASCADE bindings.

Imports stay in this module's try/except so mesh-only CI still loads.
STEPper NEXT is not used here — it has no cleanup RNA.
"""

from __future__ import annotations

import math
from typing import Any, Never

from . import defeaturing as spec
from . import ocp_core

try:
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.BRepAlgoAPI import BRepAlgoAPI_Defeaturing
    from OCP.BRepBndLib import BRepBndLib
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy
    from OCP.BRepGProp import BRepGProp
    from OCP.Bnd import Bnd_Box
    from OCP.GProp import GProp_GProps
    from OCP.GeomAbs import (
        GeomAbs_Cone,
        GeomAbs_Cylinder,
        GeomAbs_Plane,
        GeomAbs_Sphere,
        GeomAbs_Torus,
    )
    from OCP.ShapeUpgrade import ShapeUpgrade_RemoveInternalWires
    from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID
    from OCP.TopExp import TopExp_Explorer

    _DEFEATURE_IMPORT_ERROR: BaseException | None = None
except Exception as exc:  # noqa: BLE001
    BRepAdaptor_Surface = None  # type: ignore[assignment]
    BRepAlgoAPI_Defeaturing = None  # type: ignore[assignment]
    BRepBndLib = None  # type: ignore[assignment]
    BRepBuilderAPI_Copy = None  # type: ignore[assignment]
    BRepGProp = None  # type: ignore[assignment]
    Bnd_Box = None  # type: ignore[assignment]
    GProp_GProps = None  # type: ignore[assignment]
    GeomAbs_Cone = None  # type: ignore[assignment]
    GeomAbs_Cylinder = None  # type: ignore[assignment]
    GeomAbs_Plane = None  # type: ignore[assignment]
    GeomAbs_Sphere = None  # type: ignore[assignment]
    GeomAbs_Torus = None  # type: ignore[assignment]
    ShapeUpgrade_RemoveInternalWires = None  # type: ignore[assignment]
    TopAbs_FACE = None  # type: ignore[assignment]
    TopAbs_SOLID = None  # type: ignore[assignment]
    TopExp_Explorer = None  # type: ignore[assignment]
    _DEFEATURE_IMPORT_ERROR = exc

try:
    from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
except Exception:  # noqa: BLE001
    ShapeUpgrade_UnifySameDomain = None  # type: ignore[assignment]


def probe_defeaturing_api() -> dict[str, bool]:
    """Which OCCT cleanup tools this OCP build actually imported."""
    has_defeaturing = BRepAlgoAPI_Defeaturing is not None
    has_remove_wires = ShapeUpgrade_RemoveInternalWires is not None
    has_adaptor = BRepAdaptor_Surface is not None and TopExp_Explorer is not None
    return {
        "ocp": ocp_core.ocp_available(),
        "adaptor": has_adaptor,
        "defeaturing": has_defeaturing,
        "remove_wires": has_remove_wires,
        "unify": ShapeUpgrade_UnifySameDomain is not None,
        "available": ocp_core.ocp_available()
        and has_adaptor
        and (has_defeaturing or has_remove_wires),
    }


def _surface_kind(typ: Any) -> spec.FaceKind:
    name = str(typ)
    if typ is GeomAbs_Plane or "Plane" in name:
        return "plane"
    if typ is GeomAbs_Cylinder or "Cylinder" in name:
        return "cylinder"
    if typ is GeomAbs_Torus or "Torus" in name:
        return "torus"
    if typ is GeomAbs_Sphere or "Sphere" in name:
        return "sphere"
    if typ is GeomAbs_Cone or "Cone" in name:
        return "cone"
    return "other"


def _call_first(obj: Any, names: tuple[str, ...], *args: Any) -> Any:
    last: BaseException | None = None
    for name in names:
        fn = getattr(obj, name, None)
        if fn is None:
            continue
        try:
            return fn(*args)
        except TypeError as exc:
            last = exc
            continue
    if last is not None:
        raise last
    return None


def _face_area(face: Any) -> float:
    if BRepGProp is None or GProp_GProps is None:
        return 0.0
    props = GProp_GProps()
    try:
        _call_first(BRepGProp, ("SurfaceProperties_s", "SurfaceProperties"), face, props)
    except Exception:  # noqa: BLE001
        return 0.0
    try:
        return abs(float(props.Mass()))
    except Exception:  # noqa: BLE001
        return 0.0


def _radius_of(adaptor: Any, kind: spec.FaceKind) -> float:
    try:
        if kind == "cylinder":
            return float(adaptor.Cylinder().Radius())
        if kind == "torus":
            return float(adaptor.Torus().MinorRadius())
        if kind == "sphere":
            return float(adaptor.Sphere().Radius())
        if kind == "cone":
            return float(adaptor.Cone().RefRadius())
        if kind == "plane":
            return 0.0
        if kind == "other":
            return 0.0
        unreachable: Never = kind
        raise RuntimeError(f"unhandled face kind: {unreachable}")
    except Exception:  # noqa: BLE001
        return 0.0


def _iter_faces(shape: Any) -> list[Any]:
    if TopExp_Explorer is None or TopAbs_FACE is None:
        return []
    faces: list[Any] = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        faces.append(explorer.Current())
        explorer.Next()
    return faces


def _bbox_diag(shape: Any) -> float:
    if Bnd_Box is None or BRepBndLib is None:
        return 0.0
    box = Bnd_Box()
    try:
        _call_first(BRepBndLib, ("Add_s", "Add"), shape, box)
        xmin, ymin, zmin, xmax, ymax, zmax = box.Get()
    except Exception:  # noqa: BLE001
        return 0.0
    return math.sqrt(
        (xmax - xmin) ** 2 + (ymax - ymin) ** 2 + (zmax - zmin) ** 2
    )


def face_hint(face: Any) -> spec.FaceHint:
    if BRepAdaptor_Surface is None:
        return spec.FaceHint(kind="other")
    adaptor = BRepAdaptor_Surface(face)
    kind = _surface_kind(adaptor.GetType())
    u_span = abs(float(adaptor.LastUParameter()) - float(adaptor.FirstUParameter()))
    v_span = abs(float(adaptor.LastVParameter()) - float(adaptor.FirstVParameter()))
    closed_u = False
    try:
        closed_u = bool(adaptor.IsUClosed()) or bool(adaptor.IsUPeriodic())
    except Exception:  # noqa: BLE001
        closed_u = False
    return spec.FaceHint(
        kind=kind,
        radius=_radius_of(adaptor, kind),
        u_span=u_span,
        v_span=v_span,
        width=min(u_span, v_span),
        area=_face_area(face),
        closed_u=closed_u,
    )


def _copy_shape(shape: Any) -> Any:
    if BRepBuilderAPI_Copy is None:
        return shape
    try:
        return BRepBuilderAPI_Copy(shape).Shape()
    except Exception:  # noqa: BLE001
        return shape


def _shape_is_solidish(shape: Any) -> bool:
    if shape is None or TopExp_Explorer is None or TopAbs_SOLID is None:
        return False
    try:
        if shape.IsNull():
            return False
    except Exception:  # noqa: BLE001
        return False
    explorer = TopExp_Explorer(shape, TopAbs_SOLID)
    return bool(explorer.More())


def _run_defeaturing(shape: Any, faces: list[Any]) -> Any | str:
    if BRepAlgoAPI_Defeaturing is None:
        return spec.DEFEATURE_NO_FILLET_API
    if not faces:
        return shape
    try:
        tool = BRepAlgoAPI_Defeaturing()
        tool.SetShape(shape)
        for face in faces:
            adder = getattr(tool, "AddFaceToRemove", None)
            if adder is not None:
                adder(face)
            else:
                tool.AddFacesToRemove(face)
        built = getattr(tool, "Build", None)
        if built is not None:
            built()
        else:
            tool.Perform()
        if getattr(tool, "HasErrors", lambda: False)():
            return spec.DEFEATURE_FAILED
        result = tool.Shape()
        if result is None or result.IsNull():
            return spec.DEFEATURE_FAILED
        return result
    except Exception:  # noqa: BLE001
        return spec.DEFEATURE_FAILED


def _remove_small_wires(shape: Any, min_area: float) -> tuple[Any, int]:
    if ShapeUpgrade_RemoveInternalWires is None or min_area <= 0:
        return shape, 0
    try:
        before = len(_iter_faces(shape))
        tool = ShapeUpgrade_RemoveInternalWires(shape)
        if hasattr(tool, "MinArea"):
            tool.MinArea = min_area
        elif hasattr(tool, "SetMinArea"):
            tool.SetMinArea(min_area)
        if hasattr(tool, "RemoveFaceMode"):
            tool.RemoveFaceMode = True
        elif hasattr(tool, "SetRemoveFaceMode"):
            tool.SetRemoveFaceMode(True)
        tool.Perform()
        getter = getattr(tool, "GetResult", None)
        result = getter() if getter is not None else getattr(tool, "Result", lambda: shape)()
        if result is None or result.IsNull():
            return shape, 0
        after = len(_iter_faces(result))
        removed = max(0, before - after)
        return result, removed
    except Exception:  # noqa: BLE001
        return shape, 0


def _unify(shape: Any) -> Any:
    if ShapeUpgrade_UnifySameDomain is None:
        return shape
    try:
        tool = ShapeUpgrade_UnifySameDomain(shape, True, True, True)
        tool.Build()
        result = tool.Shape()
        if result is None or result.IsNull():
            return shape
        return result
    except Exception:  # noqa: BLE001
        return shape


def apply_defeaturing(
    shape: Any,
    plan: spec.DefeaturingPlan,
    *,
    filepath: str = "",
) -> tuple[Any, spec.CleanupStats] | str:
    """Suppress small fillets / chamfers / holes on an OCCT shape."""
    if not plan.active:
        return shape, spec.CleanupStats()

    probe = probe_defeaturing_api()
    blocked = spec.cleanup_blockers(
        plan,
        ocp_available=probe["ocp"],
        has_defeaturing=probe["defeaturing"],
        has_remove_wires=probe["remove_wires"],
    )
    if blocked:
        return blocked
    if not probe["adaptor"]:
        return spec.DEFEATURE_NEEDS_OCP
    if not _shape_is_solidish(shape):
        return spec.DEFEATURE_NO_SOLID

    working = _copy_shape(shape)
    faces = _iter_faces(working)
    hints = tuple(face_hint(face) for face in faces)
    meters = spec.meters_per_file_unit(filepath)
    picks = spec.select_feature_faces(
        hints,
        plan,
        meters_per_unit=meters,
        bbox_diag=_bbox_diag(working),
    )
    stats = spec.count_roles(picks)
    selected = [faces[pick.index] for pick in picks]

    if selected and probe["defeaturing"]:
        defeated = _run_defeaturing(working, selected)
        if isinstance(defeated, str):
            return defeated
        working = defeated
    elif selected and (plan.fillets or plan.chamfers):
        return spec.DEFEATURE_NO_FILLET_API

    wires = 0
    if plan.holes and probe["remove_wires"]:
        working, wires = _remove_small_wires(
            working,
            spec.hole_area_file_units(plan, meters),
        )
    working = _unify(working)
    return working, spec.CleanupStats(
        fillets=stats.fillets,
        chamfers=stats.chamfers,
        holes=stats.holes,
        wires=wires,
    )
