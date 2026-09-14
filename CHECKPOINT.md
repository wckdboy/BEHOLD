# CHECKPOINT

Living status for BEHOLD by AMIRITE.studio. Update this file when a slice lands or a lane changes. Do not treat README as the source of truth for what is in-flight.

## Mission

KeyShot-simple OSS product renders in Blender. Best Blender plugin for product rendering and production workflows under **BEHOLD by AMIRITE.studio**.

Cadence: one focused feature cut, then a GitHub Release. Do not kitchen-sink.

## Now

| | |
| --- | --- |
| **Version on `main` (before this cut)** | 0.11.0 |
| **This branch / after merge** | **0.12.0** |
| **Primary Blender target** | **5.2 LTS and newer** |
| **Install min** | 4.2.0 (`bl_info`, `blender_manifest.toml`) — cheap 4.2+ load; do not block 5.2 work on it |
| **Install zip** | `dist/behold-0.12.0.zip` (Actions artifact `behold-addon`) |

## Implemented

- **Workflow order (0.12.0)** — N-panel child order is **Import → Studio → Lights → Materials → Cameras → Shoot → Advanced** (`bl_order` + `CLASSES`). Shoot is last so dressing lights/materials/cameras does not require scrolling past Shoot and back. Flow strip stays Import → Studio → Dress → Shoot; Dress Next runs **Material Assist**.
- **Clear errors (0.12.0)** — primary operators share empty-state copy: short sentence + next step (e.g. “No mesh selected — select the product or Import Product”). Missing-prerequisite reports use `WARNING`; hard failures stay `ERROR`. Constants in `behold/ui/messages.py`. Update check/install copy stays in `behold/updates/core.py` (`describe_failure`).
- **Cyclorama auto-fit (0.11.0)** — Build Studio sizes the sweep from the product world AABB: floor = max(width, depth, XY diagonal) × margin (default 2.0×, also ≥ 0.75 × height); wall = height × 1.75 headroom (also ≥ 0.4 × floor). Lights / catcher use `rig_size` so they stay outside the floor. Rebuild drops leftover `BEHOLD_Cyclorama` / catcher meshes. Optional **Studio Margin** in Advanced; first-ship stays White / Grey / Black + Build.
- **Easy update (0.10.0)** — public GitHub Releases check for `wckdboy/BEHOLD` (no token). Preferences: **Check for updates**, last-checked status, **Update available: x.y.z** with **Install** / **Open release**. Session-dismissible notice on the main BEHOLD panel. Check/install failures are explicit (what failed + check network / Open release). Auto-check default **on**, at most once per day on a background thread + timer (cancel-safe; toggle to disable). Install downloads `behold-*.zip` to a temp path, then Blender 5.2 `extensions.package_install_files` (Install from Disk, `user_default`, overwrite, enable) with `preferences.addon_install` fallback. Always asks to **restart Blender**. Tests in `tests/test_updates.py` (fixtures, no live network).
- **Studio chrome (0.9.0)** — branded N-panel hero (**BEHOLD** / **by AMIRITE.studio**), section header icons, box cards, one-CTA empty states. **Import → Studio → Dress → Shoot** strip checks off from scene state (product / studio kit / local look / camera). Next CTA stays on the three-click path.
- **Pie + header (0.9.0)** — `BEHOLD_MT_pie` via `wm.call_menu_pie` (**Shift+Alt+B** in the 3D View): Import, Build Studio, Light Draw, Still, Turntable Setup. Viewport header icon cluster (pie / Import / Build / Still), hide from add-on preferences.
- **Preferences (0.9.0 / 0.10.0)** — branding, Docs / Releases links, flow-strip and header toggles, this-scene auto-studio / Assist / quality. **0.10.0** adds Check for updates / last-checked / Install from the release zip.
- **Import Product** — mesh + CAD. `.obj` `.fbx` `.stl` `.glb`/`.gltf` `.3mf` via native Blender importers (5.2 kwargs hardened). STEP/IGES/BREP via **STEPper NEXT first-class** (`import_scene.occ_import_step` with `filepath` + `override_file`); OCP only if STEPper is missing and bindings actually import. Missing CAD backend fails loudly with the STEPper Releases URL. Optional Build Studio + Material Assist from the filename. Shared `product_import_dispatch` / `run_product_import`.
- **Import panel (0.7.0)** — **Import Product** picker plus one CAD backend line: **STEPper NEXT ready** / **OCP fallback** / **Install STEPper NEXT** (opens Releases). Auto-studio, Material Assist, and the full CAD box stay in Advanced. STEPper's own import dialog is not embedded.
- **Studio** — cyclorama / solid / HDRI, three-point or softbox, auto camera, optional shadow catcher, White / Grey / Black first-ship backdrop tones, light mixer (key / fill / rim / temperature). Cyclorama auto-fits product bounds on Build (0.11.0).
- **Lights (0.4.0)** — add / remove / set active BEHOLD studio lights; per-light energy; empty-state UX; Build Studio seeds the rig and marks Key active.
- **Light Draw** — Reflect / Direct / Orbit modal (LMB aim, wheel power/size/distance, solo). **Aim Active vs New** against the multi-light inventory.
- **Cameras (0.5.0)** — add / remove / set active / frame / clear BEHOLD product cameras; 85 mm full-frame defaults; frames selected mesh or product bounds (studio sweep excluded); active camera is the Shoot still + main-camera bookmark. Build Studio still seeds `BEHOLD_Camera`.
- **Turntable (0.6.0)** — compact Shoot row: seconds + Setup + Play. Default **6 s / 144 frames at 24 fps**, 360° linear loop around the product using the active BEHOLD / scene camera. Empty-state copy points at Build Studio / Add Camera / Import. Advanced: Linear vs Ease, Bake (camera keys, drop pivot), Clear (pivot / baked loc-rot only), Render.
- **STEP vertical smoke (0.7.0)** — CC0 `tests/fixtures/unit_cube.step` + CI dispatch tests **done**. OCP tessellation runs when bindings exist, otherwise unittest skip. Blender Import → Build → Draft still script **ready** (`scripts/smoke_step_vertical.py` / `make smoke-step`) when OCP or STEPper is present. CI does not produce a still (no Blender / no CAD backend there). STEPper detect helpers / operator id constants / Import panel status strings are unit-tested without bpy.
- **Materials (0.8.0)** — first-class N-panel: one-click Metal / Plastic / Rubber / Glass / Paint on selected product meshes; empty state if nothing is selected. Principled BSDF product defaults (4.2 `Transmission`/`Clearcoat` and 5.2 `Transmission Weight`/`Coat Weight`). Studio sweep / catcher meshes are skipped.
- **Material Assist (0.8.0)** — filename / STEP hints map onto the local rack and **apply** that look. BlenderKit is optional: search/apply/login stay in Advanced; Assist searches only when signed in. No account required for the local path. Import post-step uses the same runner.
- **BlenderKit** — soft-dependency bridge with login / search / apply hooks (Advanced). Not required to dress a mesh.
- **Shoot depth** — EV / white balance / false color; Draft · Product · Hero (and Final) sample presets; `{angle}` `{camera}` `{quality}` path tokens; main-camera bookmark; still; batch angles; turntable.
- **CI zip** — GitHub Actions runs `make test` then builds the install zip; tags `v*` publish a GitHub Release.
- **Tests** — `make test` (`unittest` under `tests/`, no Blender required). `tests/test_studio_fit.py` covers cyclorama margin math (tiny cube, long bar, tall tower, flat sheet) without bpy. `tests/test_updates.py` covers semver compare, GitHub JSON fixtures, and operator/prefs wiring (no live network). `tests/test_materials.py` covers rack defaults, socket aliases, Assist mapping, and wiring. `tests/test_messages.py` covers shared error / empty-state copy.

