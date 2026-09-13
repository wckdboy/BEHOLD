# CHECKPOINT

Living status for BEHOLD. Update this file when a slice lands or a lane changes. Do not treat README as the source of truth for what is in-flight.

## Mission

KeyShot-simple OSS product renders in Blender.

## Now

| | |
| --- | --- |
| **Version on `main` (before this cut)** | 0.3.0 |
| **This branch / after merge** | **0.3.1** |
| **Blender min** | 4.2.0 (`bl_info`, `blender_manifest.toml`) |
| **Install zip** | `dist/behold-0.3.1.zip` (Actions artifact `behold-addon`) |

## Implemented

Honest inventory of what `main` already shipped (v0.3.0 backends). First-ship chrome hides most of this; the operators stay registered.

- **Import Product** — mesh + CAD hybrid. `.obj` `.fbx` `.stl` `.glb`/`.gltf` `.3mf` via native Blender importers; STEP/IGES/BREP via [STEPper NEXT](https://github.com/Peak-Design/STEPper_NEXT) else BEHOLD OCP. Optional Build Studio + Material Assist from the filename.
- **Studio** — cyclorama / solid / HDRI, three-point or softbox, auto camera, optional shadow catcher, light mixer (key / fill / rim / temperature).
- **Light Draw** — Reflect / Direct / Orbit modal (LMB aim, wheel power/size/distance, solo).
- **Materials / BlenderKit** — local PBR rack (metal, plastic, rubber, glass, paint) + BlenderKit login / search / apply bridge.
- **Shoot depth** — EV / white balance / false color; Draft · Product · Hero (and now Final) sample presets; `{angle}` `{camera}` `{quality}` path tokens; main-camera bookmark; still; batch angles; turntable.
- **CI zip** — GitHub Actions runs `make test` then builds the install zip; tags `v*` publish a GitHub Release.
- **Tests** — `make test` (`unittest` under `tests/`, no Blender required).

## First-ship chrome (Percival) — in this PR

N-panel = **three controls, no scroll**. Parked chrome lives in **Advanced** (`BEHOLD_PT_advanced`, `DEFAULT_CLOSED`) so the code stays reachable. Backend operators stay registered.

1. **Import** — only the **Import Product** file picker. CAD backend box, auto-studio, and Material Assist toggles are not on this panel.
2. **Studio** — backdrop **White / Grey / Black** + one **Build** button. No light mixer, no multi-light chrome.
3. **Shoot** — **Draft / Final**, **Still**, **Render** only. No batch, turntable, EV, WB, path tokens, or camera bookmark on this panel.

## Coming / In flight

- First-ship UI cut — **done here (0.3.1)**.
- **Multi-light studio + Blender 5.2 LTS (v0.4)** — draft [PR #5](https://github.com/wckdboy/BEHOLD/pull/5) (`cursor/behold-multi-light-5f2a`). Do **not** merge that branch into first-ship chrome. First-ship stays skinny even while those operators exist elsewhere.
- Live tessellation regenerate (OCP / STEPper deflection without re-picking the file).
- Defeaturing (fillet/chamfer/hole suppress before tessellate).
- Full auto-dress grid (filename + STEP material names → applied look, not just a BlenderKit query).
- Tag a GitHub Release (`v0.3.1` / later) so the Actions zip is a one-click download.
- Multi-light mixer chrome after first ship (Percival), wired to Galahad’s light list.

## Change log

### 2026-09-13

- Added this living CHECKPOINT (mission, `main` 0.3.0 inventory, first-ship chrome, coming / in-flight).
- Percival first-ship N-panel: Import / Studio / Shoot skinny; Materials, Light Draw, mixer, batch, turntable, CAD box parked in collapsed **Advanced**.
- Studio first-ship backdrop tones White / Grey / Black drive the sweep (and solid world) color. Build stays one click.
- Shoot first-ship quality **Draft / Final** (Final = 256 samples). Product / Hero remain on the property and in Advanced.
- Version **0.3.1**. PR #5 multi-light / 5.2 LTS listed as coming — not merged.

## Operating notes

- **Galahad** owns backends and the tessellator (import, OCP/STEPper, studio build, lights, shoot operators).
- **Percival** owns panel chrome (what the first-ship N-panel shows, what stays collapsed in Advanced).
- First-ship chrome must stay skinny even if extra operators remain registered.
- Prefer parking controls in `BEHOLD_PT_advanced` over deleting them.
