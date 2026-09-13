# BEHOLD

Open-source Blender add-on for KeyShot-simple product rendering — free.

## What works (v0.1)

- **Studio** — select mesh(es) → Build Studio (cyclorama / solid / HDRI world, three-point or softbox, auto camera, optional shadow catcher) + light mixer
- **Light Draw** — Reflect / Direct / Orbit modal (LMB aim, scroll power/size/distance, solo)
- **Materials** — local PBR rack (metal, plastic, rubber, glass, paint)
- **BlenderKit** — soft-dependency bridge with **login from day one**, search, and apply hooks
- **Shoot** — EV / white balance / false color, still, batch angles (front / ¾ / top), turntable

Not in this slice: full Photographer-depth Shoot, CAD/STEP hybrid import.

## Download install zip (GitHub Actions)

Once this repo is on GitHub (`wckdboy/BEHOLD`):

1. **Every push / PR** — Actions → **Build Blender add-on zip** → download the `behold-addon` artifact (`behold-0.1.0.zip`).
2. **Versioned release** — push a tag `v0.1.0` (or later). The same workflow attaches the zip to the [GitHub Release](https://github.com/wckdboy/BEHOLD/releases) for one-click download.

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Build install zip locally

```bash
make zip
# → dist/behold-0.1.0.zip
```

Or: `bash scripts/build_addon.sh`

## Install (Blender 4.2+)

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
