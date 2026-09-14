<p align="center">
  <img src="docs/brand/behold_logo.png" alt="BEHOLD by AMIRITE.studio" width="280">
</p>

# BEHOLD

**BEHOLD by AMIRITE.studio** — the best product-render suite for Blender. KeyShot-simple lighting, cameras, and stills, as open source.

Official mark (Blender UI): [`behold/icons/behold_icon.png`](behold/icons/behold_icon.png) · Wordmark: [`docs/brand/behold_logo.png`](docs/brand/behold_logo.png) · also [`behold/icons/behold_logo.png`](behold/icons/behold_logo.png)

Primary Blender target: **5.2 LTS and newer**. Install still declares 4.2+ (`bl_info` / `blender_manifest.toml`) so older 4.x/5.1 builds can load the zip; production lighting, cameras, turntable, and materials are developed and tested against 5.2 LTS.

Living status (implemented vs coming) lives in **[CHECKPOINT.md](CHECKPOINT.md)**. Leveling path: **[ROADMAP.md](ROADMAP.md)**. Cadence: one focused feature cut, then a GitHub Release.

## What works (v0.25.0)

**0.25.0 is catalog resolution presets** on Shoot: compact **Size** with **Square 1:1**, **Portrait 4:5**, **Landscape 16:9** plus **2048² / 1080p / 4K**. Size is the long edge; output writes `scene.render.resolution_x` / `resolution_y` at 100% with square pixels (`pixel_aspect` 1:1). **0.24.0** is ground contact polish on Studio (**Catcher** next to **Build**). **0.23.0** is EEVEE quick look on Shoot (Draft = EEVEE / Final = Cycles). Product DoF / focus pick is **0.22.0**. Light & shadow linking lite is **0.21.0**; compositor look pack is **0.20.0**; catalog batch export is **0.19.0**; bake studio to HDRI is **0.18.0**; physical exposure polish is **0.17.0**; light shaping lite is **0.16.0**; Shot Manager is **0.14.0**; **0.15.0** is test hardening + N-panel draw-pass cache (no artist chrome).

**First-ship N-panel** — scroll top-to-bottom in work order: **Import → Studio → Lights → Materials → Cameras → Shoot → Advanced** (v0.12.0). Shoot is last so you do not scroll past it to dress, then back. The BEHOLD tab has a branded hero (**BEHOLD** / **by AMIRITE.studio**, official mark) and a compact **Import → Studio → Dress → Shoot** strip (Dress Next = **Material Assist**):

1. **Import** — Import Product file picker + CAD backend line (STEPper ready / OCP fallback / Install STEPper NEXT)
2. **Studio** — backdrop White / Grey / Black + **Build** + **Catcher**, compact **HDRI** (Load / Reset, strength, Z rotation, optional reflections-only), compact **Bake HDRI** (1K/2K, path, optional world / apply)
3. **Lights** — inventory + Light Draw + **Shape** presets (Softbox / Strip / Octa / Hard / Rim) + **Linking** (Link Selected / Unlink / Solo product)
4. **Materials** — local looks + Assist
5. **Cameras** — add / frame product cameras + compact **DoF** (on/off, f-stop, Focus on product / Focus on selected)
6. **Shoot** — Draft / Final (**Draft = EEVEE · Final = Cycles**), Still, Render, compact **Size** (Square 1:1 / Portrait 4:5 / Landscape 16:9 + 2048² / 1080p / 4K), compact **Look** (EV / Kelvin WB / False Color, plus Clean / Catalog / Dramatic compositor presets), compact **Shots** (Add / Apply / rename / Delete), compact **Batch export** (Front / ¾ / Top and optional Saved shots), compact **Turntable** (seconds + Setup + Play)

Each section uses the same card rhythm (box + header icon). Empty states keep **one primary CTA** (Build Studio / Import Product) with quieter secondaries underneath. Operator failures use the same copy: a short sentence plus what to do next.

