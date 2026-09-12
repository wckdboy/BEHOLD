# BEHOLD

Open-source Blender add-on for KeyShot-simple product rendering — free.

## What works (v0.1)

- **Studio** — select mesh(es) → Build Studio (cyclorama / solid / HDRI world, three-point or softbox, auto camera, optional shadow catcher) + light mixer
- **Materials** — local PBR rack (metal, plastic, rubber, glass, paint)
- **BlenderKit** — soft-dependency bridge with **login from day one**, search, and apply hooks
- **Shoot** — EV / false-color helpers, still render, turntable setup + render

Not in this slice: Light Draw modal, deep Shoot tools, CAD/STEP import.

## Install (Blender 4.2+)

1. Download or clone this repo.
2. Zip the `behold/` folder **or** install as a legacy add-on by linking the folder:
   - Blender → Edit → Preferences → Add-ons → Install… → select a zip of `behold/`
   - Or copy `behold/` into your Blender `scripts/addons/` directory and enable **BEHOLD**
3. Open the 3D Viewport sidebar (`N`) → **BEHOLD** tab.

### BlenderKit

Enable the official BlenderKit / Blendkit extension, then use **Log In to BlenderKit** in the Materials panel. BEHOLD does not re-host BlenderKit assets; your BlenderKit account/plan applies.

## Develop

```bash
git clone <repo-url>
# Point Blender at /path/to/repo/behold via preferences or symlink into addons/
```

## License

GPL-3.0-or-later — see [LICENSE](LICENSE).
