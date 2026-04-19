#!/usr/bin/env python3
"""
plot_results.py
───────────────
Reads results/timing_<x>.csv files produced by run_experiments.sh and
generates:
  • Execution time vs. thread count  (one line per config)
  • Speedup vs. thread count
  • Parallel efficiency vs. thread count

Output files:
  results/exec_time.png
  results/speedup.png
  results/efficiency.png
"""

import os
import csv
import matplotlib.pyplot as plt

CONFIGS = {
    'a': 'Nx=250, Ny=100, 0.9M pts',
    'b': 'Nx=250, Ny=100, 5M pts',
    'c': 'Nx=500, Ny=200, 3.6M pts',
    'd': 'Nx=500, Ny=200, 20M pts',
    'e': 'Nx=1000, Ny=400, 14M pts',
}

os.makedirs('results', exist_ok=True)


def load_csv(path):
    threads, times = [], []
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            threads.append(int(row['Threads']))
            times.append(float(row['TotalAlgorithmTime_s']))
    return threads, times


all_data = {}
for key in CONFIGS:
    path = f'results/timing_{key}.csv'
    if os.path.exists(path):
        all_data[key] = load_csv(path)

if not all_data:
    print("No result CSVs found. Run run_experiments.sh first.")
    exit(1)

# ── Plot 1: Execution time ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
for key, (threads, times) in all_data.items():
    ax.plot(threads, times, marker='o', label=CONFIGS[key])
ax.set_xlabel('Number of Threads')
ax.set_ylabel('Execution Time (s)')
ax.set_title('Execution Time vs Thread Count')
ax.legend(fontsize=8)
ax.set_xticks([1, 2, 4, 8, 16])
ax.grid(True)
plt.tight_layout()
plt.savefig('results/exec_time.png', dpi=150)
print("Saved results/exec_time.png")

# ── Plot 2: Speedup ───────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot([1, 2, 4, 8, 16], [1, 2, 4, 8, 16], 'k--', label='Ideal', linewidth=1)
for key, (threads, times) in all_data.items():
    if 1 in threads:
        t1 = times[threads.index(1)]
        speedups = [t1 / t for t in times]
        ax.plot(threads, speedups, marker='o', label=CONFIGS[key])
ax.set_xlabel('Number of Threads')
ax.set_ylabel('Speedup')
ax.set_title('Speedup vs Thread Count')
ax.legend(fontsize=8)
ax.set_xticks([1, 2, 4, 8, 16])
ax.grid(True)
plt.tight_layout()
plt.savefig('results/speedup.png', dpi=150)
print("Saved results/speedup.png")

# ── Plot 3: Parallel efficiency ───────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
ax.axhline(1.0, color='k', linestyle='--', label='Ideal (100%)', linewidth=1)
for key, (threads, times) in all_data.items():
    if 1 in threads:
        t1 = times[threads.index(1)]
        eff = [(t1 / t) / p for t, p in zip(times, threads)]
        ax.plot(threads, eff, marker='o', label=CONFIGS[key])
ax.set_xlabel('Number of Threads')
ax.set_ylabel('Parallel Efficiency (S/p)')
ax.set_title('Parallel Efficiency vs Thread Count')
ax.legend(fontsize=8)
ax.set_xticks([1, 2, 4, 8, 16])
ax.grid(True)
plt.tight_layout()
plt.savefig('results/efficiency.png', dpi=150)
print("Saved results/efficiency.png")