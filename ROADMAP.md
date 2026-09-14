# ROADMAP

BEHOLD is not a KeyShot clone and not Light Wrangler parity theater. Each cut
closes one gap product artists actually hit in Studio, then we ship a GitHub
Release. See [CHECKPOINT.md](CHECKPOINT.md) for what is on `main` today.

## Shipped

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

## Next (honest order)

1. **Gobos / IES** — window lights, practicals, photometric profiles. Last
   because they need a library story and are easy to ship as a junk drawer.

## Explicitly later / maybe never

- Full Light Wrangler viewport HDRI gizmo parity (rotate in the 3D View with a
  custom manipulator). Studio Z-rotation is the 0.13.0 cut.
- In-panel BlenderKit browser.
- Live tessellation regenerate, defeaturing, per-body auto-dress from STEP
  names.

Cadence stays one focused feature cut, then a release.
