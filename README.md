<p align="center">
  <img src="docs/brand/behold_logo.png" alt="BEHOLD by AMIRITE.studio" width="280">
</p>

# BEHOLD

**BEHOLD by AMIRITE.studio** — the best product-render suite for Blender. KeyShot-simple lighting, cameras, and stills, as open source.

**v2.0.0 — four add-ons.** The 1.6.0 monolith is split into **BEHOLD Studio**, **BEHOLD Lighting**, **BEHOLD Product**, and optional **BEHOLD Utilities**. Extracted, not rewritten. **v1.6.0 — simplified.** One card, one job. **v1.5.1 — Install from Disk works.** v1.5.0 failed to enable (Auto-dress swallowed the Studio-from-Import operator). **v1.5.0** is per-body auto-dress. **Assist** still applies one look to the selection. **v1.4.0** is defeaturing lite. **v1.3.0** is live tessellation regenerate. **v1.2.0** is IES practical lite. **v1.1.0** is procedural gobo lite. **v1.0.0 is First stable.** The current logo is a **placeholder** (official mark in the UI still ships).

Official mark (Blender UI): [`behold_product/icons/behold_icon.png`](behold_product/icons/behold_icon.png) · Wordmark: [`docs/brand/behold_logo.png`](docs/brand/behold_logo.png) · also [`behold_product/icons/behold_logo.png`](behold_product/icons/behold_logo.png)

Primary Blender target: **5.2 LTS and newer**. Install still declares 4.2+ (`bl_info` / `blender_manifest.toml`) so older 4.x/5.1 builds can load the zips; production lighting, cameras, turntable, and materials are developed and tested against 5.2 LTS.

Living status (Implemented vs Coming) lives in **[CHECKPOINT.md](CHECKPOINT.md)**. Leveling path: **[ROADMAP.md](ROADMAP.md)**.

## Suite (v2.0.0)

| Zip | Add-on | Job |
| --- | --- | --- |
| `behold-studio-2.0.0.zip` | **BEHOLD Studio** | Cyclorama / backdrop builder, HDRI world, ground contact, studio setup |
| `behold-lighting-2.0.0.zip` | **BEHOLD Lighting** | Multi-light, Light Draw, shape/softbox, gobo, IES, linking |
| `behold-product-2.0.0.zip` | **BEHOLD Product** | Import (mesh + CAD/STEPper/OCP, tessellate, cleanup) + Materials (local looks, Assist, auto-dress) + Shoot/Cameras (DoF, turntable, exposure, looks, batch, shots, resolution, EEVEE draft) |
| `behold-utilities-2.0.0.zip` | **BEHOLD Utilities** | Danish wall, balcony mounts, eave/roof sections — optional |

Each zip is a complete Blender extension (`blender_manifest.toml` + `__init__.py`). Shared chrome is **vendored** into each add-on as `common/` — no fragile inter-add-on Python imports. Soft-dependency copy is OK (“Install BEHOLD Studio for Build Studio”).

N-panel: each add-on owns its section(s) on the **BEHOLD** tab. Product keeps **Import → Materials → Cameras → Shoot** inside itself. Studio, Lighting, and Utilities are separate sections.

## Quick start

**Import → Studio → Shoot.** Open the 3D Viewport sidebar (`N`) → **BEHOLD**.

