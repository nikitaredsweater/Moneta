# Author: adtiomkhin
# Date: 1
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
