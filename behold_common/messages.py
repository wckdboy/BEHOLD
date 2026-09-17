# SPDX-License-Identifier: GPL-3.0-or-later
"""Operator reports and empty-state copy — no Blender import.

Vendored into each suite add-on. Domain modules keep matching constants.
"""

from __future__ import annotations

import os

AUTO_DRESS_FAILED = 'Could not auto-dress those bodies — select the product or Import Product'

BAKE_FAILED = 'Could not bake HDRI — check the path and try Bake HDRI again'

BAKE_RENDER_FAILED = 'Bake render failed — switch to Cycles and try Bake HDRI again'

BATCH_NOTHING = 'Nothing to export — enable Front / ¾ / Top or Saved shots'

BATCH_NO_CAMERA = 'No camera — Build Studio or Add Camera'

BATCH_NO_MESH = 'No product for batch — select the product or Import Product'

BATCH_NO_SHOTS = 'No shots to export — Add from the current setup, or turn off Saved shots'

BATCH_RENDER_FAILED = 'Batch render failed — check the camera and try Batch export again'

CATCHER_FAILED = 'Could not set ground contact — Build Studio, then try Catcher again'

CATCHER_OFF = 'Catcher off — the product has no extra ground contact'

CLEANUP_OFF = 'Turn on Fillets, Chamfers, or Holes — then Apply cleanup'

DEFEATURE_FAILED = 'Could not suppress those fillets / holes — try a smaller size, then Apply cleanup'

DEFEATURE_NEEDS_OCP = 'Cleanup needs OCP (cadquery-ocp). STEPper NEXT tessellates only — install OCP or turn off Fillets / Chamfers / Holes, then Apply cleanup'

DEFEATURE_NO_FILLET_API = 'This OCP build cannot remove fillets or chamfers — turn off Fillets / Chamfers or update cadquery-ocp, then Apply cleanup'

DEFEATURE_NO_HOLE_API = 'This OCP build cannot suppress holes — turn off Holes or update cadquery-ocp, then Apply cleanup'

DEFEATURE_NO_SOLID = 'Cleanup needs a solid body — this file is a surface or shell, turn off Fillets / Chamfers / Holes, then Apply cleanup'

DOF_DISABLED = 'DoF off — the still is sharp front to back'

DOF_FAILED = 'Could not set depth of field — check the camera and try DoF again'

EMPTY_NO_CAMERA = 'No camera — Build Studio or Add Camera'

EMPTY_NO_MESH = 'No mesh selected — select the product or Import Product'

EMPTY_NO_MESH_HINT = 'Import Product, then select that mesh (not the cyclorama)'

EMPTY_NO_PRODUCT = 'No product — Import Product or Build Studio'

EMPTY_NO_SHOTS = 'No shots yet — Add from the current camera, quality, and HDRI'

EMPTY_NO_SHOTS_NEXT = 'Add from the current camera, quality, and HDRI'

EMPTY_NO_SHOTS_TITLE = 'No shots yet'

