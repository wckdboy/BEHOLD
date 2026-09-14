# Test fixtures

## `unit_cube.step`

Self-generated **10 mm** axis-aligned box (origin to 10,10,10), AP214
(`AUTOMOTIVE_DESIGN`) closed-shell `MANIFOLD_SOLID_BREP`.

| | |
| --- | --- |
| Provenance | Written by `generate_unit_cube.py` for BEHOLD. Not copied from a vendor CAD export. |
| License | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) (public-domain dedication) |
| Units | millimetres |
| Regenerating | `python3 tests/fixtures/generate_unit_cube.py` |

OpenCASCADE / STEPper should read this as a single solid. CI does not require OCP:
format dispatch tests only need the filename and the ISO-10303-21 text. Tessellation
## `github/*.json`

Trimmed GitHub Releases API payloads for `tests/test_updates.py`. Offline only — CI never hits the network.