1. **Import** (Product) — **Import Product**. Mesh formats go in natively. STEP / IGES / BREP need [STEPper NEXT](#stepper-next) (or OCP fallback).
2. **Studio** — select the mesh, pick **White / Grey / Black**, click **Build**. **Catcher** (on by default) puts ground contact under the product.
3. **Shoot** (Product) — **Draft** for a fast look (**Draft = EEVEE · Final = Cycles**). Pick **Size**. Click **Still**. Switch to **Final** for the client frame.

Dress **Lights**, **Materials**, and **Cameras** between Studio and Shoot. **Check for updates** lives in each add-on's preferences (auto-check on, once a day). See [Updates](#updates).

Faster path: pie menu **Shift+Alt+B**, or the 3D View header icons (Import / Build Studio / Still) — those live on **BEHOLD Product**.

## Feature map

N-panel order across the suite: **Import → Studio → Lights → Materials → Cameras → Shoot → Advanced**. Product's own cards stay **Import → Materials → Cameras → Shoot**.

| Panel | Add-on | What you get |
| --- | --- | --- |
| **Import** | Product | **Import Product** file picker + CAD line (**STEPper NEXT ready** / **OCP fallback** / **Install STEPper NEXT**) + **Tessellation** (**Regenerate**, tessellate only) + **Cleanup** (**Apply cleanup**) |
| **Studio** | Studio | White / Grey / Black + **Build** + **Catcher**, compact **HDRI**, compact **Bake HDRI** |
| **Lights** | Lighting | Inventory + Light Draw + **Shape** + **Gobo** + **IES** (Load / Sample / Clear) + **Linking** — each card one job; Gobo and IES do not restore each other |
| **Materials** | Product | Metal / Plastic / Rubber / Glass / Paint + **Assist** (one look) + **Auto-dress** (per body) |
| **Cameras** | Product | Add / frame product cameras + **DoF** |
| **Shoot** | Product | Draft / Final, **Still**, **Size**, **Exposure**, **Look**, **Shots**, **Batch export**, **Turntable** |
| **Advanced** | Product (plus Studio / Lighting parked cards) | Parked extras (mixer, **Studio Margin**, CAD box, BlenderKit, bake/ease, Apply buttons) |
| **Utilities** | Utilities (optional) | Danish wall, Legs / L-bracket, eave / roof sections — [docs/UTILITIES.md](docs/UTILITIES.md) |

### Import

Mesh `.obj` `.fbx` `.stl` `.glb` `.gltf` (native 4.2+ / 5.2 LTS). `.3mf` when Blender has an importer. CAD `.step` `.stp` `.iges` `.igs` `.brep` `.brp` via **STEPper NEXT** (production on 5.1+/5.2 LTS) or OCP if STEPper is missing and bindings import. Mesh never requires STEPper. Missing CAD backend **fails loudly** with the STEPper Releases URL.

After import: optional **Build Studio** around the new mesh (file-browser checkbox). Dressing is a **Materials** step: **Auto-dress** per body, or **Assist** for one look. Optional dress-after-import lives in Advanced (default **off**).

**Tessellation (1.3.0 / 1.6.0)** — **Regenerate** the last STEP / IGES / BREP without re-picking the file. Tessellate only — Cleanup is the next card. **Draft / Balanced / Fine / Ultra** match STEPper NEXT physical deflection (2 mm / 0.8 mm / 0.2 mm / 0.05 mm); **Custom** is the slider. STEPper NEXT is used when it is installed; OCP is the fallback when that is what imported (or STEPper is missing). Materials and transforms stay on the product where names still match. No CAD source cached reports a sentence plus the next step. **Apply tessellation** stays in Advanced. Mesh OBJ/FBX/STL/GLB/3MF is not retessellated.

**Cleanup (1.4.0 / 1.6.0)** — product-render defeaturing lite, not a CAD editor. **Fillets / Chamfers / Holes** toggles plus millimetre thresholds (**Blend** default 2 mm radius/width, **Hole Ø** default 3 mm) and **Apply cleanup** (then retessellates). **STEPper NEXT has no fillet / chamfer / hole RNA** — cleanup needs **OCP** (`cadquery-ocp`). Missing OCP or an unsupported OCP build reports a sentence plus the next step. Defaults off. Not a kernel UI.

### Studio

Select the product → **Build**. The cyclorama auto-fits the world AABB (floor from XY diagonal × **Studio Margin**, default 2.0×, parked in Advanced; wall clears height with headroom). Lights sit outside the sweep. Rebuild replaces the old cyclorama.

**Catcher** sits next to **Build** (default on) — believable **ground contact**, not a second engine panel:

- Cyclorama: soft contact disc under the product (`BEHOLD_ContactShadow`)
- Solid / HDRI (Advanced backdrop): optional Cycles **shadow catcher** plane; EEVEE Draft uses light contact shadows plus a Light Path fallback

**HDRI** — Load an `.hdr` / `.exr` from disk (OpenHDRI / Poly Haven / BYO). Strength, Z rotation, optional **Reflections only**. **Reset** restores a solid studio world.

**Bake HDRI** — 1K/2K equirectangular `.exr` / `.hdr` of the light rig (product and cyclorama hidden). Optional include world / apply as world. Empty path writes next to the `.blend`.

### Lights

Add / remove / set active BEHOLD area lights. Per-light energy. Build Studio seeds Key / Fill / Rim (needs **BEHOLD Lighting** installed).

- **Shape** — Softbox, Strip, Octa, Hard, Rim on the active light (size / spread). Falloff waits until Gobo and IES are off. **Apply to active**.
- **Gobo (1.1.0 / 1.6.0)** — **None / Blinds / Window / Circle** on the active BEHOLD **area or spot** light. Owns the light node tree (**turns IES off**). **Scale** and **Strength** when a pattern is on. **None** restores Shape falloff. Live RNA update; **Apply Gobo** stays in Advanced.
- **IES (1.2.0 / 1.6.0)** — **Load** / **Sample** / **Clear** a photometric `.ies` on the active BEHOLD light. Owns the light node tree (**turns Gobo off**). Cycles IES works on **spot and point**; area lights become spots while the profile is on. **Clear** restores the prior type and Shape. One bundled CC0 `sample_spot.ies` — **bring your own `.ies`**. **Apply IES** stays in Advanced.
- **Linking** — **Link Selected** cycles include → exclude (Cycles **light linking**). Independent of Shape / Gobo / IES. **Unlink** / **Solo product**. **Light / Shadow** picks receiver vs blocker collection when the 5.2 API is present.
- **Light Draw** — Aim: Active | New. Reflect / Direct / Orbit (LMB aim, scroll power/size/distance, solo).

Empty state until you Build Studio or Add Light.

### Materials

One-click **Metal / Plastic / Rubber / Glass / Paint** on the selected product mesh (not the cyclorama / catcher). **Assist** maps the filename / STEP hint onto that rack and applies **one look** to the selection — **no BlenderKit account required**. **Auto-dress (1.5.0)** assigns a look **per body** from STEP color and/or part name (same name hints as Assist). On demand on Materials (Import does not auto-dress unless you turn on the Advanced checkbox). Bodies with no color or name hint are skipped (sentence + next step: use Assist for one look). Signed-in BlenderKit still searches after Assist's local look lands. Empty state if nothing dressable is selected.

### Cameras

85 mm full-frame product cameras. Add / set active / frame / delete / clear. Active camera is the Shoot still (and the main-camera bookmark). Build Studio seeds `BEHOLD_Camera` (needs **BEHOLD Product**).

**DoF** — on/off, **f-stop** (product default **f/5.6**), **Focus on product** (AABB center, studio sweep excluded), **Focus on selected** (facing surface). Maps to Blender 5.2 `Camera.dof`. Empty Cameras state unchanged. **Apply DoF** stays in Advanced.

### Shoot

**Draft = EEVEE · Final = Cycles.** Draft uses EEVEE Next when the build has it; Final / Product / Hero stay Cycles (256 / 128 / 512 samples, denoising). Missing EEVEE falls back to Cycles Draft and says so.

**Size** — **Square 1:1**, **Portrait 4:5**, **Landscape 16:9** with **2048²** / **1080p** / **4K** (long edge 2048 / 1920 / 3840). Writes render resolution at 100% with square pixels. Default Square 1:1 at 2048². Landscape + 1080p = 1920×1080; Landscape + 4K = 3840×2160.

**Exposure** — **EV** (−6 to +6), **WB** in Kelvin (D65 = 6500 K), AgX-safe **False Color**. Color Management, not compositor. Light Draw **F** still toggles False Color.

**Look** — **Clean / Catalog / Dramatic** compositor stills (Catalog = mild **vignette** + grain, bloom off; Dramatic adds stronger edges + mild bloom-safe glare). **Compositor** toggle builds / tears down BEHOLD nodes; custom trees are left alone.

**Shot Manager** — named presets (camera, quality, turntable seconds, HDRI, backdrop, output tokens). **Add / Apply / rename / Delete**. Apply does not touch the product mesh.

**Batch export** — **Front / ¾ / Top** stills, optional saved shots. Path tokens `{angle}` `{camera}` `{quality}`. Camera pose and look restore when the run finishes.

**Turntable** — one row: seconds + Setup + Play. Default **6 seconds** (**144 frames at 24 fps**) for a 360° linear loop around the product. **Play** previews (Setup first if needed). Advanced: Linear vs Ease, Bake, Clear, Render.

### Advanced

Collapsed closed. Mixer, **Studio Margin**, CAD extras, BlenderKit login / search / apply, Light Draw hotkeys, tokens / bookmark, turntable bake / ease / render, Apply Catcher / DoF / Quality / Size / Exposure / Look / Gobo / IES / tessellation / Cleanup. Operators stay registered.

### Utilities (optional add-on)

Install **BEHOLD Utilities** for a separate **Utilities panel** (after Advanced) — layered Danish wall, Legs / L-bracket balcony mounts, and MinAltan eave / roof section presets. Not on the product-render path. In 1.6.0 this lived behind `enable_utilities` on the monolith; v2.0.0 is its own zip. See **[docs/UTILITIES.md](docs/UTILITIES.md)**.

## Coming (not 2.0.0)

Streamed IES / gobo catalogs, logo redo, Light Wrangler viewport-gizmo parity, full BlenderKit browser. The suite split shipped in **2.0.0**. Per-body auto-dress shipped in **1.5.0**. Defeaturing lite shipped in **1.4.0**. Live tessellation regenerate shipped in **1.3.0**. IES practical lite shipped in **1.2.0**. Procedural gobos shipped in **1.1.0**. See **[ROADMAP.md](ROADMAP.md)** and [CHECKPOINT.md](CHECKPOINT.md).

## STEPper NEXT

STEPper NEXT is the primary OpenCASCADE STEP/IGES/BREP importer for BEHOLD on **Blender 5.1+ / 5.2 LTS**. It is a GPL Blender **extension** (`id = "stepper_next"`) that ships bundled OCP wheels. BEHOLD does **not** vendor STEPper into the add-on zip.

**Install STEPper NEXT for CAD:**

1. Download the platform zip from **[Peak-Design/STEPper_NEXT Releases](https://github.com/Peak-Design/STEPper_NEXT/releases)**.
2. Blender → Edit → Preferences → Get Extensions → Install from Disk (or drag the zip onto Blender).
3. Enable **STEPper NEXT**. The BEHOLD Import panel should read **STEPper NEXT ready**.

If STEPper is installed but disabled, Import Product enables it. If enable fails, BEHOLD reports the module name and the Releases URL.

BEHOLD calls `bpy.ops.import_scene.occ_import_step` with an absolute `filepath` and `override_file` = basename. That stays on STEPper's synchronous importer — it does not open STEPper's full dialog. Optional STEPper RNA (`quality_preset`, `lin_deflection_len`) is passed only when those properties exist. STEPper has **no fillet / chamfer / hole RNA** — **Cleanup (1.4.0)** uses BEHOLD's OCP path (`BRepAlgoAPI_Defeaturing` / inner-wire remove) before tessellate.

On 4.2–5.0, use BEHOLD's OCP fallback (`cadquery-ocp` / `cadquery-ocp-novtk` in Blender's Python) or an older STEPper build if you have one. OCP tessellation is a thinner fallback, not STEPper quality.

Sidebar **BEHOLD → Import** (or File → Import → **BEHOLD Product**).

Prove Import → Build → Draft with the CC0 cube at [`tests/fixtures/unit_cube.step`](tests/fixtures/unit_cube.step):

```bash
make smoke-step
# blender --background --python scripts/smoke_step_vertical.py
```

## Check for updates

BEHOLD is installed from GitHub zips, so Blender's extensions.blender.org updater does not see it. Each add-on asks the public [GitHub Releases API](https://github.com/wckdboy/BEHOLD/releases) for `wckdboy/BEHOLD` — **no token**, nothing about you or your files.

1. **Auto-check** (default on) runs in the background shortly after Blender loads, at most **once per day**. Turn it off with **Check for updates** in that add-on's preferences.
2. Click **Check for updates** any time. Preferences show last-checked status, or **Update available: x.y.z**.
3. A light notice on the **BEHOLD** tab offers **Install** / **Open release**. **X** dismisses it until you restart Blender. Failures say **what failed** and what to try next.
4. **Install** downloads that add-on's `behold-*.zip` from the release, then runs Blender 5.2 **Install from Disk** (`extensions.package_install_files` into `user_default`, overwrite + enable). Older 4.2+ builds fall back to **Add-ons → Install**.
5. **Restart Blender** to finish. The zip is in, but the old code stays in memory until restart.

If the release has no `behold-*.zip` asset, **Open release** and install the zips the same way as the first time.

## Install (Blender 5.2 LTS+)

**Use the four v2.0.0 zips.** Do not install the old monolith `behold-1.6.0.zip` next to them.

### Artist install order

1. `behold-studio-2.0.0.zip` — **BEHOLD Studio**
2. `behold-lighting-2.0.0.zip` — **BEHOLD Lighting**
3. `behold-product-2.0.0.zip` — **BEHOLD Product** (the shoot pipeline)
4. `behold-utilities-2.0.0.zip` — **BEHOLD Utilities** (optional)

Then: Blender → Edit → Preferences → **Get Extensions** → **Install from Disk** for each zip (Blender 4.2+ Add-ons → Install also works). Enable each add-on, then open the 3D Viewport sidebar (`N`) → **BEHOLD** tab.

Product-only still imports and shoots; Build Studio needs Studio; lights need Lighting. Missing siblings show a sentence (“Install BEHOLD Studio for Build Studio”) instead of crashing.

The zips also load on **4.2+** when you need them; 5.2 LTS is the production target.

**Versioned release** — push a tag `v2.0.0`. The [Build Blender add-on zip](https://github.com/wckdboy/BEHOLD/actions) workflow attaches all four zips to the [GitHub Release](https://github.com/wckdboy/BEHOLD/releases). Every push / PR also uploads the `behold-addon` artifact.

```bash
git tag v2.0.0
git push origin v2.0.0

make zip
# → dist/behold-studio-2.0.0.zip
# → dist/behold-lighting-2.0.0.zip
# → dist/behold-product-2.0.0.zip
# → dist/behold-utilities-2.0.0.zip
```

### Migrating from 1.6.0

1. Disable and uninstall the monolith **BEHOLD** add-on (`behold-1.6.0.zip` / folder `behold/`).
2. Install the four v2.0.0 zips in the order above. Do not enable both the monolith and the suite.
3. Open an existing `.blend`. Studio / lighting / product / utilities settings live on `scene.behold_studio`, `scene.behold_lighting`, `scene.behold_product`, and `scene.behold_utilities`. Rebuild Studio / re-apply a Shot if a look did not carry over.

### Preferences

Edit → Preferences → Add-ons → **BEHOLD Product** (and the sibling add-ons): branding (**BEHOLD** / **by AMIRITE.studio**), Docs and Releases links, **Check for updates**, workflow strip and 3D View header toggles, this-scene Build Studio / Material Assist after Import, Quality.

### Pie and header

**3D Viewport pie** (`Shift+Alt+B`) — West Import Product · East Still · South Light Draw · North Build Studio · North-west Turntable Setup. **3D View header** — pie / Import / Build Studio / Still. Toggle the header cluster off in preferences if you want a stock header. Pie / header register with **BEHOLD Product**.

### BlenderKit

Local Metal / Plastic / Rubber / Glass / Paint looks **do not** need BlenderKit. Enable the official BlenderKit / Blendkit extension only if you want library search; **Log In to BlenderKit** lives under **Advanced**. BEHOLD does not re-host BlenderKit assets.

## Develop

```bash
git clone https://github.com/wckdboy/BEHOLD.git
make test
make zip
make smoke-step   # Blender + OCP or STEPper; not CI
```

`make test` is offline and CI-safe. If OCP is missing, tessellation is skipped; the unit-cube fixture is still classified as CAD. `make zip` vendors `behold_common/` into each add-on, then writes the four install zips.

## Remotes

- **Primary:** GitHub [`wckdboy/BEHOLD`](https://github.com/wckdboy/BEHOLD)
- **Mirror:** Origin [`wckdboy/BEHOLD`](https://cursor.com/codebase/wckdboy/BEHOLD)

```bash
git remote add origin https://github.com/wckdboy/BEHOLD.git
git remote add cursor https://origin.cursor.com/wckdboy/BEHOLD.git
```

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
