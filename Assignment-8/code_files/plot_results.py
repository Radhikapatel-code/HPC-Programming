#!/usr/bin/env python3
"""
plot_results.py

Reads cluster timing CSV files from data_cluster/ and generates SVG plots
without external plotting dependencies.
"""

import csv
import os


CONFIGS = {
    "a": "Nx=250, Ny=100, 0.9M pts",
    "b": "Nx=250, Ny=100, 5M pts",
    "c": "Nx=500, Ny=200, 3.6M pts",
    "d": "Nx=500, Ny=200, 20M pts",
    "e": "Nx=1000, Ny=400, 14M pts",
}

DATA_DIR = "data_cluster"
RESULTS_DIR = "results"
COLORS = ["#0f766e", "#dc2626", "#2563eb", "#7c3aed", "#ea580c"]


def load_csv(path):
    cores = []
    times = []
    speedups = []
    efficiencies = []

    with open(path, newline="") as handle:
        rows = list(csv.DictReader(handle))

    if not rows:
        return cores, times, speedups, efficiencies

    if "TotalCores" in rows[0]:
        for row in rows:
            total_cores = int(row["TotalCores"])
            serial_time = float(row["SerialTime_s"])
            parallel_time = float(row["TotalAlgorithmTime_s"])

            cores.append(total_cores)
            times.append(parallel_time)
            speedup = serial_time / parallel_time
            speedups.append(speedup)
            efficiencies.append(speedup / total_cores)
    elif "Threads" in rows[0]:
        serial_time = None
        for row in rows:
            total_cores = int(row["Threads"])
            parallel_time = float(row["TotalAlgorithmTime_s"])
            if total_cores == 1:
                serial_time = parallel_time
            cores.append(total_cores)
            times.append(parallel_time)

        if serial_time is None and times:
            serial_time = times[0]

        for total_cores, parallel_time in zip(cores, times):
            speedup = serial_time / parallel_time
            speedups.append(speedup)
            efficiencies.append(speedup / max(total_cores, 1))
    else:
        raise KeyError(f"Unsupported CSV format in {path}")

    return cores, times, speedups, efficiencies


