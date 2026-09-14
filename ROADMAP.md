# ROADMAP

BEHOLD is not a KeyShot clone and not Light Wrangler parity theater. Each cut
closes one gap product artists actually hit in Studio, then we ship a GitHub
Release. See [CHECKPOINT.md](CHECKPOINT.md) for what is on `main` today.

## Shipped

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

1. **Light shaping / softbox textures** — area lights still read as rectangles
   on chrome. KeyShot and Light Wrangler win on barn doors, softbox maps, and
   falloff. Native Blender lights first. Not an IES catalog.
2. **Physical exposure / false color polish** — EV and false color already live
   on Advanced. Make them trustworthy for hero chrome (metering, AgX-safe
   false color) so artists stop guessing.
3. **Bake-to-HDRI** — studio + area lights → an environment the artist can
   reuse or hand off. After Shot Manager, not before: you bake a *look*, not a
   random rig.
4. **Gobos / IES** — window lights, practicals, photometric profiles. Last
   because they need a library story and are easy to ship as a junk drawer.

## Explicitly later / maybe never

- Full Light Wrangler viewport HDRI gizmo parity (rotate in the 3D View with a
  custom manipulator). Studio Z-rotation is the 0.13.0 cut.
- In-panel BlenderKit browser.
- Live tessellation regenerate, defeaturing, per-body auto-dress from STEP
  names.

Cadence stays one focused feature cut, then a release.
