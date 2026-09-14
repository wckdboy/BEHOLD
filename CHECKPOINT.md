# CHECKPOINT

Living status for BEHOLD by AMIRITE.studio. Update this file when a slice lands or a lane changes. Do not treat README as the source of truth for what is in-flight.

## Mission

KeyShot-simple OSS product renders in Blender. Best Blender plugin for product rendering and production workflows under **BEHOLD by AMIRITE.studio**.

Cadence: one focused feature cut, then a GitHub Release. Do not kitchen-sink.

## Now

| | |
| --- | --- |
| **Version on `main` (before this cut)** | 0.6.0 |
| **This branch / after merge** | **0.7.0** |
| **Primary Blender target** | **5.2 LTS and newer** |
| **Install min** | 4.2.0 (`bl_info`, `blender_manifest.toml`) — cheap 4.2+ load; do not block 5.2 work on it |
| **Install zip** | `dist/behold-0.7.0.zip` (Actions artifact `behold-addon`) |

## Implemented

Honest inventory of what this cut ships (plus what `main` already had).

- **Import Product** — mesh + CAD. `.obj` `.fbx` `.stl` `.glb`/`.gltf` `.3mf` via native Blender importers (5.2 kwargs hardened). STEP/IGES/BREP via **STEPper NEXT first-class** (`import_scene.occ_import_step` with `filepath` + `override_file`); OCP only if STEPper is missing and bindings actually import. Missing CAD backend fails loudly with the STEPper Releases URL. Optional Build Studio + Material Assist from the filename. Shared `product_import_dispatch` / `run_product_import`.
- **Import panel (0.7.0)** — **Import Product** picker plus one CAD backend line: **STEPper NEXT ready** / **OCP fallback** / **Install STEPper NEXT** (opens Releases). Auto-studio, Material Assist, and the full CAD box stay in Advanced. STEPper's own import dialog is not embedded.
- **Studio** — cyclorama / solid / HDRI, three-point or softbox, auto camera, optional shadow catcher, White / Grey / Black first-ship backdrop tones, light mixer (key / fill / rim / temperature).
- **Lights (0.4.0)** — add / remove / set active BEHOLD studio lights; per-light energy; empty-state UX; Build Studio seeds the rig and marks Key active.
- **Light Draw** — Reflect / Direct / Orbit modal (LMB aim, wheel power/size/distance, solo). **Aim Active vs New** against the multi-light inventory.
- **Cameras (0.5.0)** — add / remove / set active / frame / clear BEHOLD product cameras; 85 mm full-frame defaults; frames selected mesh or product bounds (studio sweep excluded); active camera is the Shoot still + main-camera bookmark. Build Studio still seeds `BEHOLD_Camera`.
- **Turntable (0.6.0)** — compact Shoot row: seconds + Setup + Play. Default **6 s / 144 frames at 24 fps**, 360° linear loop around the product using the active BEHOLD / scene camera. Empty-state copy points at Build Studio / Add Camera / Import. Advanced: Linear vs Ease, Bake (camera keys, drop pivot), Clear (pivot / baked loc-rot only), Render.
- **STEP vertical smoke (0.7.0)** — CC0 `tests/fixtures/unit_cube.step` + CI dispatch tests **done**. OCP tessellation runs when bindings exist, otherwise unittest skip. Blender Import → Build → Draft still script **ready** (`scripts/smoke_step_vertical.py` / `make smoke-step`) when OCP or STEPper is present. CI does not produce a still (no Blender / no CAD backend there). STEPper detect helpers / operator id constants / Import panel status strings are unit-tested without bpy.
- **Materials / BlenderKit** — local PBR rack (metal, plastic, rubber, glass, paint) + BlenderKit login / search / apply bridge.
- **Shoot depth** — EV / white balance / false color; Draft · Product · Hero (and Final) sample presets; `{angle}` `{camera}` `{quality}` path tokens; main-camera bookmark; still; batch angles; turntable.
- **CI zip** — GitHub Actions runs `make test` then builds the install zip; tags `v*` publish a GitHub Release.
- **Tests** — `make test` (`unittest` under `tests/`, no Blender required).

## First-ship chrome (Percival)

N-panel keeps the three-click path skinny. Lights and Cameras are dedicated sections after Shoot so lighting and cameras are findable without stuffing either into Studio. Turntable is a compact row on Shoot — not a fourth first-class section.

