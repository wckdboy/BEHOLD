# BEHOLD

**BEHOLD by AMIRITE.studio** — open-source Blender add-on for KeyShot-simple product rendering.

Primary Blender target: **5.2 LTS and newer**. Install still declares 4.2+ (`bl_info` / `blender_manifest.toml`) so older 4.x/5.1 builds can load the zip; production lighting is developed and tested against 5.2 LTS.

Living status (implemented vs coming) lives in **[CHECKPOINT.md](CHECKPOINT.md)**. Cadence: one focused feature cut, then a GitHub Release.

## What works (v0.4.0)

**First-ship N-panel** — Import → Studio → Shoot stays the three-click path:

1. **Import** — Import Product file picker only
2. **Studio** — backdrop White / Grey / Black + **Build**
3. **Shoot** — Draft / Final, Still, Render

**Lights** (this cut) — native multi-light inventory plus Light Draw:

- Add / remove / set active BEHOLD studio lights
- Per-light energy
- Empty state when the studio has no lights yet
- Light Draw **Aim: Active | New** — Reflect / Direct / Orbit (LMB aim, scroll power/size/distance, solo)

Parked chrome (Materials, mixer, CAD backend, batch, turntable, EV/WB/tokens/bookmark, Light Draw hotkeys) is in **Advanced**, collapsed closed. Operators stay registered.

Backends:

- **Import Product** — pick `.obj`, `.fbx`, `.stl`, `.glb`/`.gltf`, `.3mf` (when Blender has an importer), or STEP/IGES/BREP → import → optional **Build Studio** + **Material Assist** from the filename
- **Studio** — select mesh(es) → Build Studio (cyclorama / solid / HDRI world, three-point or softbox, auto camera, optional shadow catcher) + light mixer
- **Lights** — named BEHOLD area lights; Build Studio seeds Key / Fill / Rim and marks Key active
- **Light Draw** — Reflect / Direct / Orbit modal aimed at the **active** light or a **new** light
- **Materials** — local PBR rack (metal, plastic, rubber, glass, paint)
- **BlenderKit** — soft-dependency bridge with **login from day one**, search, and apply hooks
- **Shoot** — EV / white balance / false color, Draft·Final·Product·Hero quality presets, output path tokens (`{angle}` `{camera}` `{quality}`), main-camera bookmark, still, batch angles (front / ¾ / top), turntable
- **CAD** — hybrid STEP/IGES/BREP: detect [STEPper NEXT](https://github.com/Peak-Design/STEPper_NEXT) → else BEHOLD OCP; Material Assist + Studio from Import

## Coming (not this release)

Camera management suite, auto-turntable polish, gobos / IES / scrims, bake-to-HDRI, light/shadow linking UI, Materials/BlenderKit redesign, live tessellation regenerate, defeaturing, full auto-dress grid. See [CHECKPOINT.md](CHECKPOINT.md).

## Import Product

Sidebar **BEHOLD → Import** (or File → Import → **BEHOLD Product**):

| Kind | Extensions | Backend |
| --- | --- | --- |
| Mesh | `.obj` `.fbx` `.stl` `.glb` `.gltf` | Native Blender 4.2+ / 5.2 LTS (`wm.obj_import`, `import_scene.fbx` / `gltf`, `wm.stl_import`) |
| 3MF | `.3mf` | Native or add-on importer when present (`wm.threemf_import` / `import_mesh.threemf`) |
| CAD | `.step` `.stp` `.iges` `.igs` `.brep` `.brp` | [STEPper NEXT](https://github.com/Peak-Design/STEPper_NEXT) if installed, else BEHOLD OCP |

Mesh and 3MF paths **never** require STEPper. CAD files need STEPper NEXT (preferred) or `cadquery-ocp` / `cadquery-ocp-novtk` in Blender's Python.

After import, BEHOLD can:

1. **Build Studio** around the new mesh(es) (toggle on the file-browser operator / Advanced).
2. **Material Assist** — guess a BlenderKit query from the filename, extension, or STEP material names (`housing_aluminum.step` → “brushed aluminum”).

### STEPper NEXT

STEPper NEXT is the recommended OpenCASCADE STEP/IGES/BREP importer for Blender. Install it from **[Peak-Design/STEPper_NEXT](https://github.com/Peak-Design/STEPper_NEXT)** (Releases zip → drag onto Blender, or Preferences → Get Extensions → Install from Disk). Current STEPper NEXT targets **Blender 5.1**. On 4.2–5.0, use BEHOLD's OCP fallback or an older STEPper build if you have one.

## Lights

Sidebar **BEHOLD → Lights**:

1. **Build Studio** (or **Add Light**) so the list is not empty.
2. Click the radio to set **Active**. Drag wattage on the row. **X** removes that light.
3. Light Draw **Aim = Active** moves the current light; **Aim = New** creates `BEHOLD_Draw_###` and aims it.
4. In the viewport: LMB drag aim · Wheel power · Shift+Wheel size · Ctrl+Wheel distance · `1`/`2`/`3` mode · `S` solo · Esc exit.

Hotkey legend stays under **Advanced**. Key / Fill / Rim mixer stays under **Advanced → Studio**.

## Download install zip (GitHub Actions)

1. **Every push / PR** — Actions → **Build Blender add-on zip** → download the `behold-addon` artifact (`behold-0.4.0.zip`).
2. **Versioned release** — push a tag `v0.4.0` (or later). The same workflow attaches the zip to the [GitHub Release](https://github.com/wckdboy/BEHOLD/releases) for one-click download.

```bash
git tag v0.4.0
git push origin v0.4.0
```

## Build install zip locally

```bash
make zip
# → dist/behold-0.4.0.zip
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

Enable the official BlenderKit / Blendkit extension, then use **Log In to BlenderKit** under **Advanced → Materials**. BEHOLD does not re-host BlenderKit assets; your BlenderKit account/plan applies.

## Develop

```bash
git clone https://github.com/wckdboy/BEHOLD.git
# Point Blender at /path/to/repo/behold via preferences or symlink into addons/
make test
make zip
```

## Remotes

- **Primary:** GitHub [`wckdboy/BEHOLD`](https://github.com/wckdboy/BEHOLD)
- **Mirror:** Origin [`wckdboy/BEHOLD`](https://cursor.com/codebase/wckdboy/BEHOLD)

```bash
git remote add origin https://github.com/wckdboy/BEHOLD.git
git remote add cursor https://origin.cursor.com/wckdboy/BEHOLD.git
```

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
