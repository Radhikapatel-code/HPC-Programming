#!/bin/bash
# ─── run_exp1.sh ─────────────────────────────────────────────────────────────
# Builds and runs Experiment 01 (serial scaling with particle count).
# Saves raw output to data_local/local_exp1.txt
#
# Usage:  bash run_exp1.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e
cd "$(dirname "$0")"

mkdir -p data_local

echo "Building Experiment 01..."
make clean && make

echo ""
echo "Running Experiment 01  (this may take several minutes for large N)..."
./exp1 | tee data_local/local_exp1.txt

echo ""
echo "Done. Results saved to data_local/local_exp1.txt"
