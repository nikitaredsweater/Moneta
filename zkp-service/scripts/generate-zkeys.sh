#!/usr/bin/env bash
# Author: adtiomkhin
# Date: 10/08/2025
#
# Generate zkey files for circom circuits using snarkjs
#
# Usage:
#   ./generate-zkeys.sh [PTAU_FILE] [CONTRIBUTION_NAME]
#
# Examples:
#   ./generate-zkeys.sh powersOfTau28_hez_final_10.ptau
#   ./generate-zkeys.sh powersOfTau28_hez_final_10.ptau "Alice's Contribution"
#
# The script will process all .r1cs files in the circuits/src directory

set -euo pipefail

# ---------- Configuration ----------
DEFAULT_CONTRIBUTION_NAME="Anonymous Contribution $(date +%Y%m%d_%H%M%S)"
PTAU_FILE="${1:-}"
CONTRIBUTION_NAME="${2:-$DEFAULT_CONTRIBUTION_NAME}"

# ---------- Helper Functions ----------
print_usage() {
  cat << EOF
Usage: $0 [PTAU_FILE] [CONTRIBUTION_NAME]

Arguments:
  PTAU_FILE          Path to the Powers of Tau file (.ptau)
                     If not provided, will look for .ptau files in common locations
  CONTRIBUTION_NAME  Name for the contribution (optional)
                     Default: "$DEFAULT_CONTRIBUTION_NAME"

Examples:
  $0 powersOfTau28_hez_final_10.ptau
  $0 /path/to/ceremony.ptau "My Contribution"

Note: This script requires snarkjs to be installed globally or in node_modules
EOF
}

# ---------- Check for help flag ----------
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  print_usage
  exit 0
fi

# ---------- Locate script and project directories ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find circuits/src directory
if [[ -n "${CIRCUITS_SRC_DIR:-}" ]]; then
  SRC_DIR="$CIRCUITS_SRC_DIR"
else
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

echo "[zkey] Using circuits directory: $SRC_DIR"

# ---------- Check for Node.js ----------
if ! command -v node &> /dev/null; then
  echo "ERROR: Node.js is not installed!" >&2
  echo "" >&2
  echo "Please install Node.js from https://nodejs.org/" >&2
  echo "Or use a package manager:" >&2
  echo "  - macOS: brew install node" >&2
  echo "  - Ubuntu/Debian: sudo apt install nodejs npm" >&2
  exit 1
fi

echo "[node] Found Node.js version: $(node --version)"

# ---------- Check for npm ----------
if ! command -v npm &> /dev/null; then
  echo "ERROR: npm is not installed!" >&2
  echo "npm should come with Node.js. Please reinstall Node.js." >&2
  exit 1
fi

echo "[npm] Found npm version: $(npm --version)"

# ---------- Check for snarkjs ----------
SNARKJS_BIN=""

# Check for global snarkjs
if command -v snarkjs &> /dev/null; then
  SNARKJS_BIN="snarkjs"
  echo "[snarkjs] Found global installation: $(which snarkjs)"
# Check for local node_modules
elif [[ -f "$SCRIPT_DIR/../node_modules/.bin/snarkjs" ]]; then
  SNARKJS_BIN="$SCRIPT_DIR/../node_modules/.bin/snarkjs"
  echo "[snarkjs] Found in node_modules: $SNARKJS_BIN"
elif [[ -f "$SCRIPT_DIR/../../node_modules/.bin/snarkjs" ]]; then
  SNARKJS_BIN="$SCRIPT_DIR/../../node_modules/.bin/snarkjs"
  echo "[snarkjs] Found in node_modules: $SNARKJS_BIN"
else
  echo "WARNING: snarkjs not found!" >&2
  echo "" >&2
  echo "Installing snarkjs globally..." >&2

  if npm install -g snarkjs; then
    SNARKJS_BIN="snarkjs"
    echo "[snarkjs] Successfully installed globally"
  else
    echo "ERROR: Failed to install snarkjs globally" >&2
    echo "" >&2
    echo "You can try installing it locally in your project:" >&2
    echo "  npm install snarkjs" >&2
    exit 1
  fi
fi

# # Verify snarkjs works
# if ! "$SNARKJS_BIN" 2>&1 | head -n 1 | grep -q "snarkjs"; then
#   echo "ERROR: snarkjs is installed but not working properly" >&2
#   exit 1
# fi

# Prints which snarkjs is installed globally.
# echo "[snarkjs] Version: $("$SNARKJS_BIN" --version)"

