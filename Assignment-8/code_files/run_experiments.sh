#!/bin/bash

set -euo pipefail

MPIRUN=${MPIRUN:-/usr/mpi/gcc/openmpi-1.8.8/bin/mpirun}
DATA_DIR=${DATA_DIR:-data_cluster}
INPUT_DIR=${INPUT_DIR:-inputs}

mkdir -p "$DATA_DIR" "$INPUT_DIR"

make all

echo "Generating assignment input files..."
./inputFileMaker 250 100 900000 10 "$INPUT_DIR/config_a.bin"
./inputFileMaker 250 100 5000000 10 "$INPUT_DIR/config_b.bin"
./inputFileMaker 500 200 3600000 10 "$INPUT_DIR/config_c.bin"
./inputFileMaker 500 200 20000000 10 "$INPUT_DIR/config_d.bin"
./inputFileMaker 1000 400 14000000 10 "$INPUT_DIR/config_e.bin"

CONFIGS=(a b c d e)
TOTAL_CORES=(2 4 8 16 32 64)
MPI_RANKS=(1 1 1 1 2 4)
OMP_THREADS=(2 4 8 16 16 16)

export OMP_PLACES=cores
export OMP_PROC_BIND=close

for cfg in "${CONFIGS[@]}"; do
    input_path="$INPUT_DIR/config_${cfg}.bin"
    out_csv="$DATA_DIR/timing_${cfg}_cluster.csv"

    serial_time=$( ./serial "$input_path" 2>/dev/null \
        | grep "Total Algorithm Time" \
        | awk '{print $(NF-1)}' )
    rm -f output.txt

    echo "TotalCores,MpiRanks,ThreadsPerRank,SerialTime_s,TotalAlgorithmTime_s" > "$out_csv"

    echo ""
    echo "=== Config $cfg ==="
    echo "Serial baseline: ${serial_time}s"

    for idx in "${!TOTAL_CORES[@]}"; do
        total_cores=${TOTAL_CORES[$idx]}
        ranks=${MPI_RANKS[$idx]}
        threads=${OMP_THREADS[$idx]}

        export OMP_NUM_THREADS=$threads
        parallel_time=$( $MPIRUN -np "$ranks" ./parallel "$input_path" 2>/dev/null \
            | grep "Total Algorithm Time" \
            | awk '{print $(NF-1)}' )
        rm -f output.txt

        echo "  cores=$total_cores ranks=$ranks threads=$threads time=${parallel_time}s"
        echo "$total_cores,$ranks,$threads,$serial_time,$parallel_time" >> "$out_csv"
    done
done

echo ""
echo "Cluster timing CSVs saved in $DATA_DIR/"
