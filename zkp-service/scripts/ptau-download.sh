# Author: adtiomkhin
# Date: 10/08/2025
#
#
# After successfully running the scheme-compilation.sh file, you need to make
# sure that you have all necessary .ptau files for each of your schemes.
#
# For that, you need to find out how many constraints a scheme has
# To do that, you can run:
#
# npm snarkjs r1cs info [scheme_name].r1cs
#
#
# Then, go to:
#
# https://github.com/iden3/snarkjs?tab=readme-ov-file#7-prepare-phase-2
#
# and select the correct ptau file to download. Name it hez[n].ptau, where n is
# the power.
#
#
# Download the files into circuits/ptau/ folder. It is marked to be
# ignored by git.
#
# Example instruction to copy the file:
#
# wget https://storage.googleapis.com/zkevm/ptau/powersOfTau28_hez_final_08.ptau -O hez8.ptau
#
#
# Maybe later I will implement a script that will do this automatically, but not right now
#
# Guides:
#   - https://habr.com/ru/companies/metalamp/articles/869414/
#   - https://github.com/iden3/snarkjs?tab=readme-ov-file#7-prepare-phase-2


TARGET_DIR="../circuits/ptau"
FILE_NAME="hez13.ptau"
URL="https://storage.googleapis.com/zkevm/ptau/powersOfTau28_hez_final_13.ptau"

mkdir -p "$TARGET_DIR"

echo "Downloading $FILE_NAME..."

if command -v wget >/dev/null 2>&1; then
  wget -q "$URL" -O "$TARGET_DIR/$FILE_NAME"
elif command -v curl >/dev/null 2>&1; then
  curl -sSL "$URL" -o "$TARGET_DIR/$FILE_NAME"
else
  echo "Neither wget nor curl found. Please install one of them."
  exit 1
fi

if [ -f "$TARGET_DIR/$FILE_NAME" ]; then
  echo "Download complete"
else
  echo "Download failed."
  exit 1
fi
