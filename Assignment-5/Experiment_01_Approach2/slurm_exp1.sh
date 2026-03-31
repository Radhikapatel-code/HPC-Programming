#!/bin/bash
#SBATCH --job-name=hpc_a5_exp1
#SBATCH --output=slurm_exp1_%j.out
#SBATCH --error=slurm_exp1_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1          # Exp1 is serial – 1 core is enough
#SBATCH --mem=32G                  # 10^9 particles * 2*8 bytes ≈ 16 GB
#SBATCH --time=02:00:00

# ─── Load required modules ────────────────────────────────────────────────────
# Uncomment / adjust module names to match your cluster's environment
# module load gcc/12.2.0
# module load openmpi/4.1.4          # only needed if your cluster links omp via mpi
# ─────────────────────────────────────────────────────────────────────────────

echo "Job ID     : $SLURM_JOB_ID"
echo "Node       : $SLURMD_NODENAME"
echo "Start time : $(date)"
echo ""

# ─── Navigate to Experiment 01 code directory ─────────────────────────────────
# EDIT THIS PATH to match where you upload your files on the cluster
WORKDIR=$HOME/assignment5/Experiment_01/code_files
cd $WORKDIR

# ─── Build ────────────────────────────────────────────────────────────────────
echo "Compiling..."
make clean
make
echo "Build complete."
echo ""

# ─── Create output directory ──────────────────────────────────────────────────
mkdir -p ../data_cluster

# ─── Run ──────────────────────────────────────────────────────────────────────
echo "Running Experiment 01 (serial mover scaling)..."
./exp1 | tee ../data_cluster/cluster_exp1.txt

echo ""
echo "End time : $(date)"
echo "Done."