EMPTY_STATE_MESSAGES = frozenset({'No BEHOLD cameras to clear — Build Studio or Add Camera', 'No render settings on this scene — pick a scene, then choose a size on Shoot', 'Unknown focus target — pick Focus on product or Focus on selected', 'Could not reach GitHub — Check your network, then Check for updates. Or Open release.', 'No product to focus — select the mesh or Import Product', 'No mesh selected — select the product or a surface', 'Light linking needs Cycles or EEVEE — switch the render engine, then Link Selected', 'No studio yet — Build Studio, then Catcher', 'IES needs a spot or point light — this light is a sun. Add Light, then Load IES', 'Light Draw cancelled — the light is gone. Add Light or Build Studio', 'No world on this scene — Build Studio, then Load HDRI', 'No objects selected — select meshes to link, or Solo product', 'No Color Management view on this scene — pick a scene and try again', 'EEVEE Next is not on this Blender — Draft is using Cycles. Update Blender, then Still', 'No BEHOLD camera to remove — Build Studio or Add Camera', 'No BEHOLD lights yet — drawing a new light. Build Studio or Add Light for a full rig', 'No shot to apply — Add from the current setup', 'No turntable yet — click Setup on Shoot', 'Cycles is not on this Blender — Final stills need Cycles. Enable Cycles, then Still', 'Unknown aspect — pick Square 1:1, Portrait 4:5, or Landscape 16:9', 'This release has no behold-*.zip — Open release and install the zip the same way as the first time.', 'No compositor on this scene — pick a scene, then toggle Compositor on Shoot', 'Unknown linking kind — pick Light or Shadow', 'No product to solo — select the mesh or Import Product', 'No BEHOLD light to remove — Build Studio or Add Light', 'Shot needs a name — type a name and try again', 'Unknown size — pick 2048², 1080p, or 4K', 'Shadow linking is not on this Blender — update to 5.2, then try Shadows', 'No product for ground contact — select the mesh or Import Product', 'Unknown quality — pick Draft or Final', 'Turn on Fillets, Chamfers, or Holes — then Apply cleanup', 'No camera — Build Studio or Add Camera', 'No mesh selected — select the product or Import Product', 'No product to frame — select the mesh or Import Product', 'No BEHOLD lights yet — Build Studio or Add Light', 'Cleanup needs OCP (cadquery-ocp). STEPper NEXT tessellates only — install OCP or turn off Fillets / Chamfers / Holes, then Apply cleanup', 'No shot to rename — Add from the current setup', 'No product for batch — select the product or Import Product', 'Depth of field needs camera DoF RNA — update to Blender 5.2, then enable DoF', 'No file selected — pick a product mesh or CAD file', 'No BEHOLD cameras yet — Build Studio or Add Camera', 'This OCP build cannot suppress holes — turn off Holes or update cadquery-ocp, then Apply cleanup', 'Light linking needs Blender 4.2+ with Cycles collections — update Blender, then Link Selected', 'Unsupported bake format — use .hdr or .exr', 'No product — Import Product or Build Studio', 'No CAD source cached — Import Product with a STEP, IGES, or BREP file, then Regenerate', 'Unknown tessellation quality — pick Draft, Balanced, Fine, Ultra, or Custom', 'False Color is not on this Color Management config — keep AgX and use EV', 'No IES selected — pick a .ies from disk, or Sample', 'No STEP color or part-name hint — name the bodies or use Assist for one look', 'No shot to remove — Add from the current setup', 'No turntable to clear — click Setup on Shoot first', 'This OCP build cannot remove fillets or chamfers — turn off Fillets / Chamfers or update cadquery-ocp, then Apply cleanup', 'No shots to export — Add from the current setup, or turn off Saved shots', 'No main camera bookmarked yet — Bookmark on Advanced → Shoot, or Add Camera', 'Cleanup needs a solid body — this file is a surface or shell, turn off Fillets / Chamfers / Holes, then Apply cleanup', 'Light Draw needs a 3D Viewport — open a 3D View and run it from Lights', 'Nothing to export — enable Front / ¾ / Top or Saved shots', 'Shadow catcher needs object Visibility RNA — update Blender, then Catcher', 'No shots yet — Add from the current camera, quality, and HDRI', 'Gobos need an area or spot light — Apply a Softbox, or Add Light', 'Unknown backdrop — pick Cyclorama, Solid, or HDRI', 'No bake path — save the .blend or pick an .hdr / .exr file', 'This scene already has compositor nodes — clear them, then toggle Compositor', 'No HDRI selected — pick an HDR, EXR, or image from disk'})

ERROR = 'ERROR'

EXPOSURE_APPLIED = 'Exposure applied — Color Management has EV and white balance'

FALSE_COLOR_OFF = 'False Color off — restored the previous view look'

FALSE_COLOR_ON = 'False Color on — meter hot/cold, then toggle off for AgX'

FALSE_COLOR_UNAVAILABLE = 'False Color is not on this Color Management config — keep AgX and use EV'

FOCUS_NO_PRODUCT = 'No product to focus — select the mesh or Import Product'

FOCUS_NO_SELECTION = 'No mesh selected — select the product or a surface'

FRAME_NO_PRODUCT = 'No product to frame — select the mesh or Import Product'

GOBO_CLEARED = 'Gobo off — the light is uniform again'

GOBO_NODES_FAILED = 'Could not build that gobo — this Blender build is missing a light node. Try None, or update Blender'

HDRI_LOAD_FAILED = 'Could not load that HDRI — pick another .hdr / .exr and try Load HDRI'

IES_CLEARED = 'IES off — the light is back to its prior type and Shape'

IES_LOAD_FAILED = 'Could not load that IES — pick another .ies and try Load'

IES_NODES_FAILED = 'Could not build that IES graph — this Blender build is missing a light node. Try Clear, or update Blender'

LIGHT_DRAW_LIGHT_MISSING = 'Light Draw cancelled — the light is gone. Add Light or Build Studio'