## First-ship chrome (Percival)

N-panel keeps the three-click path skinny, but **physical order matches the work**. Lights, Materials, and Cameras sit between Studio and Shoot so artists do not scroll past Shoot to dress, then back. Turntable stays a compact row on Shoot — not a fourth first-class section. v0.9.0 is Percival chrome (hero, flow strip, cards, pie/header); v0.10.0 adds the update notice; v0.11.0 is cyclorama auto-fit (order already shoot-path); v0.12.0 is Percival `bl_order` + error copy — not a new backend lane.

1. **Import** — **Import Product** file picker + one CAD backend line (**STEPper NEXT ready** / **OCP fallback** / **Install STEPper NEXT**). Auto-studio, Material Assist toggle, and the full CAD box stay in Advanced. Do not embed STEPper's import dialog.
2. **Studio** — backdrop **White / Grey / Black** + one **Build** button. No light mixer. Cyclorama auto-fits; **Studio Margin** stays in Advanced.
3. **Lights** — inventory + Light Draw Active / New. Not a Light Wrangler clone; native Blender chrome.
4. **Materials (0.8.0)** — local rack + Assist. Empty state if no product mesh is selected. Not a BlenderKit browser. Flow-strip **Dress** Next = Assist.
5. **Cameras** — inventory + Add / Frame / Clear. Not Blender's Properties camera dump; native BEHOLD chrome.
6. **Shoot** — **Draft / Final**, **Still**, **Render**, compact **Turntable** (seconds + Setup + Play). Last first-class section. No batch, EV, WB, path tokens, camera bookmark, bake, or ease on this panel.
7. **Main shell (0.9.0)** — `BEHOLD_PT_main` draws the hero + flow strip. Child panels keep `draw_header` icons and `bl_order`. **0.10.0** adds a dismissible update notice on the main panel when a newer stable zip is cached — not a new first-class section.
8. **Advanced** (`BEHOLD_PT_advanced`, `DEFAULT_CLOSED`) — mixer, **Studio Margin**, CAD box, BlenderKit login/search/apply, Light Draw hotkeys, batch, turntable spin / bake / clear / render, Bookmark / Use Main.

