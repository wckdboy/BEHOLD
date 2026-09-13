# BEHOLD

Open-source Blender add-on for KeyShot-simple product rendering — free.

## What works (v0.1)

- **Studio** — select mesh(es) → Build Studio (cyclorama / solid / HDRI world, three-point or softbox, auto camera, optional shadow catcher) + light mixer
- **Light Draw** — Reflect / Direct / Orbit modal (LMB aim, scroll power/size/distance, solo)
- **Materials** — local PBR rack (metal, plastic, rubber, glass, paint)
- **BlenderKit** — soft-dependency bridge with **login from day one**, search, and apply hooks
- **Shoot** — EV / false-color helpers, still render, turntable setup + render

Not in this slice: deep Shoot tools, CAD/STEP hybrid import.

## Build install zip

```bash
make zip
# → dist/behold-0.1.0.zip
```

Or: `bash scripts/build_addon.sh`

## Install (Blender 4.2+)

1. Build the zip (`make zip`) or download a release zip.
2. Blender → Edit → Preferences → Add-ons → Install… → select `dist/behold-*.zip`
3. Enable **BEHOLD**, then open the 3D Viewport sidebar (`N`) → **BEHOLD** tab.

Alternate (dev): copy or symlink `behold/` into your Blender `scripts/addons/` directory.

### BlenderKit

Enable the official BlenderKit / Blendkit extension, then use **Log In to BlenderKit** in the Materials panel. BEHOLD does not re-host BlenderKit assets; your BlenderKit account/plan applies.

## Develop

```bash
git clone <repo-url>
# Point Blender at /path/to/repo/behold via preferences or symlink into addons/
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
