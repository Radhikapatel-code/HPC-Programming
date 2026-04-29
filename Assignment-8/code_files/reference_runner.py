#!/usr/bin/env python3
"""
Reference runner for Assignment 08.

This script reproduces the serial algorithm in Python so we can generate
correctness artifacts when native compilation is unavailable locally.
It is intended only for correctness/reference outputs, not performance data.
"""

from __future__ import annotations

import argparse
import math
import struct
from pathlib import Path
from time import perf_counter


def read_input(path: Path):
    data = path.read_bytes()
    nx, ny, num_points, maxiter = struct.unpack_from("4i", data, 0)
    points = []
    offset = 16
    for _ in range(num_points):
        x, y, f = struct.unpack_from("3d", data, offset)
        points.append([x, y, f, 1])
        offset += 24
    return nx, ny, num_points, maxiter, points


def idx(ci: int, cj: int, grid_x: int) -> int:
    return cj * grid_x + ci


def compute_weights(px: float, py: float, dx: float, dy: float, nx: int, ny: int):
    ci = int(px / dx)
    cj = int(py / dy)

    if ci >= nx:
        ci = nx - 1
    if cj >= ny:
        cj = ny - 1
    if ci < 0:
        ci = 0
    if cj < 0:
        cj = 0

    lx = px - ci * dx
    ly = py - cj * dy

    w00 = (dx - lx) * (dy - ly)
    w10 = lx * (dy - ly)
    w01 = (dx - lx) * ly
    w11 = lx * ly
    return ci, cj, w00, w10, w01, w11


def interpolation(mesh_value, points, grid_x, grid_y, dx, dy, nx, ny):
    for i in range(grid_x * grid_y):
        mesh_value[i] = 0.0

    for x, y, f, active in points:
        if not active:
            continue
        ci, cj, w00, w10, w01, w11 = compute_weights(x, y, dx, dy, nx, ny)
        mesh_value[idx(ci, cj, grid_x)] += w00 * f
        mesh_value[idx(ci + 1, cj, grid_x)] += w10 * f
        mesh_value[idx(ci, cj + 1, grid_x)] += w01 * f
        mesh_value[idx(ci + 1, cj + 1, grid_x)] += w11 * f


def normalization(mesh_value):
    mn = min(mesh_value)
    mx = max(mesh_value)
    value_range = mx - mn
    if value_range < 1e-15:
        value_range = 1.0
    for i, value in enumerate(mesh_value):
        mesh_value[i] = 2.0 * (value - mn) / value_range - 1.0
    return mn, mx


def mover(mesh_value, points, grid_x, dx, dy, nx, ny):
    for point in points:
        if not point[3]:
            continue
        ci, cj, w00, w10, w01, w11 = compute_weights(point[0], point[1], dx, dy, nx, ny)
        field_value = (
            w00 * mesh_value[idx(ci, cj, grid_x)]
            + w10 * mesh_value[idx(ci + 1, cj, grid_x)]
            + w01 * mesh_value[idx(ci, cj + 1, grid_x)]
            + w11 * mesh_value[idx(ci + 1, cj + 1, grid_x)]
        )
        point[0] += field_value * dx
        point[1] += field_value * dy
        if point[0] < 0.0 or point[0] > 1.0 or point[1] < 0.0 or point[1] > 1.0:
            point[3] = 0


def denormalization(mesh_value, mn, mx):
    value_range = mx - mn
    if value_range < 1e-15:
        value_range = 1.0
    for i, value in enumerate(mesh_value):
        mesh_value[i] = (value + 1.0) * 0.5 * value_range + mn


def save_mesh(mesh_value, grid_x, grid_y, path: Path):
    with path.open("w", encoding="utf-8") as handle:
        for j in range(grid_y):
            row = mesh_value[j * grid_x : (j + 1) * grid_x]
            handle.write(" ".join(f"{value:.6f}" for value in row))
            handle.write("\n")


def void_count(points) -> int:
    return sum(1 for point in points if not point[3])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stdout-log", type=Path, required=True)
    args = parser.parse_args()

    nx, ny, num_points, maxiter, points = read_input(args.input_file)
    grid_x = nx + 1
    grid_y = ny + 1
    dx = 1.0 / nx
    dy = 1.0 / ny
    mesh_value = [0.0] * (grid_x * grid_y)

    total_int_time = 0.0
    total_norm_time = 0.0
    total_move_time = 0.0
    total_denorm_time = 0.0

    for _ in range(maxiter):
        t0 = perf_counter()
        interpolation(mesh_value, points, grid_x, grid_y, dx, dy, nx, ny)
        t1 = perf_counter()

        mn, mx = normalization(mesh_value)
        t2 = perf_counter()

        mover(mesh_value, points, grid_x, dx, dy, nx, ny)
        t3 = perf_counter()

        denormalization(mesh_value, mn, mx)
        t4 = perf_counter()

        total_int_time += t1 - t0
        total_norm_time += t2 - t1
        total_move_time += t3 - t2
        total_denorm_time += t4 - t3

    save_mesh(mesh_value, grid_x, grid_y, args.output)

    stdout_lines = [
        f"Grid: {nx}x{ny} | Particles: {num_points} | Iterations: {maxiter}",
        "MPI ranks: 1 (python reference)",
        f"Mesh saved to {args.output.name}  ({grid_x} x {grid_y} grid)",
        f"Total Interpolation Time   = {total_int_time:.6f} seconds",
        f"Total Normalization Time   = {total_norm_time:.6f} seconds",
        f"Total Mover Time           = {total_move_time:.6f} seconds",
        f"Total Denormalization Time = {total_denorm_time:.6f} seconds",
        (
            "Total Algorithm Time       = "
            f"{(total_int_time + total_norm_time + total_move_time + total_denorm_time):.6f} seconds"
        ),
        f"Total Number of Voids      = {void_count(points)}",
    ]
    args.stdout_log.write_text("\n".join(stdout_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
