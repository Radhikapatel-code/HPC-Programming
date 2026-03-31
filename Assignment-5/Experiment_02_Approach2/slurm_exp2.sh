#!/bin/bash
#SBATCH --job-name=hpc_a5_exp2
#SBATCH --output=slurm_exp2_%j.out
#SBATCH --error=slurm_exp2_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16         # Must be >= max threads tested (16)
#SBATCH --mem=8G                   # 14M * 2 * 8 bytes ≈ 224 MB – plenty of room
#SBATCH --time=01:30:00

# ─── Load modules ─────────────────────────────────────────────────────────────
# module load gcc/12.2.0

echo "Job ID     : $SLURM_JOB_ID"
echo "Node       : $SLURMD_NODENAME"
echo "CPUs alloc : $SLURM_CPUS_PER_TASK"
echo "Start time : $(date)"
echo ""

# ─── Navigate to Experiment 02 code directory ─────────────────────────────────
WORKDIR=$HOME/assignment5/Experiment_02/code_files
cd $WORKDIR

# ─── Build ────────────────────────────────────────────────────────────────────
echo "Compiling..."
make clean
make
echo "Build complete."
echo ""

mkdir -p ../data_cluster

# ─── Run ──────────────────────────────────────────────────────────────────────
# OMP_PROC_BIND and OMP_PLACES help pin threads to physical cores for
# reproducible timing on multi-socket nodes.
export OMP_PROC_BIND=close
export OMP_PLACES=cores

echo "Running Experiment 02 (parallel scalability, 2/4/8/16 threads)..."
./exp2 | tee ../data_cluster/cluster_exp2.txt

echo ""
echo "End time : $(date)"
echo "Done."
