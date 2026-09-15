# ROADMAP

BEHOLD is not a KeyShot clone and not Light Wrangler parity theater.
**v1.0.0 is first stable** — the suite 0.4.0–0.25.0 already ships. **v1.1.0**
is procedural gobo lite. **v1.2.0** is IES practical lite (BYO `.ies`, not a
streamed catalog). Each later cut still closes one gap product artists
actually hit, then we ship a GitHub Release. See [CHECKPOINT.md](CHECKPOINT.md)
for living status.

## Implemented

The 1.2.0 zip is this path. Nothing below is “coming” anymore.

- **1.2.0 IES practical lite** — Load / Sample / Clear a photometric `.ies` on
  the active BEHOLD spot or point (area lights become spots while IES is on).
  Strength / scale. Clear restores prior type / Shape / Gobo. One CC0 sample;
  bring your own `.ies` for a real fixture. Not a manufacturer catalog.
- **1.1.0 Procedural gobo / flag lite** — None / Blinds / Window / Circle on
  the active BEHOLD area or spot light (Wave bands / Brick panes / circular
  cookie, plus scale / strength). None tears the graph down. Not an IES
  library, logo redo, or Light Wrangler streamed catalog.
- **1.0.0 First stable** — artist README, version 1.0.0 everywhere, honest
  Implemented vs Coming. No new operators. Logo stays a placeholder.
- **0.25.0 Catalog resolution presets** — Square 1:1, Portrait 4:5, Landscape 16:9
  plus 2048² / 1080p / 4K on Shoot. Size is the long edge; writes
  `scene.render.resolution_*` at 100% with square pixel aspect. Not gobos,
  IES, logo, or a custom width/height suite.
- **0.24.0 Ground contact polish** — Catcher toggle next to Build. Cyclorama
  gets a soft contact shadow under the product; Solid / HDRI get a Cycles
  shadow-catcher plane with an EEVEE-friendly fallback (contact disc + light
  contact shadows / Light Path material when RNA is missing). Not gobos, IES,
  logo, or EEVEE engine changes beyond the catcher.
- **0.23.0 EEVEE quick look** — Draft uses EEVEE Next when available; Final /
  Product / Hero stay Cycles. Shoot caption Draft = EEVEE · Final = Cycles.
  Cheap product EEVEE shadows / reflections. Not gobos, IES, or logo.
- **0.22.0 Product DoF / focus pick** — DoF on/off, product f-stop (default f/5.6),
  Focus on product / Focus on selected on the active BEHOLD camera. Maps to
  Blender 5.2 `Camera.dof` (`use_dof` / `aperture_fstop` / `focus_distance`).
  Photographer-class lite, not a viewport focus picker. Not gobos, IES, or logo.
- **0.21.0 Light & shadow linking lite** — Link Selected / Unlink / Solo product on
  the active BEHOLD light (Cycles receiver collection include/exclude; optional
  shadow linking via blocker collection on 5.2). Light Wrangler L / Shift+L as a
  compact Lights card, not a viewport modal. Not gobos, IES, or Wrangler gizmos.
- **0.20.0 Compositor look pack** — Clean / Catalog / Dramatic still looks on
  Shoot. Vignette, subtle grain, mild contrast; Dramatic adds bloom-safe glare.
  Toggle tears the graph down. Not gobos, IES, or a full grade suite.
- **0.19.0 Catalog batch export** — one-click front / ¾ / top stills on Shoot,
  plus optional Shot Manager shots, with `{angle}` `{camera}` `{quality}`
  path tokens. Not a render-queue farm.
- **0.18.0 Bake studio to HDRI** — render BEHOLD area lights (optional world) to
  a 1K/2K equirectangular HDR/EXR for reuse or Eevee. Optional apply as the
  scene world. Not gobos, IES, or a Light Wrangler viewport gizmo.
- **0.17.0 Physical exposure polish** — EV, Kelvin white balance, and
  AgX-safe False Color on Shoot (Photographer-class lite). Live Color
  Management apply. Not a full metering suite.
- **0.16.0 Light shaping lite** — Softbox / Strip / Octa / Hard / Rim on the
  active BEHOLD area light (Cycles `shape` / `size` / `size_y` / `energy` /
  `spread` plus a procedural emission falloff). Not gobos, IES, or barn-door
  gizmos — native area lights that no longer read as bare rectangles on chrome.
- **0.15.0 Test hardening + perf** — regression tests and N-panel draw-once
  cache only. No new artist chrome. Does not change Shot Manager.
- **0.14.0 Shot Manager** — named camera + quality + HDRI + backdrop +
  output presets on Shoot. Save / recall “hero chrome” vs “pack shot”
  without duplicating the .blend. Not a full editorial suite.
- **0.13.0 Brand + HDRI world** — official mark in the add-on UI; Studio load /
  rotate / strength / optional reflections-only HDRI; Reset world back to a
  solid studio. Cyclorama + area lights were already here; the missing piece
  was a KeyShot-class environment step (OpenHDRI / BYO file + Z spin).
- **0.12.0** Workflow order + clear errors.
- **0.11.0** Cyclorama auto-fit.
- **0.10.0** Easy update from GitHub Releases.
- **0.9.0** Studio chrome (hero, flow strip, pie / header).
- **0.8.0** Local materials + Assist.
- **0.7.0** Import that works (STEPper NEXT).
- **0.6.0–0.4.0** Turntable, cameras, multi-light + Light Draw.

## Coming

Honest order after 1.2.0. None of this is in the 1.2 zip.

Feature-flagged **Utilities** (Danish wall + balcony mounts, default off) is a
side track, not a product release — [docs/UTILITIES.md](docs/UTILITIES.md).

1. **Logo redo** — replace the placeholder wordmark. Official mark in the
   N-panel can stay until the new art is ready.
2. **Live tessellation regenerate** — OCP / STEPper deflection without
   re-picking the CAD file.
3. **Defeaturing** — fillet / chamfer / hole suppress before tessellate.
4. **Per-body auto-dress** — each STEP color/name → its own look (Assist still
   applies one look to the selection in 1.0).

## Explicitly later / maybe never

- Streamed IES / gobo texture catalogs (1.2.0 is BYO + one sample; 1.1.0 is
  three procedural gobos).
- Full Light Wrangler viewport HDRI gizmo parity (rotate in the 3D View with a
  custom manipulator). Studio Z-rotation is the 0.13.0 cut.
- In-panel BlenderKit browser.

Cadence after 1.0.0 stays one focused feature cut, then a release.