def svg_line_chart(path, title, y_label, series, x_ticks, ideal_points=None):
    width = 920
    height = 560
    margin_left = 80
    margin_right = 220
    margin_top = 60
    margin_bottom = 70
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    all_y = []
    for _, _, ys in series:
        all_y.extend(ys)
    if ideal_points:
        all_y.extend(y for _, y in ideal_points)

    y_min = 0.0
    y_max = max(all_y) if all_y else 1.0
    if y_max <= y_min:
        y_max = y_min + 1.0
    y_max *= 1.08

    x_min = min(x_ticks)
    x_max = max(x_ticks)

    def sx(x):
        if x_max == x_min:
            return margin_left + plot_w / 2.0
        return margin_left + (x - x_min) * plot_w / (x_max - x_min)

    def sy(y):
        return margin_top + plot_h - (y - y_min) * plot_h / (y_max - y_min)

    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    parts.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    parts.append(f'<text x="{width/2:.1f}" y="30" text-anchor="middle" font-size="20" font-family="Arial" fill="#111827">{title}</text>')

    for tick in range(6):
        y_value = y_min + (y_max - y_min) * tick / 5.0
        y_pos = sy(y_value)
        parts.append(f'<line x1="{margin_left}" y1="{y_pos:.2f}" x2="{margin_left + plot_w}" y2="{y_pos:.2f}" stroke="#e5e7eb" stroke-width="1"/>')
        parts.append(f'<text x="{margin_left - 10}" y="{y_pos + 4:.2f}" text-anchor="end" font-size="11" font-family="Arial" fill="#374151">{y_value:.2f}</text>')

    for x in x_ticks:
        x_pos = sx(x)
        parts.append(f'<line x1="{x_pos:.2f}" y1="{margin_top}" x2="{x_pos:.2f}" y2="{margin_top + plot_h}" stroke="#f3f4f6" stroke-width="1"/>')
        parts.append(f'<text x="{x_pos:.2f}" y="{margin_top + plot_h + 22}" text-anchor="middle" font-size="11" font-family="Arial" fill="#374151">{x}</text>')

    parts.append(f'<line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{margin_left + plot_w}" y2="{margin_top + plot_h}" stroke="#111827" stroke-width="1.5"/>')
    parts.append(f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" stroke="#111827" stroke-width="1.5"/>')
    parts.append(f'<text x="{margin_left + plot_w/2:.1f}" y="{height - 20}" text-anchor="middle" font-size="13" font-family="Arial" fill="#111827">Total Cores / Threads</text>')
    parts.append(f'<text x="24" y="{margin_top + plot_h/2:.1f}" text-anchor="middle" font-size="13" font-family="Arial" fill="#111827" transform="rotate(-90 24 {margin_top + plot_h/2:.1f})">{y_label}</text>')

    if ideal_points:
        poly = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in ideal_points)
        parts.append(f'<polyline points="{poly}" fill="none" stroke="#111827" stroke-width="1.5" stroke-dasharray="6 4"/>')

    legend_y = margin_top + 10
    legend_x = margin_left + plot_w + 20
    if ideal_points:
        parts.append(f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 18}" y2="{legend_y}" stroke="#111827" stroke-width="1.5" stroke-dasharray="6 4"/>')
        parts.append(f'<text x="{legend_x + 26}" y="{legend_y + 4}" font-size="11" font-family="Arial" fill="#111827">Ideal</text>')
        legend_y += 20

    for label, color, ys in series:
        poly = " ".join(f"{sx(x):.2f},{sy(y):.2f}" for x, y in zip(x_ticks, ys))
        parts.append(f'<polyline points="{poly}" fill="none" stroke="{color}" stroke-width="2.5"/>')
        for x, y in zip(x_ticks, ys):
            parts.append(f'<circle cx="{sx(x):.2f}" cy="{sy(y):.2f}" r="3.2" fill="{color}"/>')
        parts.append(f'<line x1="{legend_x}" y1="{legend_y}" x2="{legend_x + 18}" y2="{legend_y}" stroke="{color}" stroke-width="2.5"/>')
        parts.append(f'<text x="{legend_x + 26}" y="{legend_y + 4}" font-size="11" font-family="Arial" fill="#111827">{label}</text>')
        legend_y += 20

    parts.append("</svg>")

    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(parts))


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)

    all_data = {}
    for key in CONFIGS:
        csv_path = os.path.join(DATA_DIR, f"timing_{key}_cluster.csv")
        if os.path.exists(csv_path):
            all_data[key] = load_csv(csv_path)

    if not all_data:
        print("No cluster timing CSVs found in data_cluster/.")
        raise SystemExit(1)

    x_ticks = sorted({core for cores, _, _, _ in all_data.values() for core in cores})
    exec_series = []
    speedup_series = []
    eff_series = []

    for idx, key in enumerate(CONFIGS):
        if key not in all_data:
            continue
        cores, times, speedups, efficiencies = all_data[key]
        color = COLORS[idx % len(COLORS)]
        label = CONFIGS[key]
        exec_series.append((label, color, times))
        speedup_series.append((label, color, speedups))
        eff_series.append((label, color, efficiencies))

    svg_line_chart(
        os.path.join(RESULTS_DIR, "exec_time_cluster.svg"),
        "Execution Time vs Total Cores",
        "Execution Time (s)",
        exec_series,
        x_ticks,
    )
    print("Saved results/exec_time_cluster.svg")

    svg_line_chart(
        os.path.join(RESULTS_DIR, "speedup_cluster.svg"),
        "Speedup vs Total Cores",
        "Speedup",
        speedup_series,
        x_ticks,
        ideal_points=[(x, x) for x in x_ticks],
    )
    print("Saved results/speedup_cluster.svg")

    svg_line_chart(
        os.path.join(RESULTS_DIR, "efficiency_cluster.svg"),
        "Parallel Efficiency vs Total Cores",
        "Efficiency",
        eff_series,
        x_ticks,
        ideal_points=[(x, 1.0) for x in x_ticks],
    )
    print("Saved results/efficiency_cluster.svg")


if __name__ == "__main__":
    main()
