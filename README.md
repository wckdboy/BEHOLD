# BEHOLD

**BEHOLD by AMIRITE.studio** — open-source Blender add-on for KeyShot-simple product rendering.

Primary Blender target: **5.2 LTS and newer**. Install still declares 4.2+ (`bl_info` / `blender_manifest.toml`) so older 4.x/5.1 builds can load the zip; production lighting, cameras, turntable, and materials are developed and tested against 5.2 LTS.

Living status (implemented vs coming) lives in **[CHECKPOINT.md](CHECKPOINT.md)**. Cadence: one focused feature cut, then a GitHub Release.

## What works (v0.12.0)

**First-ship N-panel** — scroll top-to-bottom in work order: **Import → Studio → Lights → Materials → Cameras → Shoot → Advanced**. Shoot is last so you do not scroll past it to dress, then back. The BEHOLD tab has a branded hero (**BEHOLD** / **by AMIRITE.studio**) and a compact **Import → Studio → Dress → Shoot** strip (Dress Next = **Material Assist**):

1. **Import** — Import Product file picker + CAD backend line (STEPper ready / OCP fallback / Install STEPper NEXT)
2. **Studio** — backdrop White / Grey / Black + **Build** (cyclorama auto-fits the product)
3. **Lights** — inventory + Light Draw
4. **Materials** — local looks + Assist
5. **Cameras** — add / frame product cameras
6. **Shoot** — Draft / Final, Still, Render, compact **Turntable** (seconds + Setup + Play)

Each section uses the same card rhythm (box + header icon). Empty states keep **one primary CTA** (Build Studio / Import Product) with quieter secondaries underneath. Operator failures use the same copy: a short sentence plus what to do next.

