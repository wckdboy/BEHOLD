#!/usr/bin/env bash
# Build an installable Blender add-on zip for BEHOLD.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${ROOT}/behold"
DIST="${ROOT}/dist"
MANIFEST="${SRC}/blender_manifest.toml"

if [[ ! -f "${MANIFEST}" ]]; then
  echo "error: missing ${MANIFEST}" >&2
  exit 1
fi

VERSION="$(
  python3 - "${MANIFEST}" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
if not match:
    raise SystemExit("version not found in blender_manifest.toml")
print(match.group(1))
PY
)"

mkdir -p "${DIST}"
OUT="${DIST}/behold-${VERSION}.zip"
TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

STAGE="${TMP}/behold"
mkdir -p "${STAGE}"

# Copy add-on tree without rsync (not always installed).
python3 - "${SRC}" "${STAGE}" <<'PY'
import os, shutil, sys
src, dst = sys.argv[1], sys.argv[2]
skip_dirs = {"__pycache__"}
skip_suffixes = {".pyc", ".pyo", ".blend", ".blend1"}
skip_names = {".DS_Store"}

for root, dirs, files in os.walk(src):
    dirs[:] = [d for d in dirs if d not in skip_dirs]
    rel = os.path.relpath(root, src)
    target_root = dst if rel == "." else os.path.join(dst, rel)
    os.makedirs(target_root, exist_ok=True)
    for name in files:
        if name in skip_names or os.path.splitext(name)[1] in skip_suffixes:
            continue
        shutil.copy2(os.path.join(root, name), os.path.join(target_root, name))
PY

mkdir -p "${STAGE}/assets"
if [[ -z "$(find "${STAGE}/assets" -mindepth 1 -maxdepth 1 2>/dev/null || true)" ]]; then
  printf '# Keeps the assets package in the install zip.\n' > "${STAGE}/assets/.gitkeep"
fi

rm -f "${OUT}"
(
  cd "${TMP}"
  zip -r -q "${OUT}" behold
)

echo "Built ${OUT}"
echo "Install in Blender 5.2: Edit → Preferences → Get Extensions → Install from Disk → select this zip"
