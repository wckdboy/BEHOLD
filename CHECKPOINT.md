# CHECKPOINT

Living status for BEHOLD by AMIRITE.studio. Update this file when a slice lands or a lane changes. Do not treat README as the source of truth for what is in-flight.

## Mission

KeyShot-simple OSS product renders in Blender. Best Blender plugin for product rendering and production workflows under **BEHOLD by AMIRITE.studio**.

Cadence: one focused feature cut, then a GitHub Release. Do not kitchen-sink.

## Now

| | |
| --- | --- |
| **Version on `main` (before this cut)** | 0.3.1 |
| **This branch / after merge** | **0.4.0** |
| **Primary Blender target** | **5.2 LTS and newer** |
| **Install min** | 4.2.0 (`bl_info`, `blender_manifest.toml`) — cheap 4.2+ load; do not block 5.2 work on it |
| **Install zip** | `dist/behold-0.4.0.zip` (Actions artifact `behold-addon`) |

## Implemented

Honest inventory of what this cut ships (plus what `main` already had).

- **Import Product** — mesh + CAD hybrid. `.obj` `.fbx` `.stl` `.glb`/`.gltf` `.3mf` via native Blender importers; STEP/IGES/BREP via [STEPper NEXT](https://github.com/Peak-Design/STEPper_NEXT) else BEHOLD OCP. Optional Build Studio + Material Assist from the filename.
- **Studio** — cyclorama / solid / HDRI, three-point or softbox, auto camera, optional shadow catcher, White / Grey / Black first-ship backdrop tones, light mixer (key / fill / rim / temperature).
- **Lights (0.4.0)** — add / remove / set active BEHOLD studio lights; per-light energy; empty-state UX; Build Studio seeds the rig and marks Key active.
- **Light Draw** — Reflect / Direct / Orbit modal (LMB aim, wheel power/size/distance, solo). **Aim Active vs New** against the multi-light inventory.
- **Materials / BlenderKit** — local PBR rack (metal, plastic, rubber, glass, paint) + BlenderKit login / search / apply bridge.
- **Shoot depth** — EV / white balance / false color; Draft · Product · Hero (and Final) sample presets; `{angle}` `{camera}` `{quality}` path tokens; main-camera bookmark; still; batch angles; turntable.
- **CI zip** — GitHub Actions runs `make test` then builds the install zip; tags `v*` publish a GitHub Release.
- **Tests** — `make test` (`unittest` under `tests/`, no Blender required).

## First-ship chrome (Percival)

N-panel keeps the three-click path skinny. Lights is a dedicated section after Shoot so lighting is findable without stuffing the mixer into Studio.

1. **Import** — only the **Import Product** file picker. CAD backend box, auto-studio, and Material Assist toggles are not on this panel.
2. **Studio** — backdrop **White / Grey / Black** + one **Build** button. No light mixer.
3. **Shoot** — **Draft / Final**, **Still**, **Render** only. No batch, turntable, EV, WB, path tokens, or camera bookmark on this panel.
4. **Lights** — inventory + Light Draw Active / New. Not a Light Wrangler clone; native Blender chrome.
5. **Advanced** (`BEHOLD_PT_advanced`, `DEFAULT_CLOSED`) — mixer, CAD box, materials, Light Draw hotkeys, batch, turntable.

Backend operators stay registered.

## Coming / In flight

Not this PR:

- Camera creation / management suite.
- Auto-turntable chrome redesign / polish.
- Gobos, IES library streaming, scrims.
- Bake-to-HDRI.
- Light / shadow linking UI.
- False-color variants beyond what Shoot already has.
- Materials / BlenderKit redesign.
- Live tessellation regenerate (OCP / STEPper deflection without re-picking the file).
- Defeaturing (fillet/chamfer/hole suppress before tessellate).
- Full auto-dress grid (filename + STEP material names → applied look, not just a BlenderKit query).
- STEP vertical smoke — open [PR #7](https://github.com/wckdboy/BEHOLD/pull/7); separate lane, do not merge into 0.4.0.

Draft [PR #5](https://github.com/wckdboy/BEHOLD/pull/5) (`cursor/behold-multi-light-5f2a`) sketched this multi-light + Active/New direction on pre-first-ship chrome. **0.4.0 continues that sketch** on current `main` (first-ship N-panel + backdrop tones). Leave PR #5 as historical draft.

## Change log

### 2026-09-14

- v**0.4.0** Light Wrangler foundation: multi-light inventory (add / remove / set active, per-light energy, empty state) + Light Draw Aim Active / New.
- Focused **Lights** N-panel; Import / Studio / Shoot first-ship path unchanged.
- Primary Blender target documented as **5.2 LTS+**; install min stays 4.2.0.
- Continues PR #5’s helpers (`studio/lights.py`, `light_draw/draw_core.py`) without taking its pre-0.3.1 panel dump or dropping White/Grey/Black studio tones.

### 2026-09-13

- Added this living CHECKPOINT (mission, `main` 0.3.0 inventory, first-ship chrome, coming / in-flight).
- Percival first-ship N-panel: Import / Studio / Shoot skinny; Materials, Light Draw, mixer, batch, turntable, CAD box parked in collapsed **Advanced**.
- Studio first-ship backdrop tones White / Grey / Black drive the sweep (and solid world) color. Build stays one click.
- Shoot first-ship quality **Draft / Final** (Final = 256 samples). Product / Hero remain on the property and in Advanced.
- Version **0.3.1**. PR #5 multi-light / 5.2 LTS listed as coming — not merged.

## Operating notes

- **Galahad** owns backends and the tessellator (import, OCP/STEPper, studio build, lights, shoot operators).
- **Percival** owns panel chrome (what the N-panel shows, what stays collapsed in Advanced).
- First-ship Import / Studio / Shoot must stay skinny even if extra operators remain registered.
- Prefer parking controls in `BEHOLD_PT_advanced` over deleting them.
- Lights is the one extra first-class section for the lighting cut; do not reopen Materials or Shoot chrome here.
