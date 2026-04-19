/*
 * main.cpp  –  Entry point for HPC Assignment 07
 *
 * Timing uses omp_get_wtime() when compiled with OpenMP (wall-clock),
 * and clock() for the pure serial build.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "init.h"
#include "utils.h"

#ifdef _OPENMP
#  include <omp.h>
#  define GET_TIME() omp_get_wtime()
#else
#  include <time.h>
#  define GET_TIME() ((double)clock() / CLOCKS_PER_SEC)
#endif

/* Global variables (extern declared in init.h) */
int    GRID_X, GRID_Y, NX, NY;
int    NUM_Points, Maxiter;
double dx, dy;

int main(int argc, char **argv)
{
    if (argc != 2) {
        printf("Usage: %s <input_file>\n", argv[0]);
        return 1;
    }

    FILE *file = fopen(argv[1], "rb");
    if (!file) { printf("Error opening input file\n"); return 1; }

    if (fread(&NX,         sizeof(int), 1, file) != 1 ||
        fread(&NY,         sizeof(int), 1, file) != 1 ||
        fread(&NUM_Points, sizeof(int), 1, file) != 1 ||
        fread(&Maxiter,    sizeof(int), 1, file) != 1) {
        printf("Error reading header\n"); return 1;
    }

    GRID_X = NX + 1;
    GRID_Y = NY + 1;
    dx     = 1.0 / NX;
    dy     = 1.0 / NY;

    printf("Grid: %dx%d | Particles: %d | Iterations: %d\n",
           NX, NY, NUM_Points, Maxiter);
#ifdef _OPENMP
    printf("OpenMP threads: %d\n", omp_get_max_threads());
#else
    printf("Serial build\n");
#endif

    double *mesh_value = (double *)calloc(GRID_X * GRID_Y, sizeof(double));
    Points *points     = (Points *)malloc(NUM_Points * sizeof(Points));
    if (!mesh_value || !points) {
        printf("Memory allocation failed\n"); return 1;
    }

    read_points(file, points);
    fclose(file);

    double total_int_time    = 0.0;
    double total_norm_time   = 0.0;
    double total_move_time   = 0.0;
    double total_denorm_time = 0.0;

    for (int iter = 0; iter < Maxiter; iter++) {
        double t0 = GET_TIME();
        interpolation(mesh_value, points);
        double t1 = GET_TIME();

        normalization(mesh_value);
        double t2 = GET_TIME();

        mover(mesh_value, points);
        double t3 = GET_TIME();

        denormalization(mesh_value);
        double t4 = GET_TIME();

        total_int_time    += t1 - t0;
        total_norm_time   += t2 - t1;
        total_move_time   += t3 - t2;
        total_denorm_time += t4 - t3;
    }

    save_mesh(mesh_value);

    printf("Total Interpolation Time   = %.6f seconds\n", total_int_time);
    printf("Total Normalization Time   = %.6f seconds\n", total_norm_time);
    printf("Total Mover Time           = %.6f seconds\n", total_move_time);
    printf("Total Denormalization Time = %.6f seconds\n", total_denorm_time);
    printf("Total Algorithm Time       = %.6f seconds\n",
           total_int_time + total_norm_time + total_move_time + total_denorm_time);
    printf("Total Number of Voids      = %lld\n", void_count(points));

    free(mesh_value);
    free(points);
    return 0;
}