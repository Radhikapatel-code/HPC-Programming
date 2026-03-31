import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Fix: always save relative to script location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
os.makedirs(RESULTS_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────
# PARSER
# ─────────────────────────────────────────────────────────

def parse_exp2(filepath):
    data = {}

    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return data

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split(",")

            if len(parts) != 8:
                continue

            try:
                nx       = int(parts[0])
                ny       = int(parts[1])
                approach = parts[2].strip()
                nthreads = int(parts[3])
                t_in     = float(parts[4])
                t_mv     = float(parts[5])
                t_tot    = float(parts[6])   # ✅ TOTAL RUNTIME
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


# ─────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────

CONFIGS  = [(250, 100), (500, 200), (1000, 400)]
THREADS  = [2, 4, 8, 16]

APPROACHES = {
    "No_Del(A4)": ("Assignment 04 (No Ins/Del)", "steelblue",  "o", "--"),
    "Deferred":   ("Deferred Insertion",          "darkorange", "s", "-"),
    "Immediate":  ("Immediate Replacement",       "seagreen",   "^", "-"),
}


# ─────────────────────────────────────────────────────────
# SPEEDUP
# ─────────────────────────────────────────────────────────

def plot_speedup(data, label_suffix):

    for (nx, ny) in CONFIGS:

        if (nx, ny) not in data:
            continue

        fig, ax = plt.subplots(figsize=(7, 5))

        ax.set_title(f"Speedup ({label_suffix}) NX={nx}, NY={ny}")
        ax.set_xlabel("Threads")
        ax.set_ylabel("Speedup")
        ax.set_xticks(THREADS)
        ax.grid(True, linestyle="--", alpha=0.5)

        # ideal line
        ideal_x = np.array(THREADS)
        ideal_y = ideal_x / 2.0
        ax.plot(ideal_x, ideal_y, linestyle=":", label="Ideal")

        cfg = data[(nx, ny)]

        for key, (label, color, marker, ls) in APPROACHES.items():
            if key not in cfg:
                continue

            a = cfg[key]

            xs, ys = [], []
            for t in THREADS:
                if t in a:
                    xs.append(t)
                    ys.append(a[t][3])  # speedup

            ax.plot(xs, ys, marker=marker, linestyle=ls,
                    linewidth=2, markersize=7, label=label)

        ax.legend(fontsize=9)
        plt.tight_layout()

        fname = os.path.join(RESULTS_DIR,
                 f"exp2_speedup_NX{nx}_NY{ny}_{label_suffix}.png")
        plt.savefig(fname, dpi=150)
        plt.close()

        print("Saved", fname)


# ─────────────────────────────────────────────────────────
# RUNTIME (FIXED)
# ─────────────────────────────────────────────────────────

def plot_runtime(lab_data, cluster_data):

    for (nx, ny) in CONFIGS:

        fig, axes = plt.subplots(1, 2, figsize=(13, 5))

        for ax, (name, data) in zip(
            axes,
            [("Lab PC", lab_data), ("HPC Cluster", cluster_data)]
        ):

            ax.set_title(name)
            ax.set_xlabel("Threads")
            ax.set_ylabel("Total Runtime (s)")
            ax.set_xticks(THREADS)
            ax.grid(True)

            if (nx, ny) not in data:
                ax.text(0.5, 0.5, "No data", ha="center")
                continue

            cfg = data[(nx, ny)]

            for key, (label, color, marker, ls) in APPROACHES.items():

                if key not in cfg:
                    continue

                a = cfg[key]

                xs, ys = [], []

                for t in THREADS:
                    if t in a:
                        xs.append(t)
                        ys.append(float(a[t][2]))  # ✅ FORCE TOTAL RUNTIME

                # 🔥 DEBUG PRINT
                print(f"[DEBUG] {name} {nx},{ny} {key} →", ys)

                ax.plot(xs, ys,
                        marker=marker,
                        linestyle=ls,
                        linewidth=2,
                        markersize=7,
                        label=label)

            ax.legend(fontsize=9)

        plt.tight_layout()

        fname = os.path.join(RESULTS_DIR,
                 f"exp2_runtime_NX{nx}_NY{ny}.png")
        plt.savefig(fname, dpi=150)
        plt.close()

        print("Saved", fname)


# ─────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":

    print("Parsing...")

    lab_data     = parse_exp2("../data_lab/output_exp2.txt")
    cluster_data = parse_exp2("../data_cluster/cluster_exp2.txt")

    print("Lab:", lab_data.keys())
    print("Cluster:", cluster_data.keys())

    if not lab_data and not cluster_data:
        print("No data found.")
        exit()

    plot_speedup(lab_data, "lab")
    plot_speedup(cluster_data, "cluster")

    plot_runtime(lab_data, cluster_data)

    print("\nDone. Check results folder.")