LIGHT_DRAW_NEEDS_VIEWPORT = 'Light Draw needs a 3D Viewport — open a 3D View and run it from Lights'

LIGHT_DRAW_NO_LIGHTS = 'No BEHOLD lights yet — drawing a new light. Build Studio or Add Light for a full rig'

LINKING_FAILED = 'Could not update light linking — check the collection and try Link Selected again'

LOOK_COMPOSITOR_BUSY = 'This scene already has compositor nodes — clear them, then toggle Compositor'

LOOK_DISABLED = 'Look compositor off — stills skip vignette and grain'

LOOK_NODES_FAILED = 'Could not build that compositor look — this Blender build is missing a compositor node. Try Clean, or update Blender'

NO_BAKE_PATH = 'No bake path — save the .blend or pick an .hdr / .exr file'

NO_BODY_HINT = 'No STEP color or part-name hint — name the bodies or use Assist for one look'

NO_CAD_SOURCE = 'No CAD source cached — Import Product with a STEP, IGES, or BREP file, then Regenerate'

NO_CAMERA = 'No camera — Build Studio or Add Camera'

NO_CAMERAS = 'No BEHOLD cameras yet — Build Studio or Add Camera'

NO_CAMERAS_HINT = 'Build Studio to add a framed product camera'

NO_CAMERAS_NEXT = 'Build Studio or Add Camera'

NO_CAMERAS_TITLE = 'No BEHOLD cameras yet'

NO_CAMERAS_TO_CLEAR = 'No BEHOLD cameras to clear — Build Studio or Add Camera'

NO_CAMERA_TO_REMOVE = 'No BEHOLD camera to remove — Build Studio or Add Camera'

NO_CATCHER_API = 'Shadow catcher needs object Visibility RNA — update Blender, then Catcher'

NO_COMPOSITOR = 'No compositor on this scene — pick a scene, then toggle Compositor on Shoot'

NO_CYCLES = 'Cycles is not on this Blender — Final stills need Cycles. Enable Cycles, then Still'

NO_DOF_API = 'Depth of field needs camera DoF RNA — update to Blender 5.2, then enable DoF'

NO_EEVEE = 'EEVEE Next is not on this Blender — Draft is using Cycles. Update Blender, then Still'

NO_FILE_SELECTED = 'No file selected — pick a product mesh or CAD file'

NO_GOBO_TYPE = 'Gobos need an area or spot light — Apply a Softbox, or Add Light'

NO_HDRI_FILE = 'No HDRI selected — pick an HDR, EXR, or image from disk'

NO_IES_FILE = 'No IES selected — pick a .ies from disk, or Sample'

NO_IES_TYPE = 'IES needs a spot or point light — this light is a sun. Add Light, then Load IES'

NO_LIGHTS = 'No BEHOLD lights yet — Build Studio or Add Light'

NO_LIGHTS_HINT = 'Build Studio to seed Key, Fill, and Rim'

NO_LIGHTS_NEXT = 'Build Studio or Add Light'

NO_LIGHTS_TITLE = 'No BEHOLD lights yet'

NO_LIGHTS_TO_BAKE = 'No BEHOLD lights yet — Build Studio or Add Light'

NO_LIGHT_TO_REMOVE = 'No BEHOLD light to remove — Build Studio or Add Light'

NO_LINKING_API = 'Light linking needs Blender 4.2+ with Cycles collections — update Blender, then Link Selected'

NO_LINKING_ENGINE = 'Light linking needs Cycles or EEVEE — switch the render engine, then Link Selected'

NO_MAIN_CAMERA = 'No main camera bookmarked yet — Bookmark on Advanced → Shoot, or Add Camera'

NO_MESH_HINT = 'Import Product, then select that mesh (not the cyclorama)'

NO_MESH_SELECTED = 'No mesh selected — select the product or Import Product'

NO_PRODUCT = 'No product — Import Product or Build Studio'

NO_PRODUCT_FOR_CATCHER = 'No product for ground contact — select the mesh or Import Product'

NO_PRODUCT_TO_SOLO = 'No product to solo — select the mesh or Import Product'

NO_RENDER_SETTINGS = 'No render settings on this scene — pick a scene, then choose a size on Shoot'

NO_SELECTION = 'No objects selected — select meshes to link, or Solo product'

NO_SHADOW_API = 'Shadow linking is not on this Blender — update to 5.2, then try Shadows'

NO_SHOTS = 'No shots yet — Add from the current camera, quality, and HDRI'

