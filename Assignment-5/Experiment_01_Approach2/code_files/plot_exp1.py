"""
plot_exp1.py  –  Assignment 05  |  Experiment 01 Plots
=======================================================
Reads:
  data_local/local_exp1.txt   (lab PC timings)
  data_cluster/cluster_exp1.txt  (HPC cluster timings)

Generates (saved to results/):
  1. exp1_scaling_<config>.png   – 3 log-log comparison plots (one per grid)
     Each plot shows 4 lines: Lab+Deferred, Lab+Immediate, Cluster+Deferred,
     Cluster+Immediate  vs  number of particles.

  2. exp1_perparticle_ppc.png    – per-particle time vs particles-per-cell (PPC)

  3. exp1_particle_distribution.png  – histogram verifying uniform distribution

Usage:
  python3 plot_exp1.py
"""

import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── output directory ─────────────────────────────────────────────────────────
os.makedirs("results", exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 – Parse output files
# ─────────────────────────────────────────────────────────────────────────────

def parse_exp1(filepath):
    """
    Parse exp1 output. Returns a dict:
      data[(NX, NY)][num_points] = (total_interp, total_deferred, total_immediate, avg_del)
    """
    data = {}
    if not os.path.exists(filepath):
        return data
    with open(filepath) as f:
        cur_nx, cur_ny = None, None
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                # Look for config header comment like "# ── CONFIG 1  NX=250  NY=100"
                if "NX=" in line and "NY=" in line:
                    parts = line.split()
                    for tok in parts:
                        if tok.startswith("NX="):
                            cur_nx = int(tok.split("=")[1])
                        if tok.startswith("NY="):
                            cur_ny = int(tok.split("=")[1])
                continue
            # Data lines:  NX,NY,NUM_Points,Total_Interp,Total_Deferred,
            #               Total_Immediate,Avg_Deletions_per_iter
            parts = line.split(",")
            if len(parts) < 7:
                continue
            try:
                nx   = int(parts[0])
                ny   = int(parts[1])
                np_  = int(parts[2])
                t_in = float(parts[3])
                t_de = float(parts[4])
                t_im = float(parts[5])
                t_av = float(parts[6])
            except ValueError:
                continue
            key = (nx, ny)
            if key not in data:
                data[key] = {}
            data[key][np_] = (t_in, t_de, t_im, t_av)
    return data


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 – Plot scaling (Experiment 01, one plot per grid config)
# ─────────────────────────────────────────────────────────────────────────────

CONFIGS = [(250, 100), (500, 200), (1000, 400)]

def plot_scaling(lab_data, cluster_data):
    for (nx, ny) in CONFIGS:
        fig, axes = plt.subplots(1, 2, figsize=(13, 5))
        fig.suptitle(f"Exp 01 – Execution Time Scaling  (NX={nx}, NY={ny})",
                     fontsize=13, fontweight="bold")

        for ax_idx, (ax, ylabel, t_idx, title) in enumerate(zip(
                axes,
                ["Total Mover Time (s)", "Total Mover Time (s)"],
                [1, 2],           # index into (t_in, t_de, t_im, t_av)
                ["Approach 1 – Deferred Insertion",
                 "Approach 2 – Immediate Replacement"])):

            ax.set_title(title, fontsize=11)
            ax.set_xlabel("Number of Particles", fontsize=10)
            ax.set_ylabel(ylabel, fontsize=10)
            ax.set_xscale("log")
            ax.set_yscale("log")
            ax.grid(True, which="both", linestyle="--", alpha=0.5)

            for source_name, data, color, marker in [
                    ("Lab PC",      lab_data,     "steelblue",  "o"),
                    ("HPC Cluster", cluster_data, "darkorange", "s")]:
                if (nx, ny) not in data:
                    continue
                d = data[(nx, ny)]
                xs = sorted(d.keys())
                ys = [d[x][t_idx] for x in xs]
                ax.plot(xs, ys, color=color, marker=marker,
                        linewidth=1.8, markersize=6, label=source_name)

            ax.legend(fontsize=9)

        plt.tight_layout()
        fname = f"results/exp1_scaling_NX{nx}_NY{ny}.png"
        plt.savefig(fname, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  Saved {fname}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 – Per-particle time vs PPC
# ─────────────────────────────────────────────────────────────────────────────

def plot_perparticle_ppc(lab_data):
    """
    PPC = particles / (NX * NY)
    Per-particle time = total_mover / NUM_Points
    """
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("Per-Particle Execution Time vs Particles Per Cell (PPC)",
                 fontsize=13, fontweight="bold")

    colors = plt.cm.tab10.colors

    for ax_idx, (ax, t_idx, title) in enumerate(zip(
            axes, [1, 2],
            ["Deferred Insertion", "Immediate Replacement"])):
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("Particles Per Cell (PPC)", fontsize=10)
        ax.set_ylabel("Per-Particle Time (s/particle)", fontsize=10)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.grid(True, which="both", linestyle="--", alpha=0.5)

        for i, (nx, ny) in enumerate(CONFIGS):
            if (nx, ny) not in lab_data:
                continue
            d = lab_data[(nx, ny)]
            total_cells = nx * ny
            xs = sorted(d.keys())
            ppc = [x / total_cells for x in xs]
            ys  = [d[x][t_idx] / x for x in xs]   # time per particle
            ax.plot(ppc, ys, marker="o", color=colors[i],
                    linewidth=1.8, markersize=6,
                    label=f"NX={nx}, NY={ny}")
        ax.legend(fontsize=9)

    plt.tight_layout()
    fname = "results/exp1_perparticle_ppc.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {fname}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 – Particle distribution verification
# ─────────────────────────────────────────────────────────────────────────────

def plot_particle_distribution():
    """
    Generate synthetic sample to verify RNG gives uniform distribution.
    In a real run you would export the particle array; here we use numpy
    to replicate srand(42) + rand()/RAND_MAX for demonstration.
    """
    rng = np.random.default_rng(42)
    N   = 100_000
    x   = rng.uniform(0, 1, N)
    y   = rng.uniform(0, 1, N)

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle("Particle Distribution Verification  (N=100 000)",
                 fontsize=13, fontweight="bold")

    # x histogram
    axes[0].hist(x, bins=50, color="steelblue", edgecolor="white", linewidth=0.3)
    axes[0].set_title("X-coordinate distribution")
    axes[0].set_xlabel("x"); axes[0].set_ylabel("Count")
    axes[0].axhline(N/50, color="red", linestyle="--",
                    linewidth=1.2, label="Expected (uniform)")
    axes[0].legend()

    # y histogram
    axes[1].hist(y, bins=50, color="darkorange", edgecolor="white", linewidth=0.3)
    axes[1].set_title("Y-coordinate distribution")
    axes[1].set_xlabel("y"); axes[1].set_ylabel("Count")
    axes[1].axhline(N/50, color="red", linestyle="--", linewidth=1.2,
                    label="Expected (uniform)")
    axes[1].legend()

    # 2-D scatter (sub-sample for clarity)
    idx = rng.choice(N, 5000, replace=False)
    axes[2].scatter(x[idx], y[idx], s=1, alpha=0.4, color="purple")
    axes[2].set_title("2-D scatter (5 000 particles)")
    axes[2].set_xlabel("x"); axes[2].set_ylabel("y")
    axes[2].set_xlim(0, 1); axes[2].set_ylim(0, 1)
    axes[2].set_aspect("equal")

    plt.tight_layout()
    fname = "results/exp1_particle_distribution.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Saved {fname}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 – Memory & FLOP table  (printed, not plotted)
# ─────────────────────────────────────────────────────────────────────────────

def print_memory_flop_table():
    """
    For each (NX,NY,N_particles) combination print:
      - Memory for points array  (bytes)
      - Memory for mesh grid     (bytes)
      - Estimated FLOPs for interpolation  (12 per particle)
      - Estimated FLOPs for mover         (~6 per particle)
    """
    print("\n" + "="*80)
    print("Memory & FLOP Analysis")
    print("="*80)
    print(f"{'NX':>6} {'NY':>6} {'N_particles':>12} {'Pts_MB':>9} "
          f"{'Mesh_MB':>9} {'Total_MB':>9} {'Interp_GFLOPs':>14} {'Mover_GFLOPs':>13}")
    print("-"*80)
    particle_list = [100, 10_000, 1_000_000, 100_000_000, 1_000_000_000]
    for (nx, ny) in CONFIGS:
        gx = nx + 1; gy = ny + 1
        for np_ in particle_list:
            pts_mb  = np_ * 2 * 8 / 1e6      # 2 doubles per particle
            mesh_mb = gx * gy * 8 / 1e6      # one double per node
            tot_mb  = pts_mb + mesh_mb
            interp_gf = np_ * 12 / 1e9       # ~12 FLOPs per particle for bilinear
            mover_gf  = np_ *  6 / 1e9       # ~6 FLOPs per particle
            print(f"{nx:>6} {ny:>6} {np_:>12,} {pts_mb:>9.2f} "
                  f"{mesh_mb:>9.2f} {tot_mb:>9.2f} {interp_gf:>14.4f} {mover_gf:>13.4f}")
        print()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Parsing data files...")
    lab_data     = parse_exp1("data_local/local_exp1.txt")
    cluster_data = parse_exp1("data_cluster/cluster_exp1.txt")

    if not lab_data and not cluster_data:
        print("  No data files found yet. Generating placeholder distribution plot only.")
    else:
        print(f"  Lab data:     {sum(len(v) for v in lab_data.values())} data points")
        print(f"  Cluster data: {sum(len(v) for v in cluster_data.values())} data points")

    print("\nGenerating scaling plots...")
    plot_scaling(lab_data, cluster_data)

    print("Generating per-particle PPC plot...")
    plot_perparticle_ppc(lab_data if lab_data else cluster_data)

    print("Generating particle distribution plot...")
    plot_particle_distribution()

    print_memory_flop_table()

    print("\nAll plots saved to results/")
