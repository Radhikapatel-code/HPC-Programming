set -e
 
THREADS=(1 2 4 8 16)
FILES=("input_0.9M.bin" "input_5M.bin" "input_3.6M.bin" "input_20M.bin" "input_14M.bin")
NAMES=("0.9M" "5M" "3.6M" "20M" "14M")
REPEATS=3          # run each config N times and take the minimum (reduces noise)
RESULTS="results_cluster.csv"
LOG="cluster_run.log"
 
echo "=== HPC Cluster Run — Assignment 6 ===" | tee "$LOG"
echo "Host      : $(hostname)"                 | tee -a "$LOG"
echo "Date      : $(date)"                     | tee -a "$LOG"
echo "CPU info  : $(lscpu | grep 'Model name' | cut -d: -f2 | xargs)" | tee -a "$LOG"
echo "Cores     : $(nproc)"                    | tee -a "$LOG"
echo ""                                         | tee -a "$LOG"
 
# Step 1 — compile fresh on the cluster
echo "[1/3] Compiling..." | tee -a "$LOG"
make clean && make
echo "Compilation OK" | tee -a "$LOG"
 
# Step 2 — generate input files if not present
echo "[2/3] Checking input files..." | tee -a "$LOG"
[ ! -f input_0.9M.bin ] && ./input_fileMaker 300  150  900000   10 input_0.9M.bin
[ ! -f input_5M.bin   ] && ./input_fileMaker 250  100  5000000  10 input_5M.bin
[ ! -f input_3.6M.bin ] && ./input_fileMaker 500  200  3600000  10 input_3.6M.bin
[ ! -f input_20M.bin  ] && ./input_fileMaker 500  200  20000000 10 input_20M.bin
[ ! -f input_14M.bin  ] && ./input_fileMaker 1000 400  14000000 10 input_14M.bin
echo "Input files ready" | tee -a "$LOG"
 
# Step 3 — run experiments
echo "[3/3] Running experiments..." | tee -a "$LOG"
echo "Configuration,Threads,Time(s),Run" > "$RESULTS"
 
for i in "${!FILES[@]}"; do
    file=${FILES[$i]}
    name=${NAMES[$i]}
    echo ""
    echo "=== $name ===" | tee -a "$LOG"
 
    for t in "${THREADS[@]}"; do
        echo -n "  $t threads: " | tee -a "$LOG"
        best_time=999999
 
        for r in $(seq 1 $REPEATS); do
            output=$(./interp "$file" /dev/null "$t" 2>&1)
            t_run=$(echo "$output" | grep -oP 'Total time with .* threads: \K[0-9.]+')
 
            if [ -n "$t_run" ]; then
                echo "$name,$t,$t_run,$r" >> "$RESULTS"
                # Track best (minimum) time
                if (( $(echo "$t_run < $best_time" | bc -l) )); then
                    best_time=$t_run
                fi
            fi
        done
 
        echo "$best_time s (best of $REPEATS)" | tee -a "$LOG"
    done
done
 
echo ""
echo "✅ Done! Results → $RESULTS" | tee -a "$LOG"
echo "   Full log    → $LOG"
 
# Quick summary
echo ""
echo "=== Raw results ==="
cat "$RESULTS"