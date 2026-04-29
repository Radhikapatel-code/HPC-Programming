#!/bin/bash
#SBATCH --job-name=hpc_a08_hybrid
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --partition=compute

set -euo pipefail

MPIRUN=/usr/mpi/gcc/openmpi-1.8.8/bin/mpirun

cd "$SLURM_SUBMIT_DIR"
mkdir -p logs data_cluster results inputs

export OMP_PLACES=cores
export OMP_PROC_BIND=close
export MPIRUN

echo "Job $SLURM_JOB_ID started on $(hostname) at $(date)"
echo "Allocated nodes: $SLURM_JOB_NUM_NODES"
echo "OpenMP threads per rank available: $SLURM_CPUS_PER_TASK"

make clean
make all

echo "Running correctness check..."
make test_cluster

echo "Running performance sweep..."
bash ./run_experiments.sh

echo "Generating plots..."
python3 ./plot_results.py

echo "Job finished at $(date)"