1. **Import** — **Import Product** file picker + one CAD backend line (**STEPper NEXT ready** / **OCP fallback** / **Install STEPper NEXT**). Auto-studio, Material Assist, and the full CAD box stay in Advanced. Do not embed STEPper's import dialog.
2. **Studio** — backdrop **White / Grey / Black** + one **Build** button. No light mixer.
3. **Shoot** — **Draft / Final**, **Still**, **Render**, compact **Turntable** (seconds + Setup + Play). No batch, EV, WB, path tokens, camera bookmark, bake, or ease on this panel.
4. **Lights** — inventory + Light Draw Active / New. Not a Light Wrangler clone; native Blender chrome.
5. **Cameras** — inventory + Add / Frame / Clear. Not Blender's Properties camera dump; native BEHOLD chrome.
6. **Advanced** (`BEHOLD_PT_advanced`, `DEFAULT_CLOSED`) — mixer, CAD box, materials, Light Draw hotkeys, batch, turntable spin / bake / clear / render, Bookmark / Use Main.

Backend operators stay registered.

## Coming / In flight

Not this PR:

- Gobos, IES library streaming, scrims.
- Bake-to-HDRI.
- Light / shadow linking UI.
- False-color variants beyond what Shoot already has.
- Materials / BlenderKit redesign.
- Live tessellation regenerate (OCP / STEPper deflection without re-picking the file).
- Defeaturing (fillet/chamfer/hole suppress before tessellate).
- Full auto-dress grid (filename + STEP material names → applied look, not just a BlenderKit query).

Draft [PR #7](https://github.com/wckdboy/BEHOLD/pull/7) (`galahad/behold-step-vertical-smoke`) sketched STEP vertical on pre-0.4 chrome (v0.3.2). Leave PR #7 as historical draft — do not merge it as-is. [PR #11](https://github.com/wckdboy/BEHOLD/pull/11) is the 0.7.0 **smoke-only** fixture/tests/script; **this cut supersedes #11** as the real 0.7.0 (STEPper NEXT first-class + mesh reliability + first-ship Import UX).

## Change log

### 2026-09-14

- v**0.7.0** Import that works: first-class [STEPper NEXT](https://github.com/Peak-Design/STEPper_NEXT) (`bl_ext.*.stepper_next` detect, enable-if-disabled, `import_scene.occ_import_step` with `filepath` + `override_file`). Import panel shows **STEPper NEXT ready** / **OCP fallback** / **Install STEPper NEXT**. Mesh native import reports which operator failed and why (Blender 5.2 kwargs). Loud fail + Releases URL when no CAD backend. Ports PR #11's CC0 `tests/fixtures/unit_cube.step`, `product_import_dispatch` / `run_product_import`, `ocp_core`, and `make smoke-step` onto current `main`. First-ship Import is picker + CAD status line (not STEPper's dialog). Does not merge PR #7.
- v**0.6.0** Auto turntable: compact Shoot controls, 6 s / 24 fps default (144 frames), loop-friendly linear 360° around the product / active camera. Play / bake / clear without touching other animation. Ease parked in Advanced.
- v**0.5.0** Cameras: create, manage, and frame product cameras from the N-panel. Shoot still uses the active / bookmarked camera.
- Focused **Cameras** N-panel next to Lights; Import / Studio / Shoot first-ship path unchanged (0.5.0); 0.6.0 adds the compact Turntable row on Shoot only.
- Product defaults: 85 mm, 36×24 mm full-frame sensor, horizontal fit, clip range from product size. Frame selected mesh, else tagged product, else non-studio meshes.
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

- **Galahad** owns backends and the tessellator (import, OCP/STEPper, studio build, lights, cameras, shoot operators, turntable rig, STEP vertical smoke, STEPper NEXT first-class import).
- **Percival** owns panel chrome (what the N-panel shows, what stays collapsed in Advanced).
- First-ship Import / Studio / Shoot must stay skinny even if extra operators remain registered. Import may show one CAD backend line; auto-studio / Material Assist / full CAD box stay in Advanced. Turntable on Shoot is one compact row; bake / ease / render stay in Advanced.
- Prefer parking controls in `BEHOLD_PT_advanced` over deleting them.
- Lights and Cameras are the extra first-class sections; do not reopen Materials here.
- Real STEP Import → Build → Render: `blender --background --python scripts/smoke_step_vertical.py` (needs OCP or STEPper).
