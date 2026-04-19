"""
Enhanced HPC Results Plotter — with cluster comparison
Assignment 6 - OpenMP Bilinear Interpolation
Usage: python3 plot_results_final.py
Place results.csv (local) and results_cluster.csv (cluster) in same directory.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 11,
    'axes.titlesize': 13, 'axes.titleweight': 'bold',
    'axes.spines.top': False, 'axes.spines.right': False,
    'figure.dpi': 150, 'axes.grid': True,
    'grid.alpha': 0.3, 'grid.linestyle': '--',
})

COLORS = ['#378ADD', '#1D9E75', '#D85A30', '#D4537E', '#7F77DD']
LOCAL_COLOR  = '#378ADD'
CLUSTER_COLOR = '#1D9E75'

SERIAL_LOCAL = {
    '0.9M': 0.028971, '5M': 0.165851,
    '3.6M': 0.127530, '20M': 0.924769, '14M': 1.643468,
}

df_local   = pd.read_csv('results.csv')
df_cluster = pd.read_csv('results_cluster.csv')

configs = ['0.9M', '5M', '3.6M', '20M', '14M']
threads_local   = [2, 4, 8, 16]
threads_cluster = [1, 2, 4, 8, 16]

def get_times(df, cfg, thread_list):
    d = df[df['Configuration'] == cfg].sort_values('Threads')
    return [d[d['Threads'] == t]['Time(s)'].values[0] for t in thread_list if t in d['Threads'].values]

# ── Fig 1: Local execution time ────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
for i, cfg in enumerate(configs):
    t = get_times(df_local, cfg, threads_local)
    ax.plot(threads_local[:len(t)], t, marker='o', label=cfg, color=COLORS[i], linewidth=2)
ax.set_xlabel('Number of Threads')
ax.set_ylabel('Execution Time (s)')
ax.set_title('Local Machine: Execution Time vs Thread Count')
ax.set_xticks(threads_local)
ax.legend(title='Dataset', bbox_to_anchor=(1.01,1), loc='upper left')
plt.tight_layout()
plt.savefig('fig1_local_time.png', dpi=200, bbox_inches='tight')
plt.close(); print("Saved fig1_local_time.png")

# ── Fig 2: Local speedup vs serial ────────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot([1]+threads_local, [1]+threads_local, 'k--', alpha=0.2, linewidth=1.5, label='Ideal')
for i, cfg in enumerate(configs):
    t = get_times(df_local, cfg, threads_local)
    sp = [SERIAL_LOCAL[cfg] / x for x in t]
    ax.plot(threads_local[:len(sp)], sp, marker='o', label=cfg, color=COLORS[i], linewidth=2)
ax.set_xlabel('Number of Threads')
ax.set_ylabel('Speedup')
ax.set_title('Local Machine: Speedup vs Serial Baseline')
ax.set_xticks(threads_local)
ax.legend(title='Dataset', bbox_to_anchor=(1.01,1), loc='upper left')
plt.tight_layout()
plt.savefig('fig2_local_speedup.png', dpi=200, bbox_inches='tight')
plt.close(); print("Saved fig2_local_speedup.png")

# ── Fig 3: Cluster speedup vs serial ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(threads_cluster, threads_cluster, 'k--', alpha=0.2, linewidth=1.5, label='Ideal')
for i, cfg in enumerate(configs):
    t = get_times(df_cluster, cfg, threads_cluster)
    t1 = t[0]
    sp = [t1 / x for x in t]
    ax.plot(threads_cluster[:len(sp)], sp, marker='o', label=cfg, color=COLORS[i], linewidth=2)
ax.set_xlabel('Number of Threads')
ax.set_ylabel('Speedup')
ax.set_title('Cluster (Xeon E5-2620 v3): Speedup vs Serial Baseline')
ax.set_xticks(threads_cluster)
ax.legend(title='Dataset', bbox_to_anchor=(1.01,1), loc='upper left')
plt.tight_layout()
plt.savefig('fig3_cluster_speedup.png', dpi=200, bbox_inches='tight')
plt.close(); print("Saved fig3_cluster_speedup.png")

# ── Fig 4: Local parallel efficiency ──────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
for i, cfg in enumerate(configs):
    t = get_times(df_local, cfg, threads_local)
    sp = [SERIAL_LOCAL[cfg] / x for x in t]
    eff = [s / th * 100 for s, th in zip(sp, threads_local)]
    ax.plot(threads_local[:len(eff)], eff, marker='o', label=cfg, color=COLORS[i], linewidth=2)
ax.axhline(100, color='gray', linestyle='--', alpha=0.3, linewidth=1)
ax.set_xlabel('Number of Threads')
ax.set_ylabel('Parallel Efficiency (%)')
ax.set_title('Local Machine: Parallel Efficiency')
ax.set_xticks(threads_local); ax.set_ylim(0, 115)
ax.legend(title='Dataset', bbox_to_anchor=(1.01,1), loc='upper left')
plt.tight_layout()
plt.savefig('fig4_local_efficiency.png', dpi=200, bbox_inches='tight')
plt.close(); print("Saved fig4_local_efficiency.png")

# ── Fig 5: Cluster parallel efficiency ────────────────────────────────────
fig, ax = plt.subplots(figsize=(8, 5))
for i, cfg in enumerate(configs):
    t = get_times(df_cluster, cfg, threads_cluster)
    t1 = t[0]
    sp = [t1 / x for x in t]
    eff = [s / th * 100 for s, th in zip(sp, threads_cluster)]
    ax.plot(threads_cluster[:len(eff)], eff, marker='o', label=cfg, color=COLORS[i], linewidth=2)
ax.axhline(100, color='gray', linestyle='--', alpha=0.3, linewidth=1)
ax.set_xlabel('Number of Threads')
ax.set_ylabel('Parallel Efficiency (%)')
ax.set_title('Cluster: Parallel Efficiency')
ax.set_xticks(threads_cluster); ax.set_ylim(0, 115)
ax.legend(title='Dataset', bbox_to_anchor=(1.01,1), loc='upper left')
plt.tight_layout()
plt.savefig('fig5_cluster_efficiency.png', dpi=200, bbox_inches='tight')
plt.close(); print("Saved fig5_cluster_efficiency.png")

# ── Fig 6: Local vs Cluster speedup side-by-side ──────────────────────────
common_threads = [2, 4, 8, 16]
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
axes = axes.flatten()
for i, cfg in enumerate(configs):
    ax = axes[i]
    lt = get_times(df_local, cfg, common_threads)
    ct_all = get_times(df_cluster, cfg, threads_cluster)
    ct = get_times(df_cluster, cfg, common_threads)
    l_sp = [SERIAL_LOCAL[cfg] / x for x in lt]
    c_sp = [ct_all[0] / x for x in ct]
    ax.plot(common_threads, l_sp, marker='o', color=LOCAL_COLOR, label='Local', linewidth=2)
    ax.plot(common_threads, c_sp, marker='s', color=CLUSTER_COLOR, label='Cluster', linewidth=2)
    ax.set_title(cfg); ax.set_xticks(common_threads)
    ax.set_xlabel('Threads'); ax.set_ylabel('Speedup')
    ax.legend(fontsize=9)

axes[5].set_visible(False)
fig.suptitle('Local vs Cluster Speedup Comparison (vs each system\'s serial baseline)', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('fig6_local_vs_cluster.png', dpi=200, bbox_inches='tight')
plt.close(); print("Saved fig6_local_vs_cluster.png")

# ── Fig 7: Degradation bar — 4T to 16T ───────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
for ax, (df, label, thr) in zip(axes, [
    (df_local, 'Local machine', threads_local),
    (df_cluster, 'Cluster (gics0)', threads_cluster)
]):
    pct = []
    for cfg in configs:
        t = get_times(df, cfg, thr)
        t4  = t[thr.index(4)]
        t16 = t[thr.index(16)]
        pct.append((t16 - t4) / t4 * 100)
    bars = ax.bar(configs, pct, color=COLORS, width=0.5)
    ax.axhline(0, color='black', linewidth=0.8)
    for bar, val in zip(bars, pct):
        lbl = f'+{val:.1f}%' if val >= 0 else f'{val:.1f}%'
        ypos = bar.get_height() + 1 if val >= 0 else bar.get_height() - 8
        ax.text(bar.get_x()+bar.get_width()/2, ypos, lbl, ha='center', fontsize=9)
    ax.set_title(label); ax.set_xlabel('Dataset'); ax.set_ylabel('% time change (4T → 16T)')
plt.suptitle('Scaling regression: 4 threads to 16 threads', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('fig7_degradation.png', dpi=200, bbox_inches='tight')
plt.close(); print("Saved fig7_degradation.png")

# ── Fig 8: Heatmaps ───────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 4))
for ax, (df, label, thr) in zip(axes, [
    (df_local, 'Local machine', threads_local),
    (df_cluster, 'Cluster (gics0)', threads_cluster)
]):
    matrix = np.array([[get_times(df, cfg, thr)[thr.index(t)] for t in thr] for cfg in configs])
    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
    ax.set_xticks(range(len(thr))); ax.set_xticklabels([f'{t}T' for t in thr])
    ax.set_yticks(range(len(configs))); ax.set_yticklabels(configs)
    ax.set_title(f'{label} — Time (s)')
    for i in range(len(configs)):
        for j in range(len(thr)):
            ax.text(j, i, f'{matrix[i,j]:.3f}', ha='center', va='center', fontsize=8,
                    color='white' if matrix[i,j] > matrix.max()*0.5 else 'black')
    plt.colorbar(im, ax=ax, label='Time (s)')
plt.tight_layout()
plt.savefig('fig8_heatmaps.png', dpi=200, bbox_inches='tight')
plt.close(); print("Saved fig8_heatmaps.png")

print("\nAll 8 figures saved!")
print("\n=== Speedup Summary (Cluster) ===")
print(f"{'Config':<8}", end='')
for t in threads_cluster: print(f"  {t}T", end='')
print()
for cfg in configs:
    t_all = get_times(df_cluster, cfg, threads_cluster)
    t1 = t_all[0]
    print(f"{cfg:<8}", end='')
    for t in t_all: print(f"  {t1/t:>5.2f}x", end='')
    print()