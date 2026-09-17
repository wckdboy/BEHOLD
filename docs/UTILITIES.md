# BEHOLD Utilities

Optional CAD/build helpers for **MinAltan / Scandinavian balcony-mount
workflows**. Artists use these to show how a balcony sits in a Danish apartment
wall — not as structural engineering, and **not** as part of the default
product-render path.

This track is **not a product release**. In **1.6.0** it lived behind the
monolith preference `enable_utilities` (default off). In **v2.0.0** it is its
own installable add-on: `behold-utilities-2.0.0.zip`. Do not treat Utilities as
a product-render milestone.

## Enable

Install **BEHOLD Utilities** from Disk, then enable it. There is no
`enable_utilities` switch on Product / Studio / Lighting — the **Utilities
panel** is on whenever this zip is enabled. It does not appear unless you
install this add-on. Import → Studio → Lights → Materials → Cameras → Shoot
stays the product-render path.

1. Get `behold-utilities-2.0.0.zip` (after Studio, Lighting, and Product).
2. Blender → Edit → Preferences → Get Extensions → **Install from Disk**
3. Enable **BEHOLD Utilities**
4. Open the 3D Viewport sidebar (`N`) → **BEHOLD** → **Utilities** (after
   Advanced, collapsed closed)

Migrating from 1.6.0: uninstall the monolith, then install this zip. The old
Chrome → **Utilities panel** (`enable_utilities`) checkbox is gone.

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

## Eave / roof sections

Parametric bpy meshes that show how the balcony sits **under** or **over** the
eaves, plus simple wall-crown / skunk / roof-cut variants from MinAltan A/S
snit 6.01. Dimensions on those sheets are **vejledende** — this helper does not
encode planning rules, kvistaltan 50% cantilever policy, BIM, or load calcs.

Needs a Danish wall. A selected balcony mesh is optional (width / depth follow
the product when present, otherwise the wall). The kit is constrained to the
wall like the mount kits. Rebuild replaces the previous eave section.

Typical order: **Build Wall** → **Build Legs / L-bracket** → pick a snit preset
→ **Build eave section**. Roof pitch defaults to 45°.

| Preset | MinAltan label | What you get |
| --- | --- | --- |
| **Under eaves** | Altan under tagrende | Roof + gutter outboard over the balcony; wall crown (murkrone) stays |
| **Over eaves** | Altan over tagrende | Balcony at the cut eaves; roof and gutter behind with ~200 mm leftover overhang |
| **Wall crown off** | Murkrone fjernet | Under eaves without the parapet; more headroom under the roof |
| **Recessed skunk** | Indraget skunk | Over eaves with the deck pushed back into the attic / skunk volume |
| **Roof inclusion** | Inddragelse af tag | Over eaves with cheek walls where the roof is cut around the balcony |

Objects: `BEHOLD_Util_Eave*` plus `BEHOLD_Util_EaveSnap` at the deck. Meshes
use the `BEHOLD_Util_` prefix so they never count as the imported product.

## OpenSCAD (optional)

`behold_utilities/openscad/wall_stack.scad` is a millimetre wall-stack template.
**Export wall .scad** writes the current panel dimensions to a text block and,
when the `.blend` is saved, to `behold_danish_wall.scad` beside it. Mount kits
and eave sections are Blender-only.

## Out of scope

Full BIM / IFC, structural engineering, replacing STEPper, logo redo, merging
Utilities into Import → Shoot, tagging a GitHub Release *only* for this track,
encoding kvistaltan planning rules.
