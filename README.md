# BEHOLD

Open-source Blender add-on for KeyShot-simple product rendering — free.

## What works (v0.4)

- **Import Product** — pick `.obj`, `.fbx`, `.stl`, `.glb`/`.gltf`, `.3mf` (when Blender has an importer), or STEP/IGES/BREP → import → optional **Build Studio** + **Material Assist** from the filename
- **Studio** — select mesh(es) → Build Studio (cyclorama / solid / HDRI world, three-point or softbox, auto camera, optional shadow catcher) + light mixer
- **Lights** — add multiple BEHOLD lights and set each light’s intensity in the Studio panel
- **Light Draw** — Reflect / Direct / Orbit modal (LMB aim, scroll power/size/distance, solo)
- **Materials** — local PBR rack (metal, plastic, rubber, glass, paint)
- **BlenderKit** — soft-dependency bridge with **login from day one**, search, and apply hooks
- **Shoot** — EV / white balance / false color, Draft·Product·Hero quality presets, output path tokens (`{angle}` `{camera}` `{quality}`), main-camera bookmark, still, batch angles (front / ¾ / top), turntable
- **CAD** — hybrid STEP/IGES/BREP: detect [STEPper NEXT](https://github.com/Peak-Design/STEPper_NEXT) → else BEHOLD OCP; Material Assist + Studio from Import

Deferred: live tessellation regenerate, defeaturing, full auto-dress grid.

## Import Product

Sidebar **BEHOLD → Import** (or File → Import → **BEHOLD Product**):

| Kind | Extensions | Backend |
| --- | --- | --- |
| Mesh | `.obj` `.fbx` `.stl` `.glb` `.gltf` | Native Blender 5.2 LTS (`wm.obj_import`, `import_scene.fbx` / `gltf`, `wm.stl_import`) |
| 3MF | `.3mf` | Native or add-on importer when present (`wm.threemf_import` / `import_mesh.threemf`) |
| CAD | `.step` `.stp` `.iges` `.igs` `.brep` `.brp` | [STEPper NEXT](https://github.com/Peak-Design/STEPper_NEXT) if installed, else BEHOLD OCP |

Mesh and 3MF paths **never** require STEPper. CAD files need STEPper NEXT (preferred) or `cadquery-ocp` / `cadquery-ocp-novtk` in Blender's Python.

After import, BEHOLD can:

1. **Build Studio** around the new mesh(es) (toggle on the operator / Import panel).
2. **Material Assist** — guess a BlenderKit query from the filename, extension, or STEP material names (`housing_aluminum.step` → “brushed aluminum”).

### STEPper NEXT

STEPper NEXT is the recommended OpenCASCADE STEP/IGES/BREP importer for Blender. Install it from **[Peak-Design/STEPper_NEXT](https://github.com/Peak-Design/STEPper_NEXT)** (Releases zip → drag onto Blender, or Preferences → Get Extensions → Install from Disk). Current STEPper NEXT targets **Blender 5.1**. On 4.2–5.0, use BEHOLD's OCP fallback or an older STEPper build if you have one.

## Download install zip (GitHub Actions)

Once this repo is on GitHub (`wckdboy/BEHOLD`):

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

## Install (Blender 5.2 LTS)

1. Get `behold-*.zip` (Actions artifact, Release asset, or `make zip`).
2. Blender → Edit → Preferences → Add-ons → Install… → select the zip  
   (or Get Extensions → Install from Disk).
3. Enable **BEHOLD**, then open the 3D Viewport sidebar (`N`) → **BEHOLD** tab.

Alternate (dev): copy or symlink `behold/` into your Blender `scripts/addons/` directory.

### BlenderKit

Enable the official BlenderKit / Blendkit extension, then use **Log In to BlenderKit** in the Materials panel. BEHOLD does not re-host BlenderKit assets; your BlenderKit account/plan applies.

## Develop

```bash
git clone https://github.com/wckdboy/BEHOLD.git
# Point Blender at /path/to/repo/behold via preferences or symlink into addons/
make test
make zip
```

## Remotes

- **Primary:** GitHub [`wckdboy/BEHOLD`](https://github.com/wckdboy/BEHOLD) (create if missing — CI runs here)
- **Mirror:** Origin [`wckdboy/BEHOLD`](https://cursor.com/codebase/wckdboy/BEHOLD)

```bash
git remote add origin https://github.com/wckdboy/BEHOLD.git
git remote add cursor https://origin.cursor.com/wckdboy/BEHOLD.git
```

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