**Faster actions** — pie menu + 3D View header (see [Pie and header](#pie-and-header) below).

**Easy update** — Check for updates in add-on preferences (or the notice on the BEHOLD tab). Auto-check is on by default, at most once a day. See [Updates](#updates).

**Lights** — native multi-light inventory plus Light Draw:

- Add / remove / set active BEHOLD studio lights
- Per-light energy
- Empty state when the studio has no lights yet
- Light Draw **Aim: Active | New** — Reflect / Direct / Orbit (LMB aim, scroll power/size/distance, solo)

**Cameras** — product cameras without hunting Blender's default camera UI:

- Add a BEHOLD camera with product defaults (85 mm, full-frame 36×24 mm sensor, framed on the selection or product)
- List / set active / frame selected-or-product / delete / clear
- Active camera is the Shoot still camera (and the main-camera bookmark)

**Turntable** — one row on Shoot, not a new sidebar section:

- Default **6 seconds** at scene fps (**144 frames at 24 fps**) for a 360° linear loop
- Uses the active BEHOLD / scene camera and the product bounds (studio sweep excluded)
- Empty state if there is no camera or product yet (Build Studio / Add Camera / Import)
- **Play** previews (Setup first if needed). **Advanced**: Linear vs Ease, Bake, Clear, Render

**Materials** — product looks without hunting Blender's material UI:

- One-click **Metal / Plastic / Rubber / Glass / Paint** on the selected product mesh
- Empty state if nothing dressable is selected (Import or select a mesh)
- **Assist** applies a matching local look from the filename / STEP hint — **no BlenderKit account required**
- If BlenderKit is signed in, Assist still applies the local look and also runs search

Parked chrome (BlenderKit login / search / apply, mixer, **Studio Margin**, CAD extras, batch, EV/WB/tokens/bookmark, Light Draw hotkeys, turntable bake/ease/render) is in **Advanced**, collapsed closed. Operators stay registered.

Backends:

- **Import Product** — pick `.obj`, `.fbx`, `.stl`, `.glb`/`.gltf`, `.3mf` (when Blender has an importer), or STEP/IGES/BREP → import → optional **Build Studio** + **Material Assist** from the filename
- **Studio** — select mesh(es) → **Build Studio**. Cyclorama floor / wall auto-fit the product world AABB (v0.11.0: XY diagonal × margin, wall clears height with headroom). Rebuild replaces the old sweep. Lights sit outside the floor. Optional **Studio Margin** lives in Advanced (default 2.0×). White / Grey / Black first-ship tones + one Build button.
- **Lights** — named BEHOLD area lights; Build Studio seeds Key / Fill / Rim and marks Key active
- **Light Draw** — Reflect / Direct / Orbit modal aimed at the **active** light or a **new** light
- **Cameras** — named BEHOLD product cameras; Build Studio seeds `BEHOLD_Camera` and marks it active; Add Camera / Frame / Clear from the N-panel
- **Turntable** — `BEHOLD_TurntablePivot` orbits the active camera; Clear drops the pivot only; Bake writes camera loc/rot then removes the pivot
- **Materials** — local PBR rack (metal, plastic, rubber, glass, paint) applied from the N-panel; Material Assist finishes with that look
- **BlenderKit** — optional soft-dependency bridge (login / search / apply in Advanced). Local looks work without an account
- **Shoot** — EV / white balance / false color, Draft·Final·Product·Hero quality presets, output path tokens (`{angle}` `{camera}` `{quality}`), main-camera bookmark, still, batch angles (front / ¾ / top), turntable
- **CAD** — first-class [STEPper NEXT](https://github.com/Peak-Design/STEPper_NEXT) for STEP/IGES/BREP on 5.1+/5.2 LTS (`import_scene.occ_import_step`). OCP fallback only if STEPper is missing and OpenCASCADE bindings actually import; otherwise Import fails with the [STEPper Releases](https://github.com/Peak-Design/STEPper_NEXT/releases) URL. Mesh formats stay native. Shared `product_import_dispatch` / `run_product_import`. CI-safe unit-cube STEP fixture; optional Blender smoke (`make smoke-step`) for Import → Build → Draft still.

## Coming (not this release)

Gobos / IES / scrims, bake-to-HDRI, light/shadow linking UI, live tessellation regenerate, defeaturing, per-body auto-dress from STEP material names, full BlenderKit browser. See [CHECKPOINT.md](CHECKPOINT.md).

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

1. Select the product mesh(es). Pick **White / Grey / Black**. Click **Build**.
2. The cyclorama sizes itself from the product world AABB: floor from the XY diagonal (or max width/depth) × **Studio Margin** (default 2.0×), wall from product height × 1.75 headroom. Lights sit outside the sweep. Build replaces any existing `BEHOLD_Cyclorama`.
3. Empty / error if nothing is selected: **No mesh selected — select the product or Import Product**. Optional **Studio Margin** (1.5–2.5×) is under **Advanced → Studio**. First-ship stays one Build button.

## Lights

Sidebar **BEHOLD → Lights**:

1. **Build Studio** (or **Add Light**) so the list is not empty.
2. Click the radio to set **Active**. Drag wattage on the row. **X** removes that light.
3. Light Draw **Aim = Active** moves the current light; **Aim = New** creates `BEHOLD_Draw_###` and aims it.
4. In the viewport: LMB drag aim · Wheel power · Shift+Wheel size · Ctrl+Wheel distance · `1`/`2`/`3` mode · `S` solo · Esc exit.

Hotkey legend stays under **Advanced**. Key / Fill / Rim mixer stays under **Advanced → Studio**.

## Cameras

Sidebar **BEHOLD → Cameras**:

1. **Build Studio** (or **Add Camera**) so the list is not empty.
2. Click the radio to set **Active** — that becomes the scene camera and the Shoot still / bookmark.
3. Drag focal length on the row. The zoom-selected icon **Frames** that camera on the selection (or the product if nothing is selected). **X** removes it.
4. **Add** makes another `BEHOLD_Camera_###` with the mm field as the lens. **Frame** reframes the active camera. **Clear** removes the BEHOLD camera kit.

Bookmark / Use Main stay under **Advanced → Shoot** for non-BEHOLD cameras.

## Turntable

Sidebar **BEHOLD → Shoot**:

1. **Build Studio** (or **Add Camera**) so there is a product and a camera. The compact row stays empty-state until both exist.
2. Default **6 seconds** — **144 frames at 24 fps** (or `seconds ×` the scene fps) for a 360° **linear** loop. Drag seconds for a slower or faster spin.
3. **Setup** parents the active BEHOLD camera to `BEHOLD_TurntablePivot` and keys Z rotation. Linear keys 360° one frame past the last rendered frame so looping does not freeze on a duplicate start pose.
4. **Play** previews (runs Setup first if the pivot is missing).
5. **Advanced → Shoot**: **Linear** vs **Ease** (ease is a one-shot in/out, not a loop), **Bake** (camera loc/rot keys, then delete the pivot), **Clear** (unparent, restore the previous frame range, delete the pivot — or strip baked camera loc/rot), **Render Turntable**.

Clear / Bake only touch the turntable pivot (and baked camera location / rotation keys). Other objects' animation is left alone.

## Materials

Sidebar **BEHOLD → Materials**:

1. Select the product mesh (not the cyclorama / shadow catcher).
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

- Branding line (**BEHOLD** / **by AMIRITE.studio**) plus Docs and Releases links
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

1. **Every push / PR** — Actions → **Build Blender add-on zip** → download the `behold-addon` artifact (`behold-0.12.0.zip`).
2. **Versioned release** — push a tag `v0.12.0` (or later). The same workflow attaches the zip to the [GitHub Release](https://github.com/wckdboy/BEHOLD/releases) for one-click download.

```bash
git tag v0.12.0
git push origin v0.12.0
```

## Build install zip locally

```bash
make zip
# → dist/behold-0.12.0.zip
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
