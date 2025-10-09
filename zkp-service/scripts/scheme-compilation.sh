#!/usr/bin/env bash
# Author: adtiomkhin
# Date: 10/08/2025
#
# This file should be run before the initiation of the other parts of this service.
# It will make sure that the circom circuits are compiled
#
# WARNING: Only run this script if you have installed circom, circomlib and Rust
# Guides:
#  - https://habr.com/ru/companies/metalamp/articles/869414/
#  - https://github.com/iden3/circomlib
#  - https://docs.circom.io/getting-started/installation/#installing-circom

set -euo pipefail

# ---------- Ensure Cargo-installed binaries (circom) are on PATH ----------
if [[ -f "$HOME/.cargo/env" ]]; then
  # shellcheck source=/dev/null
  . "$HOME/.cargo/env"
else
  export PATH="$HOME/.cargo/bin:$PATH"
fi

# Allow explicit override: CIRCOM_BIN=/full/path/to/circom ./compile-circuits.sh
CIRCOM_BIN="${CIRCOM_BIN:-$(command -v circom || true)}"
if [[ -z "$CIRCOM_BIN" ]]; then
  echo "ERROR: 'circom' not found. Ensure ~/.cargo/bin is on PATH or set CIRCOM_BIN=/full/path/to/circom" >&2
  exit 1
fi

# ---------- Locate circuits/src ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# You can override via env var:
#   CIRCUITS_SRC_DIR=/path/to/circuits/src ./compile-circuits.sh
if [[ -n "${CIRCUITS_SRC_DIR:-}" ]]; then
  SRC_DIR="$CIRCUITS_SRC_DIR"
else
  # Try common layouts:
  #  - repoRoot/circuits/src  (script at repoRoot/scripts)
  #  - ../../circuits/src     (script at services/api/scripts)
  #  - ../circuits/src
  if [[ -d "$SCRIPT_DIR/../circuits/src" ]]; then
    SRC_DIR="$(cd "$SCRIPT_DIR/../circuits/src" && pwd)"
  elif [[ -d "$SCRIPT_DIR/../../circuits/src" ]]; then
    SRC_DIR="$(cd "$SCRIPT_DIR/../../circuits/src" && pwd)"
  elif [[ -d "$SCRIPT_DIR/../../../circuits/src" ]]; then
    SRC_DIR="$(cd "$SCRIPT_DIR/../../../circuits/src" && pwd)"
  else
    SRC_DIR=""
  fi
fi

if [[ -z "${SRC_DIR:-}" || ! -d "$SRC_DIR" ]]; then
  echo "ERROR: circuits/src not found. Tried relative to: $SCRIPT_DIR" >&2
  echo "Hint: set CIRCUITS_SRC_DIR=/absolute/path/to/circuits/src" >&2
  exit 1
fi

echo "[circom] Scanning: $SRC_DIR"

# ---------- Check for circomlib installation ----------
# Allow explicit override: CIRCOMLIB_PATH=/path/to/circomlib ./compile-circuits.sh
CIRCOMLIB_PATH="${CIRCOMLIB_PATH:-}"

if [[ -z "$CIRCOMLIB_PATH" ]]; then
  # Try to find circomlib in common locations
  POSSIBLE_PATHS=(
    "$SRC_DIR/../circomlib/circuits"
    "$SRC_DIR/../../circomlib/circuits"
    "$SCRIPT_DIR/../circomlib/circuits"
    "$SCRIPT_DIR/../../circomlib/circuits"
    "$SCRIPT_DIR/../../../circomlib/circuits"
    "$SRC_DIR/../node_modules/circomlibjs/circuits"
    "$SRC_DIR/../../node_modules/circomlibjs/circuits"
    "$SCRIPT_DIR/../node_modules/circomlibjs/circuits"
    "$SCRIPT_DIR/../../node_modules/circomlibjs/circuits"
    "/Users/adtimokhin/Documents/useful_github_tools/circomlib/circuits" # <-- Include the location of the circomlib/circuits
  )

  for path in "${POSSIBLE_PATHS[@]}"; do
    if [[ -d "$path" && -f "$path/poseidon.circom" ]]; then
      CIRCOMLIB_PATH="$(cd "$path" && pwd)"
      break
    fi
  done
fi

if [[ -z "$CIRCOMLIB_PATH" || ! -d "$CIRCOMLIB_PATH" ]]; then
  echo "ERROR: circomlib not found!" >&2
  echo "" >&2
  echo "circomlib is required for Poseidon and other circuit templates." >&2
  echo "" >&2
  echo "To install circomlib, choose one of these options:" >&2
  echo "" >&2
  echo "Option 1 - Clone circomlib (recommended):" >&2
  echo "  cd $(dirname "$SRC_DIR")" >&2
  echo "  git clone https://github.com/iden3/circomlib.git" >&2
  echo "" >&2
  echo "Option 2 - Use npm package:" >&2
  echo "  npm install circomlibjs" >&2
  echo "" >&2
  echo "Or set CIRCOMLIB_PATH manually:" >&2
  echo "  CIRCOMLIB_PATH=/path/to/circomlib/circuits ./compile-circuits.sh" >&2
  exit 1
fi

# Verify that required templates exist
if [[ ! -f "$CIRCOMLIB_PATH/poseidon.circom" ]]; then
  echo "ERROR: circomlib found at $CIRCOMLIB_PATH but poseidon.circom is missing!" >&2
  echo "This may be an incomplete or corrupted installation." >&2
  exit 1
fi

echo "[circomlib] Found at: $CIRCOMLIB_PATH"

compiled=0
skipped=0
found_any=0

# ---------- Scan and compile ----------
# Non-recursive; adjust -maxdepth if you want subfolders
while IFS= read -r -d '' file; do
  found_any=1
  filename="$(basename "$file")"
  base="${filename%.circom}"
  r1cs="$SRC_DIR/$base.r1cs"
  wasm_dir="$SRC_DIR/${base}_js"

  need_compile=0
  [[ -f "$r1cs" ]] || need_compile=1
  [[ -d "$wasm_dir" ]] || need_compile=1

  if [[ $need_compile -eq 0 ]]; then
    echo "✓ $base: artifacts present, skipping"
    ((skipped++))
    continue
  fi

  echo "→ Compiling $filename ..."
  (cd "$SRC_DIR" && "$CIRCOM_BIN" "$filename" --r1cs --wasm -l "$CIRCOMLIB_PATH")
  ((compiled++))
done < <(find "$SRC_DIR" -maxdepth 1 -type f -name '*.circom' -print0)

if [[ $found_any -eq 0 ]]; then
  echo "No .circom files found in $SRC_DIR"
fi

echo "[circom] Done. Compiled: $compiled, Skipped: $skipped"