# ---------- Locate PTAU file ----------
if [[ -z "$PTAU_FILE" ]]; then
  echo "Searching for .ptau files..."

  # Search in common locations
  SEARCH_DIRS=(
    "$SRC_DIR"
    "$SRC_DIR/.."
    "$SRC_DIR/../.."
    "$SCRIPT_DIR"
    "$SCRIPT_DIR/.."
    "$SCRIPT_DIR/../.."
    "."
  )

  for dir in "${SEARCH_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
      while IFS= read -r -d '' file; do
        PTAU_FILE="$file"
        echo "[ptau] Found: $PTAU_FILE"
        break 2
      done < <(find "$dir" -maxdepth 1 -type f -name '*.ptau' -print0 2>/dev/null)
    fi
  done

  if [[ -z "$PTAU_FILE" ]]; then
    echo "ERROR: No .ptau file found!" >&2
    echo "" >&2
    echo "Please provide a Powers of Tau file as the first argument:" >&2
    echo "  $0 /path/to/powersOfTau.ptau" >&2
    echo "" >&2
    echo "You can download a ceremony file from:" >&2
    echo "  https://github.com/iden3/snarkjs#7-prepare-phase-2" >&2
    exit 1
  fi
fi

# Verify PTAU file exists
if [[ ! -f "$PTAU_FILE" ]]; then
  echo "ERROR: PTAU file not found: $PTAU_FILE" >&2
  exit 1
fi

PTAU_FILE="$(cd "$(dirname "$PTAU_FILE")" && pwd)/$(basename "$PTAU_FILE")"
echo "[ptau] Using: $PTAU_FILE"
echo "[contribution] Name: \"$CONTRIBUTION_NAME\""

# ---------- Process all .r1cs files ----------
processed=0
skipped=0
found_any=0

while IFS= read -r -d '' r1cs_file; do
  found_any=1
  filename="$(basename "$r1cs_file")"
  base="${filename%.r1cs}"

  zkey_0000="$SRC_DIR/${base}_0000.zkey"
  zkey_final="$SRC_DIR/${base}_final.zkey"

  # Check if final zkey already exists
  if [[ -f "$zkey_final" ]]; then
    echo "✓ $base: final zkey exists, skipping"
    ((skipped++))
    continue
  fi

  echo ""
  echo "→ Processing $base..."

  # Step 1: Setup (groth16 setup)
  echo "  [1/3] Running groth16 setup..."
  if "$SNARKJS_BIN" groth16 setup "$r1cs_file" "$PTAU_FILE" "$zkey_0000"; then
    echo "  ✓ Created ${base}_0000.zkey"
  else
    echo "  ✗ Failed to create initial zkey for $base" >&2
    continue
  fi

  # Step 2: Contribute to the ceremony
  echo "  [2/3] Contributing to the ceremony..."
  if "$SNARKJS_BIN" zkey contribute "$zkey_0000" "$zkey_final" --name="$CONTRIBUTION_NAME" -v -e="$(head -c 64 /dev/urandom | xxd -p -c 256)"; then
    echo "  ✓ Created ${base}_final.zkey"

    # FIXME: I am not sure if we even need this file removed...
    # Clean up intermediate file
    rm -f "$zkey_0000"

  else
    echo "  ✗ Failed to contribute to ceremony for $base" >&2
    continue
  fi

    vkey_file="$SRC_DIR/${base}_verification_key.json"
    echo "  [3/3] Generating verification key..."
    if "$SNARKJS_BIN" zkey export verificationkey "$zkey_final" "$vkey_file"; then
        echo "  ✓ Created ${base}_verification_key.json"
        ((processed++))
        else
        echo "  ✗ Failed to generate verification key for $base" >&2
        continue
    fi

done < <(find "$SRC_DIR" -maxdepth 1 -type f -name '*.r1cs' -print0)

if [[ $found_any -eq 0 ]]; then
  echo ""
  echo "No .r1cs files found in $SRC_DIR"
  echo "Have you compiled your circuits? Run compile-circuits.sh first."
  exit 1
fi

echo ""
echo "[zkey] Done. Processed: $processed, Skipped: $skipped"

if [[ $processed -gt 0 ]]; then
  echo ""
  echo "Next steps:"
  echo "  1. Generate verification keys:"
  echo "     snarkjs zkey export verificationkey <circuit>_final.zkey verification_key.json"
  echo "  2. Generate proofs:"
  echo "     snarkjs groth16 prove <circuit>_final.zkey witness.wtns proof.json public.json"
fi
