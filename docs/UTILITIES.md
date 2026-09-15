# BEHOLD Utilities

Feature-flagged CAD/build helpers for **MinAltan / Scandinavian balcony-mount
workflows**. Artists use these to show how a balcony sits in a Danish apartment
wall — not as structural engineering, and **not** as part of the default
product-render path.

This track is **not a product release**. Addon version is independent of this
track (currently v1.4.0). Do not treat Utilities as a product milestone.

## Enable

Default **off**. When off, there is no Utilities N-panel and the wall / mount
operators are not registered (they do not appear on Import → Studio → Lights →
Materials → Cameras → Shoot).

1. Edit → Preferences → Add-ons → **BEHOLD**
2. Chrome → **Utilities panel** (`enable_utilities`)
3. Open the 3D Viewport sidebar (`N`) → **BEHOLD** → **Utilities** (after
   Advanced, collapsed closed)

## Danish wall

Layered mesh: exterior masonry + insulation + interior plaster. Thickness
presets (user-stated Danish practice):

| Storey | Total thickness |
| --- | --- |
| Foundation / bottom | **600–700 mm** (parametrizable, default **700**) |
| Ground + floors 1–2 | **480 mm** |
| Top floors | **360 mm** |

Layer millimetres always **sum to the storey total**. Exterior masonry defaults
to 228 mm on foundation and 108 mm on upper storeys; interior plaster defaults
to 13 mm; insulation is the remainder. Override masonry / plaster in the panel
(0 = use the storey default).

Optional balcony-door opening cuts through all three layers.

**Build Wall** creates `BEHOLD_Util_Wall*` meshes plus a `BEHOLD_Util_WallFace`
empty on the exterior face (Y = 0, balcony in +Y).

## Balcony mounts

Place relative to the wall face. Needs a Danish wall **and** a balcony product
mesh (imported or selected). Actionable warnings if either is missing.

| Method | What you get |
| --- | --- |
| **Legs** | Front posts + base plates + rear wall brackets |
| **L-bracket** | Under-frame L with a diagonal brace |

The kit is parented to a root empty with a Child Of constraint on the wall.
Snap empties mark where the imported CAD balcony should sit. Rebuild replaces
the previous kit of that method.

## OpenSCAD (optional)

`behold/utilities/openscad/wall_stack.scad` is a millimetre wall-stack template.
**Export wall .scad** writes the current panel dimensions to a text block and,
when the `.blend` is saved, to `behold_danish_wall.scad` beside it. Mount kits
are Blender-only.

## MinAltan drawings

The MinAltan A/S section drawings (Altan under/over tagrende, murkrone, skunk,
dormer/kvist rules) are **reference only**. Dimensions on those sheets are
vejledende. This helper does not encode planning rules, BIM, or load calcs.

## Out of scope

Full BIM / IFC, structural engineering, replacing STEPper, logo redo, merging
Utilities into Import → Shoot, tagging a GitHub Release.