Backend operators stay registered. Pie / header / preferences do not replace the N-panel path.

## Coming / In flight

Not this PR:

- Gobos, IES library streaming, scrims.
- Bake-to-HDRI.
- Light / shadow linking UI.
- False-color variants beyond what Shoot already has.
- Full BlenderKit browser / apply-from-search-results (login/search/apply hooks stay; no in-panel library).
- Live tessellation regenerate (OCP / STEPper deflection without re-picking the file).
- Defeaturing (fillet/chamfer/hole suppress before tessellate).
- Per-body auto-dress (each STEP color/name → its own look; Assist still applies one look to the selection).

Draft [PR #7](https://github.com/wckdboy/BEHOLD/pull/7) (`galahad/behold-step-vertical-smoke`) sketched STEP vertical on pre-0.4 chrome (v0.3.2). Leave PR #7 as historical draft — do not merge it as-is. [PR #11](https://github.com/wckdboy/BEHOLD/pull/11) is the 0.7.0 **smoke-only** fixture/tests/script; **this cut supersedes #11** as the real 0.7.0 (STEPper NEXT first-class + mesh reliability + first-ship Import UX).

## Change log

### 2026-09-14

- v**0.12.0** Workflow order + clear errors: N-panel **Import → Studio → Lights → Materials → Cameras → Shoot → Advanced** (Shoot last, `bl_order`). Flow-strip Dress Next = Material Assist. Shared empty-state / operator copy in `behold/ui/messages.py` (sentence + next step; `WARNING` vs `ERROR`). Tests in `tests/test_messages.py`. Install zip `behold-0.12.0.zip`.
- v**0.11.0** Cyclorama auto-fit: Build Studio sizes floor / wall / lights from the product world AABB (XY diagonal × margin, wall clears height with headroom). Rebuild replaces leftover sweeps. Optional Studio Margin in Advanced (default 2.0×). First-ship stays White / Grey / Black + Build. N-panel order Import → Studio → Lights → Materials → Cameras → Shoot → Advanced (flow strip Import → Studio → Dress → Shoot). Tests in `tests/test_studio_fit.py`. Install zip `behold-0.11.0.zip`.
- v**0.10.0** Easy update: GitHub Releases check (public API, no token), preferences Check for updates + last-checked + Install / Open release, session-dismissible N-panel notice, optional daily auto-check (default on). Installs `behold-*.zip` via 5.2 Install from Disk then asks to restart Blender. Tests in `tests/test_updates.py`. Install zip `behold-0.10.0.zip`.
- v**0.9.0** Studio chrome / enhanced UX: branded N-panel hero, Import → Studio → Dress → Shoot strip, section icons, box cards, one-CTA empty states. Pie menu `BEHOLD_MT_pie` (**Shift+Alt+B**) + 3D View header shortcuts. Add-on preferences branding / docs / chrome toggles / this-scene quality and auto-studio. Tests in `tests/test_ux_chrome.py`. Install zip `behold-0.9.0.zip`. Native `bpy.types.Panel` / `UILayout` / pie / header only — no HTML overlay.
- v**0.8.0** Materials that apply: first-class Materials N-panel (Metal / Plastic / Rubber / Glass / Paint + Assist). Empty state if nothing is selected. Assist / Import apply a matching local Principled look without BlenderKit; search/apply/login stay in Advanced. Socket aliases cover Blender 5.2 `Transmission Weight` / `Coat Weight` and 4.2 `Transmission` / `Clearcoat`. Tests in `tests/test_materials.py`. Install zip `behold-0.8.0.zip`.
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

- **Galahad** owns backends and the tessellator (import, OCP/STEPper, studio build, lights, cameras, shoot operators, turntable rig, STEP vertical smoke, STEPper NEXT first-class import, local material apply, GitHub update check / zip install).
- **Percival** owns panel chrome (what the N-panel shows, what stays collapsed in Advanced).
- First-ship Import / Studio / Shoot must stay skinny even if extra operators remain registered. Import may show one CAD backend line; auto-studio / Material Assist toggle / full CAD box stay in Advanced. Turntable on Shoot is one compact row; bake / ease / render stay in Advanced.
- Prefer parking controls in `BEHOLD_PT_advanced` over deleting them.
- Lights, Materials, and Cameras sit between Studio and Shoot. Park BlenderKit chrome in Advanced — do not dump a library browser on Materials.
- Percival 0.9.0 chrome stays inside Blender's UI toolkit (panels, pie, header, preferences). Do not add HTML/OpenGL overlay skins.
- Real STEP Import → Build → Render: `blender --background --python scripts/smoke_step_vertical.py` (needs OCP or STEPper).