NO_SHOTS_NEXT = 'Add from the current camera, quality, and HDRI'

NO_SHOTS_TITLE = 'No shots yet'

NO_SHOT_TO_APPLY = 'No shot to apply — Add from the current setup'

NO_SHOT_TO_REMOVE = 'No shot to remove — Add from the current setup'

NO_SHOT_TO_RENAME = 'No shot to rename — Add from the current setup'

NO_STUDIO = 'No studio yet — Build Studio, then Catcher'

NO_VIEW_SETTINGS = 'No Color Management view on this scene — pick a scene and try again'

NO_WORLD = 'No world on this scene — Build Studio, then Load HDRI'

QUALITY_FAILED = 'Could not apply that quality preset — check the render engine, then Apply Quality'

REGENERATE_EMPTY = 'Tessellation produced no triangles — try a finer quality, then Regenerate'

REGENERATE_FAILED = 'Could not retessellate that CAD — check the file, then Regenerate'

RESOLUTION_FAILED = 'Could not apply that size — check Output Properties, then Apply Size'

SHOT_NAME_EMPTY = 'Shot needs a name — type a name and try again'

TURNTABLE_NOTHING_TO_CLEAR = 'No turntable to clear — click Setup on Shoot first'

TURNTABLE_NO_SETUP = 'No turntable yet — click Setup on Shoot'

TURNTABLE_READY_PLAY = 'Turntable ready — press Space to play'

UNKNOWN_ASPECT = 'Unknown aspect — pick Square 1:1, Portrait 4:5, or Landscape 16:9'

UNKNOWN_BACKDROP = 'Unknown backdrop — pick Cyclorama, Solid, or HDRI'

UNKNOWN_CAD_QUALITY = 'Unknown tessellation quality — pick Draft, Balanced, Fine, Ultra, or Custom'

UNKNOWN_FOCUS = 'Unknown focus target — pick Focus on product or Focus on selected'

UNKNOWN_GOBO = 'Unknown gobo — pick None, Blinds, Window, or Circle'

UNKNOWN_KIND = 'Unknown linking kind — pick Light or Shadow'

UNKNOWN_LIGHT_PRESET = 'Unknown light shape — pick Softbox, Strip, Octa, Hard, or Rim'

UNKNOWN_LOOK_PRESET = 'Unknown look — pick Clean, Catalog, or Dramatic'

UNKNOWN_QUALITY = 'Unknown quality — pick Draft or Final'

UNKNOWN_SIZE = 'Unknown size — pick 2048², 1080p, or 4K'

UNSUPPORTED_BAKE = 'Unsupported bake format — use .hdr or .exr'

UPDATE_CHECK_OFFLINE = 'Could not reach GitHub — Check your network, then Check for updates. Or Open release.'

UPDATE_CHECK_UNAVAILABLE = 'This release has no behold-*.zip — Open release and install the zip the same way as the first time.'

WARNING = 'WARNING'

WORLD_RESET = 'World reset to solid studio'

def em_dash_join(title: str, next_step: str) -> str:
    """Title plus the next action, matching N-panel empty-state CTAs."""
    return f"{title} — {next_step}"


def warning_set() -> set[str]:
    return {WARNING}


def error_set() -> set[str]:
    return {ERROR}


def report_type(message: str) -> str:
    """WARNING for missing-prerequisite copy, ERROR for hard failures."""
    if message in EMPTY_STATE_MESSAGES:
        return WARNING
    if message.startswith(
        (
            "File not found:",
            "Unsupported file type:",
            "HDRI file not found:",
            "Unsupported HDRI:",
            "Unsupported bake format:",
            "IES file not found:",
            "Unsupported IES:",
            "CAD file not found:",
            "Cached source is not CAD",
            "Unknown tessellation quality",
            "Cleanup needs OCP",
            "This OCP build cannot",
            "Cleanup needs a solid",
            "No STEP color",
            "Shot name “",
            "Shot camera “",
            "Batch export ",
            "Unknown aspect",
            "Unknown size",
        )
    ):
        return WARNING
    return ERROR


def report_set(message: str) -> set[str]:
    return {report_type(message)}


def named_missing(kind: str, name: str, *, next_step: str) -> str:
    shown = name.strip() or kind.lower()
    return f"{kind} “{shown}” is gone — {next_step}"


def light_not_found(name: str) -> str:
    return named_missing("Light", name, next_step=NO_LIGHTS_NEXT)


