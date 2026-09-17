#!/usr/bin/env bash
# Build installable Blender extension zips for the BEHOLD 2.0 suite.
#
# Install in Blender 5.2 LTS (Install from Disk, each zip independently):
#   1. behold-studio-2.0.0.zip
#   2. behold-lighting-2.0.0.zip
#   3. behold-product-2.0.0.zip
#   4. behold-utilities-2.0.0.zip  (optional)
# Do not use GitHub's "Source code (zip)".
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="${ROOT}/dist"
python3 "${ROOT}/scripts/vendor_common.py"

ADDONS=(behold_studio behold_lighting behold_product behold_utilities)

stage_tree() {
  python3 - "$1" "$2" <<'PY'
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
}

read_version() {
  python3 - "$1" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
if not match:
    raise SystemExit("version not found in blender_manifest.toml")
print(match.group(1))
PY
}

mkdir -p "${DIST}"

for addon in "${ADDONS[@]}"; do
  SRC="${ROOT}/${addon}"
  MANIFEST="${SRC}/blender_manifest.toml"
  if [[ ! -f "${MANIFEST}" ]]; then
    echo "error: missing ${MANIFEST}" >&2
    exit 1
  fi
  VERSION="$(read_version "${MANIFEST}")"
  slug="${addon#behold_}"
  OUT="${DIST}/behold-${slug}-${VERSION}.zip"
  TMP="$(mktemp -d)"
  STAGE="${TMP}/${addon}"
  mkdir -p "${STAGE}"
  stage_tree "${SRC}" "${STAGE}"
  mkdir -p "${STAGE}/assets"
  if [[ -z "$(find "${STAGE}/assets" -mindepth 1 -maxdepth 1 2>/dev/null || true)" ]]; then
    printf '# Keeps the assets package in the install zip.\n' > "${STAGE}/assets/.gitkeep"
  fi
  rm -f "${OUT}"
  built=0
  if command -v blender >/dev/null 2>&1; then
    if blender --command extension build --help >/dev/null 2>&1; then
      if blender --command extension build \
        --source-dir "${STAGE}" \
        --output-filepath "${OUT}" >/dev/null 2>&1; then
        built=1
        echo "Built ${OUT} with blender --command extension build"
      fi
    fi
  fi
  if [[ "${built}" -eq 0 ]]; then
    (
      cd "${TMP}"
      zip -r -q "${OUT}" "${addon}"
    )
    echo "Built ${OUT}"
  fi
  rm -rf "${TMP}"
done

echo "Install in Blender 5.2: Edit → Preferences → Get Extensions → Install from Disk"
echo "Order: Studio, Lighting, Product, then optional Utilities."
