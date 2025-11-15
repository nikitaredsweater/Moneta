#!/usr/bin/env bash
# Author: adtimokhin
# Date: 10/12/2025
#
# Setup required data directories for ZKP service
#
# Usage:
#   ./setup-data-dirs.sh
#
# Description:
#   This script ensures that the following directories exist:
#     - data
#     - data/input
#     - data/output
#
#   These folders are ignored by .gitignore and are required for proof generation.
# ------------------------------------------------------------------------------

set -euo pipefail

# ---------- Locate script and project root ----------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ---------- Define directories ----------
DATA_DIR="$PROJECT_ROOT/data"
INPUT_DIR="$DATA_DIR/input"
OUTPUT_DIR="$DATA_DIR/output"

# ---------- Helper function ----------
create_dir_if_missing() {
  local dir="$1"
  if [[ ! -d "$dir" ]]; then
    mkdir -p "$dir"
  else
    echo "[data] Directory already exists: $dir"
  fi
}

# ---------- Main ----------

create_dir_if_missing "$DATA_DIR"
create_dir_if_missing "$INPUT_DIR"
create_dir_if_missing "$OUTPUT_DIR"

exit 0