def unknown_light_preset_message(preset_id: str) -> str:
    shown = (preset_id or "").strip()
    if not shown:
        return UNKNOWN_LIGHT_PRESET
    return (
        f"Unknown light shape “{shown}” — "
        "pick Softbox, Strip, Octa, Hard, or Rim"
    )


def unknown_gobo_message(preset_id: str) -> str:
    shown = (preset_id or "").strip()
    if not shown:
        return UNKNOWN_GOBO
    return f"Unknown gobo “{shown}” — pick None, Blinds, Window, or Circle"


def unknown_gobo_preset_message(preset_id: str) -> str:
    return unknown_gobo_message(preset_id)


def unknown_look_message(preset_id: str) -> str:
    shown = (preset_id or "").strip()
    if not shown:
        return UNKNOWN_LOOK_PRESET
    return f"Unknown look “{shown}” — pick Clean, Catalog, or Dramatic"


def unknown_look_preset_message(preset_id: str) -> str:
    return unknown_look_message(preset_id)


def unknown_aspect_message(aspect_id: str) -> str:
    shown = (aspect_id or "").strip()
    if not shown:
        return UNKNOWN_ASPECT
    return (
        f"Unknown aspect “{shown}” — "
        "pick Square 1:1, Portrait 4:5, or Landscape 16:9"
    )


def unknown_aspect_preset_message(aspect_id: str) -> str:
    return unknown_aspect_message(aspect_id)


def unknown_size_message(size_id: str) -> str:
    shown = (size_id or "").strip()
    if not shown:
        return UNKNOWN_SIZE
    return f"Unknown size “{shown}” — pick 2048², 1080p, or 4K"


def unknown_size_preset_message(size_id: str) -> str:
    return unknown_size_message(size_id)


def baked_message(filepath: str, *, applied: bool = False) -> str:
    name = os.path.basename(filepath) or filepath or "HDRI"
    if applied:
        return f"Baked studio HDRI: {name} — applied as world"
    return f"Baked studio HDRI: {name}"


def camera_not_found(name: str) -> str:
    return named_missing("Camera", name, next_step=NO_CAMERAS_NEXT)


def shot_not_found(name: str) -> str:
    return named_missing("Shot", name, next_step=NO_SHOTS_NEXT)


def shot_name_taken(name: str) -> str:
    shown = (name or "").strip() or "that name"
    return f"Shot name “{shown}” is already used — pick another name"


def shot_applied_message(name: str) -> str:
    shown = (name or "").strip() or "Shot"
    return f"Shot applied: {shown}"


def shot_camera_missing(name: str) -> str:
    return named_missing(
        "Shot camera",
        name,
        next_step="Add Camera or pick another shot",
    )


def bookmark_camera_missing(name: str) -> str:
    return named_missing(
        "Bookmarked camera",
        name,
        next_step="Bookmark again or Add Camera",
    )


def file_not_found_message(filepath: str) -> str:
    name = os.path.basename(filepath) or filepath or "that file"
    return f"File not found: {name} — choose an existing product file"


def unsupported_file_message(ext: str) -> str:
    shown = (ext or "").strip() or "this file"
    return (
        f"Unsupported file type: {shown} — "
        "use OBJ, FBX, STL, GLB, 3MF, or STEP/IGES"
    )


def hdri_file_not_found(filepath: str) -> str:
    name = os.path.basename(filepath) or filepath or "that HDRI"
    return f"HDRI file not found: {name} — choose an existing .hdr / .exr"


def unsupported_hdri_message(ext: str) -> str:
    shown = (ext or "").strip() or "this file"
    return f"Unsupported HDRI: {shown} — use HDR, EXR, or a still image"


def hdri_loaded_message(filepath: str) -> str:
    name = os.path.basename(filepath) or filepath or "HDRI"
    return f"HDRI loaded: {name}"


def bake_hdri_message(filepath: str, *, applied: bool = False) -> str:
    return baked_message(filepath, applied=applied)


def bake_path_problem_message(problem) -> str:
    kind = getattr(problem, "kind", "") or ""
    detail = getattr(problem, "detail", "") or ""
    if kind == "empty":
        return NO_BAKE_PATH
    shown = detail.strip() or "this file"
    return f"Unsupported bake format: {shown} — use .hdr or .exr"


def update_failure_report(copy: dict[str, str]) -> str:
    """Compose updates.core describe_failure dicts into operator copy."""
    line = (copy.get("line") or "").strip()
    detail = (copy.get("detail") or "").strip()
    if line and detail:
        return em_dash_join(line, detail)
    return line or detail

