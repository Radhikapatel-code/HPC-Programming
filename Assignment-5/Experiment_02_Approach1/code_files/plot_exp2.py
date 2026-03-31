"""
plot_exp2.py  –  Assignment 05  |  Experiment 02 Plots
=======================================================
Reads:
  data_local/local_exp2.txt     (lab PC timings)
  data_cluster/cluster_exp2.txt (HPC cluster timings)

Generates (saved to results/):
  1. exp2_speedup_<config>_lab.png     – speedup curves for each grid, Lab PC
  2. exp2_speedup_<config>_cluster.png – speedup curves for each grid, Cluster
     Each plot contains 3 curves:
       - No_Del (Assignment 04 baseline)
       - Deferred Insertion
       - Immediate Replacement
  3. exp2_runtime_<config>.png  – total runtime vs threads (lab vs cluster)

Usage:
  python3 plot_exp2.py
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("results", exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 – Parser
# ─────────────────────────────────────────────────────────────────────────────

def parse_exp2(filepath):
    """
    Parse exp2 output.
    Returns dict:  data[(NX,NY)][approach][nthreads] = (interp, mover, total, speedup)
    """
    data = {}
    if not os.path.exists(filepath):
        return data
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            if len(parts) < 8:
                continue
            try:
                nx       = int(parts[0])
                ny       = int(parts[1])
                approach = parts[2].strip()
                nthreads = int(parts[3])
                t_in     = float(parts[4])
                t_mv     = float(parts[5])
                t_tot    = float(parts[6])
                speedup  = float(parts[7])
            except ValueError:
                continue
            key = (nx, ny)
            if key not in data:
                data[key] = {}
            if approach not in data[key]:
                data[key][approach] = {}
            data[key][approach][nthreads] = (t_in, t_mv, t_tot, speedup)
    return data


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 – Speedup plots
# ─────────────────────────────────────────────────────────────────────────────

CONFIGS  = [(250, 100), (500, 200), (1000, 400)]
THREADS  = [2, 4, 8, 16]
APPROACHES = {
    "No_Del(A4)": ("Assignment 04 (No Ins/Del)", "steelblue",  "o", "--"),
    "Deferred":   ("Deferred Insertion",          "darkorange", "s", "-"),
    "Immediate":  ("Immediate Replacement",       "seagreen",   "^", "-"),
}

def plot_speedup(lab_data, cluster_data):
    for (nx, ny) in CONFIGS:

        for source_name, data, suffix in [
                ("Lab PC",      lab_data,      "lab"),
                ("HPC Cluster", cluster_data, "cluster")]:

            if (nx, ny) not in data:
                continue

            fig, ax = plt.subplots(figsize=(7, 5))
            ax.set_title(
                f"Speedup – {source_name}  (NX={nx}, NY={ny})\n"
                f"NUM_Points=14M, Maxiter=10, base=2 threads",
                fontsize=11)
            ax.set_xlabel("Number of Threads", fontsize=10)
            ax.set_ylabel("Speedup (relative to 2 threads)", fontsize=10)
            ax.set_xticks(THREADS)
            ax.grid(True, linestyle="--", alpha=0.5)

            # Ideal speedup line (relative to 2 threads)
            ideal_x = np.array(THREADS)
            ideal_y = ideal_x / 2.0
            ax.plot(ideal_x, ideal_y, color="grey", linestyle=":", linewidth=1.4,
                    label="Ideal (linear)")

            cfg_data = data[(nx, ny)]
            for approach_key, (label, color, marker, ls) in APPROACHES.items():
                if approach_key not in cfg_data:
                    continue
                a_data  = cfg_data[approach_key]
                xs = sorted(a_data.keys())
                ys = [a_data[x][3] for x in xs]   # index 3 = speedup
                ax.plot(xs, ys, color=color, marker=marker, linestyle=ls,
                        linewidth=1.8, markersize=7, label=label)

            ax.legend(fontsize=9)
            plt.tight_layout()
            fname = f"results/exp2_speedup_NX{nx}_NY{ny}_{suffix}.png"
            plt.savefig(fname, dpi=150, bbox_inches="tight")
            plt.close()
            print(f"  Saved {fname}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 – Total runtime vs threads (Lab vs Cluster side-by-side)
# ─────────────────────────────────────────────────────────────────────────────

def plot_runtime_comparison(lab_data, cluster_data):
    for (nx, ny) in CONFIGS:
        lab_has     = (nx, ny) in lab_data
        cluster_has = (nx, ny) in cluster_data
        if not lab_has and not cluster_has:
            continue

        fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=False)
        fig.suptitle(
            f"Total Runtime vs Threads  (NX={nx}, NY={ny}, N=14M)",
            fontsize=13, fontweight="bold")

        for ax, (source_name, data, has) in zip(
                axes,
                [("Lab PC", lab_data, lab_has),
                 ("HPC Cluster", cluster_data, cluster_has)]):
            ax.set_title(source_name, fontsize=11)
            ax.set_xlabel("Number of Threads", fontsize=10)
            ax.set_ylabel("Total Runtime (s)", fontsize=10)
            ax.set_xticks(THREADS)
            ax.grid(True, linestyle="--", alpha=0.5)

            if not has:
                ax.text(0.5, 0.5, "No data", transform=ax.transAxes,
                        ha="center", va="center", fontsize=12, color="grey")
                continue

            cfg = data[(nx, ny)]
            for approach_key, (label, color, marker, ls) in APPROACHES.items():
                if approach_key not in cfg:
                    continue
                a = cfg[approach_key]
                xs = sorted(a.keys())
                ys = [a[x][2] for x in xs]   # index 2 = total runtime
                ax.plot(xs, ys, color=color, marker=marker, linestyle=ls,
                        linewidth=1.8, markersize=7, label=label)
            ax.legend(fontsize=9)

        plt.tight_layout()
        fname = f"results/exp2_runtime_NX{nx}_NY{ny}.png"
        plt.savefig(fname, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Saved {fname}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 – Summary table
# ─────────────────────────────────────────────────────────────────────────────

def print_summary_table(lab_data, cluster_data):
    print("\n" + "="*90)
    print("Experiment 02 – Speedup Summary  (Lab PC)")
    print("="*90)
    print(f"{'Config':>14} {'Approach':>14}  " +
          "  ".join(f"T={t:>2}thr" for t in THREADS))
    print("-"*90)
    for (nx, ny) in CONFIGS:
        if (nx, ny) not in lab_data:
            continue
        for approach_key in APPROACHES:
            if approach_key not in lab_data[(nx, ny)]:
                continue
            a = lab_data[(nx, ny)][approach_key]
            row = f"NX={nx},NY={ny}  {approach_key:>14}  "
            row += "  ".join(
                f"{a[t][3]:>8.3f}" if t in a else "     N/A" for t in THREADS)
            print(row)
        print()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Parsing data files...")
    lab_data     = parse_exp2("data_local/local_exp2.txt")
    cluster_data = parse_exp2("data_cluster/cluster_exp2.txt")

    if not lab_data and not cluster_data:
        print("  No data found yet — run ./exp2 first, then re-run this script.")
        raise SystemExit(0)

    print(f"  Lab data configs:     {list(lab_data.keys())}")
    print(f"  Cluster data configs: {list(cluster_data.keys())}")

    print("\nGenerating speedup plots...")
    plot_speedup(lab_data, cluster_data)

    print("Generating runtime comparison plots...")
    plot_runtime_comparison(lab_data, cluster_data)

    print_summary_table(lab_data, cluster_data)

    print("\nAll plots saved to results/")
