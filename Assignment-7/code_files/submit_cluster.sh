#!/bin/bash
#SBATCH --job-name=hpc_a07
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16        # request 16 cores (1 socket)
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --partition=compute       # change to your cluster's partition name

# ─── Load modules (adjust module names for your HPC cluster) ─────────
# module load gcc/12.2.0
# module load python/3.10

# ─── Move to submission directory ────────────────────────────────────
cd $SLURM_SUBMIT_DIR

mkdir -p logs results inputs

echo "Job $SLURM_JOB_ID started on $(hostname) at $(date)"
echo "CPUs available: $SLURM_CPUS_PER_TASK"

# ─── Build ────────────────────────────────────────────────────────────
make all

# ─── Generate inputs ──────────────────────────────────────────────────
./inputFileMaker 250  100  900000   10 inputs/config_a.bin
./inputFileMaker 250  100  5000000  10 inputs/config_b.bin
./inputFileMaker 500  200  3600000  10 inputs/config_c.bin
./inputFileMaker 500  200  20000000 10 inputs/config_d.bin
./inputFileMaker 1000 400  14000000 10 inputs/config_e.bin

# ─── Run experiments ──────────────────────────────────────────────────
CONFIGS=(a b c d e)
THREADS=(1 2 4 8 16)

for cfg in "${CONFIGS[@]}"; do
    OUTCSV="results/timing_${cfg}.csv"
    echo "Threads,TotalAlgorithmTime_s" > "$OUTCSV"

    echo "=== Config $cfg ==="
    for t in "${THREADS[@]}"; do
        export OMP_NUM_THREADS=$t
        TIME=$( ./parallel inputs/config_${cfg}.bin 2>/dev/null \
                | grep "Total Algorithm Time" \
                | awk '{print $(NF-1)}' )
        echo "  Threads=$t  Time=${TIME}s"
        echo "$t,$TIME" >> "$OUTCSV"
    done
done

# ─── Plot (if matplotlib available) ──────────────────────────────────
python3 plot_results.py || echo "Plotting skipped (no matplotlib)"

echo "Job finished at $(date)"