**Faster actions** — pie menu + 3D View header (see [Pie and header](#pie-and-header) below).

**Easy update** — Check for updates in add-on preferences (or the notice on the BEHOLD tab). Auto-check is on by default, at most once a day. See [Updates](#updates).

**Lights** — native multi-light inventory plus Light Draw, one-click area looks, and linking lite:

- Add / remove / set active BEHOLD studio lights
- Per-light energy
- **Shape** presets on the active light: Softbox, Strip, Octa, Hard, Rim (size / spread / procedural falloff)
- **Linking (0.21.0)** — **Link Selected** cycles include → exclude on the selection (Light Wrangler L, minus the viewport modal). **Unlink** drops the selection, or clears the light if nothing is selected. **Solo product** includes only the product (cyclorama stays unlit). **Light / Shadow** picks Cycles `receiver_collection` vs `blocker_collection` (shadow linking when the 5.2 API is present). Missing engine or API reports a sentence plus the next step. Not gobos / IES / Wrangler gizmos
- Empty state when the studio has no lights yet
- Light Draw **Aim: Active | New** — Reflect / Direct / Orbit (LMB aim, scroll power/size/distance, solo)

**Cameras** — product cameras without hunting Blender's default camera UI:

- Add a BEHOLD camera with product defaults (85 mm, full-frame 36×24 mm sensor, framed on the selection or product)
- List / set active / frame selected-or-product / delete / clear
- Active camera is the Shoot still camera (and the main-camera bookmark)
- **DoF (0.22.0)** — **DoF** toggle and **f-stop** (product default **f/5.6**) on the active BEHOLD camera. **Focus on product** sets distance to the product AABB center (studio sweep excluded). **Focus on selected** picks the facing surface of the selected mesh. Maps to Blender 5.2 `Camera.dof` (`use_dof` / `aperture_fstop` / `focus_distance`). Missing RNA or empty product/selection reports a sentence plus the next step. Empty Cameras state unchanged. **Apply DoF** stays in Advanced. Not a Photographer viewport picker / gobos / IES

**Draft / Final (0.23.0)** — quality-linked engine on Shoot, not a second engine panel:

- **Draft** switches to **EEVEE Next** when the Blender build has it (`BLENDER_EEVEE_NEXT` on 4.2–4.5; `BLENDER_EEVEE` on 5.2, which *is* Next). Cheap product defaults: shadows on, screen-space / ray-traced reflections on, 32 TAA samples
- **Final** (and Advanced **Product** / **Hero**) stay **Cycles** — 256 / 128 / 512 samples with denoising. Client stills do not silently stay on EEVEE
- Caption on the card: **Draft = EEVEE · Final = Cycles**. Live RNA update; **Apply Quality** stays in Advanced
- If EEVEE Next is missing, Draft falls back to Cycles (32 samples) and reports a sentence plus the next step (`NO_EEVEE`). Missing Cycles on Final reports `NO_CYCLES`

**Size (0.25.0)** — one-click catalog output sizes on Shoot, not a second Output Properties panel:

- **Square 1:1**, **Portrait 4:5**, **Landscape 16:9** compose with **2048²**, **1080p**, and **4K**. Size is the long edge (2048 / 1920 / 3840)
- Writes `scene.render.resolution_x` / `resolution_y`, `resolution_percentage` 100, and square `pixel_aspect` (1:1) so leftover anamorphic settings do not skew the still
- Default is Square 1:1 at 2048² (2048 × 2048). Landscape + 1080p is 1920 × 1080; Landscape + 4K is 3840 × 2160. A readout shows the computed pixels
- Live RNA update; **Apply Size** stays in Advanced. Unknown aspect / size reports a sentence plus the next step. Draft / Final path unchanged. Not gobos / IES / logo

**Catcher (0.24.0)** — believable ground contact after Build Studio, not a second engine panel:

- **Catcher** toggle sits next to **Build** (default on). Rebuild or the live toggle applies it — no hand-placed planes
- **Cyclorama** keeps the White / Grey / Black sweep and adds a soft contact disc under the product (`BEHOLD_ContactShadow`)
- **Solid / HDRI** (Advanced backdrop type) get an optional `BEHOLD_ShadowCatcher` plane with Cycles `Object.is_shadow_catcher`
- EEVEE Draft: light contact-shadow RNA plus a transparent radial material when catcher RNA is missing. Not a new EEVEE engine stack
- Missing product reports a sentence plus the next step (`NO_PRODUCT_FOR_CATCHER`). **Apply Catcher** stays in Advanced. Not gobos / IES / logo

**Turntable** — one row on Shoot, not a new sidebar section:

- Default **6 seconds** at scene fps (**144 frames at 24 fps**) for a 360° linear loop
- Uses the active BEHOLD / scene camera and the product bounds (studio sweep excluded)
- Empty state if there is no camera or product yet (Build Studio / Add Camera / Import)
- **Play** previews (Setup first if needed). **Advanced**: Linear vs Ease, Bake, Clear, Render

**Look (0.17.0 / 0.20.0)** — Photographer-class lite on Shoot, not buried only in Advanced:

- **EV** — exposure compensation in stops (−6 to +6), live on Color Management
- **WB** — white balance in Kelvin (D65 = 6500 K). Blender 5.2 uses `use_white_balance` + temperature; older builds fall back to a D65 offset
- **False Color** — AgX-safe heat map for hot/cold checks; toggling off restores the previous view transform instead of forcing AgX over Filmic
- **Clean / Catalog / Dramatic** (0.20.0) — one-click compositor still looks. Catalog is mild vignette + grain with bloom off; Dramatic adds stronger vignette/grain and mild bloom-safe glare. **Compositor** toggles the graph on or off (BEHOLD builds and tears down its own nodes; it will not overwrite a custom compositor)
- Dragging EV / WB applies immediately (viewport and render). Preset + toggle apply the compositor graph. **Apply Exposure** and **Apply Look** stay in Advanced. Light Draw **F** still toggles False Color.

**Bake HDRI (0.18.0)** — capture the studio light rig as a 360° environment for reuse / Eevee:

- **Bake HDRI** renders BEHOLD lights (product and cyclorama hidden) to an equirectangular `.exr` / `.hdr`
- **1K** (1024×512) or **2K** (2048×1024). Empty path writes next to the `.blend`, or to temp if the file is unsaved
- Optional **Include world** bakes the current HDRI together with the lights
- Optional **Apply after bake** loads the map as the scene world (strength 1, rotation 0). Mute Lights if you want the HDRI alone
- Needs a BEHOLD light — empty inventory reports **Build Studio or Add Light**. Bad types report a sentence plus `.hdr` / `.exr`

**Batch export (0.19.0)** — catalog stills in one click on Shoot, not buried only in Advanced:

- **Front / ¾ / Top** — three stills around the product (imported mesh or selection)
- **Saved shots** — optional; applies each Shot Manager preset and writes a still (camera / quality / HDRI / output tokens)
- Output folder tokens `{angle}` `{camera}` `{quality}` — `{angle}` is `front` / `three_quarter` / `top`, or a slug of the shot name
- Progress reports `Batch n/total`. Missing product / camera / shots stay a sentence plus the next step. Camera pose and scene look restore when the run finishes
- The old Advanced **Batch Product Angles** button is the same operator (label **Batch export**). The output folder picker stays in Advanced

**Shots (0.14.0)** — named shoot presets on the same Shoot panel, KeyShot Studios–skinny:

- **Add** stores the current camera, quality, turntable seconds, HDRI (path / strength / rotation / reflections-only), backdrop tone, and output folder tokens
- **Apply** restores those scene settings and the camera — it does not rebuild the studio or touch the product mesh
- Rename inline; **X** deletes. Shots live on the `.blend` (`scene.behold.shots`)
- Empty state until you save one: Add from the current camera, quality, and HDRI

**Materials** — product looks without hunting Blender's material UI:

- One-click **Metal / Plastic / Rubber / Glass / Paint** on the selected product mesh
- Empty state if nothing dressable is selected (Import or select a mesh)
- **Assist** applies a matching local look from the filename / STEP hint — **no BlenderKit account required**
- If BlenderKit is signed in, Assist still applies the local look and also runs search

Parked chrome (BlenderKit login / search / apply, mixer, **Studio Margin**, **Apply Catcher**, CAD extras, tokens/bookmark, Light Draw hotkeys, turntable bake/ease/render, Apply DoF, Apply Quality, Apply Size) is in **Advanced**, collapsed closed. Operators stay registered. EV / WB / False Color / compositor looks, Size, and Batch export also remain under Advanced → Shoot for people who look there.

Backends:

- **Import Product** — pick `.obj`, `.fbx`, `.stl`, `.glb`/`.gltf`, `.3mf` (when Blender has an importer), or STEP/IGES/BREP → import → optional **Build Studio** + **Material Assist** from the filename
- **Studio** — select mesh(es) → **Build Studio**. Cyclorama floor / wall auto-fit the product world AABB (v0.11.0: XY diagonal × margin, wall clears height with headroom). Rebuild replaces the old sweep. Lights sit outside the floor. Optional **Studio Margin** lives in Advanced (default 2.0×). White / Grey / Black first-ship tones + one Build button + **Catcher** (v0.24.0: soft contact on the cyclorama, or a Cycles catcher plane with EEVEE fallback for Solid / HDRI). **HDRI** (v0.13.0): Load an HDR/EXR from disk (OpenHDRI / Poly Haven / BYO), set strength and Z rotation, optional reflections-only + background strength, **Reset** to a solid studio world. **Bake HDRI** (v0.18.0): 1K/2K equirectangular EXR/HDR of the light rig, optional world, optional apply as world.
- **Lights** — named BEHOLD area lights; Build Studio seeds Key / Fill / Rim and marks Key active; **Apply** a Softbox / Strip / Octa / Hard / Rim look to the active light; **Link Selected / Unlink / Solo product** against that light (Cycles light linking, optional shadow linking)
- **Light Draw** — Reflect / Direct / Orbit modal aimed at the **active** light or a **new** light
- **Cameras** — named BEHOLD product cameras; Build Studio seeds `BEHOLD_Camera` and marks it active; Add Camera / Frame / Clear from the N-panel; **DoF** on/off, f-stop, Focus on product / Focus on selected (`Camera.dof` RNA)
- **Turntable** — `BEHOLD_TurntablePivot` orbits the active camera; Clear drops the pivot only; Bake writes camera loc/rot then removes the pivot
- **Materials** — local PBR rack (metal, plastic, rubber, glass, paint) applied from the N-panel; Material Assist finishes with that look
- **BlenderKit** — optional soft-dependency bridge (login / search / apply in Advanced). Local looks work without an account
- **Shoot** — compact **Size** (Square 1:1 / Portrait 4:5 / Landscape 16:9 + 2048² / 1080p / 4K on `scene.render` resolution), compact **Look** (EV / Kelvin white balance / False Color on Color Management; Clean / Catalog / Dramatic compositor presets), **Draft = EEVEE · Final = Cycles** (Product / Hero stay Cycles), output path tokens (`{angle}` `{camera}` `{quality}`), main-camera bookmark, still, **Batch export** (front / ¾ / top and optional saved shots), turntable, **Shot Manager** (named camera + quality + HDRI + backdrop + output presets)
- **CAD** — first-class [STEPper NEXT](https://github.com/Peak-Design/STEPper_NEXT) for STEP/IGES/BREP on 5.1+/5.2 LTS (`import_scene.occ_import_step`). OCP fallback only if STEPper is missing and OpenCASCADE bindings actually import; otherwise Import fails with the [STEPper Releases](https://github.com/Peak-Design/STEPper_NEXT/releases) URL. Mesh formats stay native. Shared `product_import_dispatch` / `run_product_import`. CI-safe unit-cube STEP fixture; optional Blender smoke (`make smoke-step`) for Import → Build → Draft still.

## Coming (not this release)

Gobos / IES, Light Wrangler viewport-gizmo parity, live tessellation regenerate, defeaturing, per-body auto-dress, full BlenderKit browser. See **[ROADMAP.md](ROADMAP.md)** and [CHECKPOINT.md](CHECKPOINT.md).

## Import Product

Sidebar **BEHOLD → Import** (or File → Import → **BEHOLD Product**):

| Kind | Extensions | Backend |
| --- | --- | --- |
| Mesh | `.obj` `.fbx` `.stl` `.glb` `.gltf` | Native Blender 4.2+ / 5.2 LTS (`wm.obj_import`, `import_scene.fbx` / `gltf`, `wm.stl_import`) |
| 3MF | `.3mf` | Native or add-on importer when present (`wm.threemf_import` / `import_mesh.threemf`) |
| CAD | `.step` `.stp` `.iges` `.igs` `.brep` `.brp` | **STEPper NEXT** (required for production CAD on 5.1+/5.2 LTS). Optional BEHOLD OCP fallback if STEPper is not installed and `cadquery-ocp` is in Blender's Python. |

Mesh and 3MF paths **never** require STEPper. The Import panel shows **STEPper NEXT ready**, **OCP fallback**, or **Install STEPper NEXT** (opens Releases). CAD import without STEPper or OCP **fails loudly** — it does not silently cancel.

After import, BEHOLD can:

1. **Build Studio** around the new mesh(es) (toggle on the file-browser operator / Advanced).
2. **Material Assist** — guess a look from the filename, extension, or STEP material names (`housing_aluminum.step` → brushed aluminum → **Metal** on the mesh). Applies the local rack. Searches BlenderKit only if you are signed in.

### STEPper NEXT

STEPper NEXT is the primary OpenCASCADE STEP/IGES/BREP importer for BEHOLD on **Blender 5.1+ / 5.2 LTS**. It is a GPL Blender **extension** (`id = "stepper_next"`) that ships bundled OCP wheels. BEHOLD does **not** vendor STEPper into the add-on zip.

**Install STEPper NEXT for CAD:**

1. Download the platform zip from **[Peak-Design/STEPper_NEXT Releases](https://github.com/Peak-Design/STEPper_NEXT/releases)**.
2. Blender → Edit → Preferences → Get Extensions → Install from Disk (or drag the zip onto Blender).
3. Enable **STEPper NEXT**. The BEHOLD Import panel should read **STEPper NEXT ready**.

If STEPper is installed but disabled, Import Product enables it. If enable fails, BEHOLD reports the module name and the Releases URL.

BEHOLD calls `bpy.ops.import_scene.occ_import_step` with an absolute `filepath` and `override_file` = basename (the same scripted path STEPper's `worker.py` uses). That stays on STEPper's synchronous importer — it does not open STEPper's full dialog and does not use `stepper.background_import`. Optional STEPper RNA (`quality_preset`, `lin_deflection_len`) is passed only when those properties exist.

On 4.2–5.0, use BEHOLD's OCP fallback (`cadquery-ocp` / `cadquery-ocp-novtk` in Blender's Python) or an older STEPper build if you have one. OCP tessellation is a thinner fallback, not STEPper quality.

### STEP vertical smoke

Prove Import Product → Build Studio → Shoot (Draft) with the CC0 10 mm cube at [`tests/fixtures/unit_cube.step`](tests/fixtures/unit_cube.step) (provenance in that folder's README). `make test` classifies it as CAD and tessellates via OCP when bindings exist. With Blender and OCP or STEPper:

```bash
make smoke-step
# blender --background --python scripts/smoke_step_vertical.py
# still → dist/smoke/still.png (or BEHOLD_SMOKE_OUT)
```

## Studio

Sidebar **BEHOLD → Studio**:

1. Select the product mesh(es). Pick **White / Grey / Black**. Click **Build**. **Catcher** (default on) adds ground contact without a manual plane.
2. The cyclorama sizes itself from the product world AABB: floor from the XY diagonal (or max width/depth) × **Studio Margin** (default 2.0×), wall from product height × 1.75 headroom. Lights sit outside the sweep. Build replaces any existing `BEHOLD_Cyclorama`. On a cyclorama, Catcher places a soft contact disc under the product; Solid / HDRI (Advanced) get a Cycles shadow-catcher plane (EEVEE fallback material if that RNA is missing).
3. Empty / error if nothing is selected: **No mesh selected — select the product or Import Product**. Optional **Studio Margin** (1.5–2.5×) and **Apply Catcher** live under **Advanced → Studio**. First-ship stays Build + Catcher plus the HDRI card below.

**HDRI world** (same Studio section — not a new panel):

1. **Load** an `.hdr` / `.exr` (or still image) from disk — OpenHDRI, Poly Haven, or any file you already have.
2. Drag **Strength** and **Rotation** (degrees around Z). Reflections on chrome and the visible background update together.
3. **Reflections only** keeps the HDRI in lighting / reflections and uses **Background** for what the camera sees (`0` hides the environment behind the cyclorama). Works in Cycles and EEVEE.
4. **Reset** restores a solid studio world. Missing files and bad types report a sentence plus what to do next.

**Bake HDRI** (same Studio section):

1. **Build Studio** (or **Add Light**) so there is a rig to capture.
2. Pick **1K** or **2K**. Leave the path empty to write `behold_studio.exr` next to the `.blend` (or in temp if unsaved), or choose an `.exr` / `.hdr`.
3. Optional **Include world** keeps the current environment in the bake. Optional **Apply after bake** loads the file as the scene world.
4. Click **Bake HDRI**. Product mesh and cyclorama stay out of the 360° map. Mute Lights after Apply if you want the HDRI alone (Eevee / hand-off).

## Lights

Sidebar **BEHOLD → Lights**:

1. **Build Studio** (or **Add Light**) so the list is not empty.
2. Click the radio to set **Active**. Drag wattage on the row. **X** removes that light.
3. Pick a **Shape** (Softbox / Strip / Octa / Hard / Rim) and **Apply to active**. That sets size, spread, and a procedural softbox falloff on the area light — no extra image files.
4. Light Draw **Aim = Active** moves the current light; **Aim = New** creates `BEHOLD_Draw_###` and aims it.
5. In the viewport: LMB drag aim · Wheel power · Shift+Wheel size · Ctrl+Wheel distance · `1`/`2`/`3` mode · `S` solo · Esc exit.

Hotkey legend stays under **Advanced**. Key / Fill / Rim mixer stays under **Advanced → Studio**.

## Cameras

Sidebar **BEHOLD → Cameras**:

1. **Build Studio** (or **Add Camera**) so the list is not empty.
2. Click the radio to set **Active** — that becomes the scene camera and the Shoot still / bookmark.
3. Drag focal length on the row. The zoom-selected icon **Frames** that camera on the selection (or the product if nothing is selected). **X** removes it.
4. **Add** makes another `BEHOLD_Camera_###` with the mm field as the lens. **Frame** reframes the active camera. **Clear** removes the BEHOLD camera kit.

Bookmark / Use Main stay under **Advanced → Shoot** for non-BEHOLD cameras.

## Look

Sidebar **BEHOLD → Shoot**:

1. After Draft / Final (**Draft = EEVEE · Final = Cycles**), the compact **Look** card has **EV**, **WB** (Kelvin), **False Color**, and **Clean / Catalog / Dramatic**.
2. Drag EV to lift or crush the still. 0 is the Color Management default.
3. Drag WB in Kelvin. **6500 K** is D65 (neutral). Set ~3200 K when the lights are tungsten so whites come back; raise it if a cool HDRI went blue.
4. Toggle **False Color** to meter clipping, then toggle off — BEHOLD restores AgX (or whatever look you were on), not a hard Filmic reset.
5. Pick **Catalog** (pack-shot vignette + grain, bloom off) or **Dramatic** (stronger edges + mild bloom-safe glare). **Clean** is a compositor passthrough. Toggle **Compositor** to build or tear down those nodes. A custom compositor in the scene reports a sentence plus the next step instead of being overwritten.
6. Still / Render / batch / turntable already push EV / WB and re-apply the compositor look when the toggle is on. Light Draw **F** toggles False Color while aiming.

Apply Exposure and Apply Look in **Advanced → Shoot** re-push the same props if you edited Color Management or the compositor by hand.

## Turntable

Sidebar **BEHOLD → Shoot**:

1. **Build Studio** (or **Add Camera**) so there is a product and a camera. The compact row stays empty-state until both exist.
2. Default **6 seconds** — **144 frames at 24 fps** (or `seconds ×` the scene fps) for a 360° **linear** loop. Drag seconds for a slower or faster spin.
3. **Setup** parents the active BEHOLD camera to `BEHOLD_TurntablePivot` and keys Z rotation. Linear keys 360° one frame past the last rendered frame so looping does not freeze on a duplicate start pose.
4. **Play** previews (runs Setup first if the pivot is missing).
5. **Advanced → Shoot**: **Linear** vs **Ease** (ease is a one-shot in/out, not a loop), **Bake** (camera loc/rot keys, then delete the pivot), **Clear** (unparent, restore the previous frame range, delete the pivot — or strip baked camera loc/rot), **Render Turntable**.

Clear / Bake only touch the turntable pivot (and baked camera location / rotation keys). Other objects' animation is left alone.

## Shots

Sidebar **BEHOLD → Shoot**:

1. Set the camera, Draft/Final (or Product/Hero in Advanced), turntable seconds, HDRI, and backdrop the way you want the catalog frame.
2. **Add** saves that as a named shot on this `.blend`. Empty state until the first one: **Add** from the current camera, quality, and HDRI.
3. Click **Apply** (or the radio) to flip to another shot — camera, quality, HDRI world, backdrop tone, and output folder tokens come back. The product mesh stays put.
4. Edit the name on the row to rename. **X** deletes that shot.

Save two or three (hero chrome vs pack shot vs turntable) and flip without duplicating the file. Gobos, IES, and full material colorways are not stored on a shot.

## Materials

Sidebar **BEHOLD → Materials**:

1. Select the product mesh (not the cyclorama / shadow catcher / contact disc).
2. Click **Metal**, **Plastic**, **Rubber**, **Glass**, or **Paint**. A Principled BSDF look lands on the mesh.
3. Or click **Assist** — BEHOLD maps the filename / STEP hint to that rack and applies it. No BlenderKit account needed.
4. Empty state if nothing is selected: Import a product or select a mesh.

BlenderKit login / search / apply stay under **Advanced → Materials / BlenderKit**. Assist still searches there when you are signed in; the local look is already on the mesh.

## Pie and header

**3D Viewport pie** (`Shift+Alt+B`) — `wm.call_menu_pie` → `BEHOLD_MT_pie`:

| Direction | Action |
| --- | --- |
| West | Import Product |
| East | Still |
| South | Light Draw |
| North | Build Studio |
| North-west | Turntable Setup |

The keymap is registered on the add-on keyconfig for **3D View** (Shift+Alt+B). Rebind in Blender Preferences → Keymap if it collides.

**3D View header** — icon cluster on the viewport header: pie, Import, Build Studio, Still (the three-click path). Toggle it off under add-on preferences if you want a stock header.

## Preferences

Edit → Preferences → Add-ons → **BEHOLD**:

- Branding row (official mark + **BEHOLD** / **by AMIRITE.studio**) plus Docs and Releases links
- **Updates** — **Check for updates**, last-checked status, **Update available: x.y.z** with **Install** / **Open release**. **Check for updates** toggle (default on) asks GitHub at most once a day
- **Workflow strip** and **3D View header shortcuts** toggles
- This-scene **Build Studio after Import**, **Material Assist after Import**, and **Quality** (same scene props as Advanced)

## Updates

BEHOLD is installed from a GitHub zip, so Blender's extensions.blender.org updater does not see it. The add-on asks the public [GitHub Releases API](https://github.com/wckdboy/BEHOLD/releases) for `wckdboy/BEHOLD` — **no token**, nothing about you or your files.

1. **Auto-check** (default on) runs in the background shortly after Blender loads, at most **once per day**. Turn it off with **Check for updates** in add-on preferences.
2. Click **Check for updates** any time. Preferences show last-checked status, or **Update available: x.y.z**.
3. A light notice on the **BEHOLD** tab offers **Install** / **Open release**. **X** dismisses it until you restart Blender. If the check or install fails, the same notice (and preferences) say **what failed** and what to try next: check your network, **Check again**, or **Open release**.
4. **Install** downloads `behold-*.zip` from that release, then runs Blender 5.2 **Install from Disk** (`extensions.package_install_files` into `user_default`, overwrite + enable). Older 4.2+ builds fall back to **Add-ons → Install**.
5. **Restart Blender** to finish. In-place replace of a loaded add-on is fragile; the zip is in, but the old code is still in memory until restart.

If the release has no `behold-*.zip` asset, **Open release** and install the zip the same way as the first time. Failures are not silent.

## Download install zip (GitHub Actions)

1. **Every push / PR** — Actions → **Build Blender add-on zip** → download the `behold-addon` artifact (`behold-0.25.0.zip`).
2. **Versioned release** — push a tag `v0.25.0` (or later). The same workflow attaches the zip to the [GitHub Release](https://github.com/wckdboy/BEHOLD/releases) for one-click download.

```bash
git tag v0.25.0
git push origin v0.25.0
```

## Build install zip locally

```bash
make zip
# → dist/behold-0.25.0.zip
```

Or: `bash scripts/build_addon.sh`

## Install (Blender 5.2 LTS+)

1. Get `behold-*.zip` (Actions artifact, Release asset, or `make zip`).
2. Blender → Edit → Preferences → Add-ons → Install… → select the zip  
   (or Get Extensions → Install from Disk).
3. Enable **BEHOLD**, then open the 3D Viewport sidebar (`N`) → **BEHOLD** tab.

Alternate (dev): copy or symlink `behold/` into your Blender `scripts/addons/` directory.

The zip also loads on **4.2+** when you need it; 5.2 LTS is the production target.

### BlenderKit

Local Metal / Plastic / Rubber / Glass / Paint looks **do not** need BlenderKit. Enable the official BlenderKit / Blendkit extension only if you want library search; **Log In to BlenderKit** lives under **Advanced → Materials / BlenderKit**. BEHOLD does not re-host BlenderKit assets; your BlenderKit account/plan applies.

## Develop

```bash
git clone https://github.com/wckdboy/BEHOLD.git
# Point Blender at /path/to/repo/behold via preferences or symlink into addons/
make test
make zip

# Real STEP Import → Build → Draft still (Blender + OCP or STEPper; not CI)
blender --background --python scripts/smoke_step_vertical.py
# or: make smoke-step
```

`make test` is offline and CI-safe. If OCP is missing, tessellation is skipped; the unit-cube fixture is still classified as CAD (not mesh). The smoke script fails clearly (exit 2) when no CAD backend is present.

## Remotes

- **Primary:** GitHub [`wckdboy/BEHOLD`](https://github.com/wckdboy/BEHOLD)
- **Mirror:** Origin [`wckdboy/BEHOLD`](https://cursor.com/codebase/wckdboy/BEHOLD)

```bash
git remote add origin https://github.com/wckdboy/BEHOLD.git
git remote add cursor https://origin.cursor.com/wckdboy/BEHOLD.git
```

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
