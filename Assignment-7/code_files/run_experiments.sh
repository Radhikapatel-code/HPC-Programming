#!/bin/bash
# ─────────────────────────────────────────────────────────────────────
#  run_experiments.sh
#
#  Generates all five input configurations, then runs the parallel
#  binary with 1, 2, 4, 8, 16 threads and records wall-clock time.
#
#  Usage (local):
#    chmod +x run_experiments.sh
#    ./run_experiments.sh
#
#  Output:
#    results/timing_<config>.csv   – one CSV per configuration
# ─────────────────────────────────────────────────────────────────────

set -e

mkdir -p results inputs

# Build everything first
make all

echo "Generating input files..."

# ── Five configurations from the assignment ───────────────────────────
# (a) Nx=250, Ny=100, points=0.9M,  Maxiter=10
./inputFileMaker 250 100 900000  10 inputs/config_a.bin

# (b) Nx=250, Ny=100, points=5M,   Maxiter=10
./inputFileMaker 250 100 5000000 10 inputs/config_b.bin

# (c) Nx=500, Ny=200, points=3.6M, Maxiter=10
./inputFileMaker 500 200 3600000 10 inputs/config_c.bin

# (d) Nx=500, Ny=200, points=20M,  Maxiter=10
./inputFileMaker 500 200 20000000 10 inputs/config_d.bin

# (e) Nx=1000, Ny=400, points=14M, Maxiter=10
./inputFileMaker 1000 400 14000000 10 inputs/config_e.bin

echo "Input files ready."

CONFIGS=(a b c d e)
THREADS=(1 2 4 8 16)

for cfg in "${CONFIGS[@]}"; do
    OUTCSV="results/timing_${cfg}.csv"
    echo "Threads,TotalAlgorithmTime_s" > "$OUTCSV"

    echo ""
    echo "=== Config $cfg ==="

    for t in "${THREADS[@]}"; do
        export OMP_NUM_THREADS=$t
        # Capture total algorithm time from stdout
        TIME=$( ./parallel inputs/config_${cfg}.bin 2>/dev/null \
                | grep "Total Algorithm Time" \
                | awk '{print $(NF-1)}' )
        echo "  Threads=$t  Time=${TIME}s"
        echo "$t,$TIME" >> "$OUTCSV"
    done
done

echo ""
echo "All results saved in results/  ── run plot_results.py to visualize."