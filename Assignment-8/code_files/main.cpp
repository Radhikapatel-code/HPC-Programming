/*
 * main.cpp - Shared entry point for serial and MPI builds.
 *
 * Serial build:
 *   g++ ... main.cpp functions.cpp
 *
 * MPI build:
 *   mpicxx ... -DUSE_MPI main.cpp functions_parallel.cpp
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef USE_MPI
#include <mpi.h>
#define GET_TIME() MPI_Wtime()
#else
#include <omp.h>
#define GET_TIME() omp_get_wtime()
#endif

#include "init.h"
#include "utils.h"

/* Global variables (extern declared in init.h) */
int    GRID_X, GRID_Y, NX, NY;
int    NUM_Points, Maxiter;
double dx, dy;

int main(int argc, char **argv)
{
    int rank = 0;
    int size = 1;

#ifdef USE_MPI
    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
#endif

    if (argc != 2) {
        if (rank == 0) printf("Usage: %s <input_file>\n", argv[0]);
#ifdef USE_MPI
        MPI_Finalize();
#endif
        return 1;
    }

    FILE *file = fopen(argv[1], "rb");
    if (!file) {
        if (rank == 0) printf("Error opening input file\n");
#ifdef USE_MPI
        MPI_Finalize();
#endif
        return 1;
    }

    if (fread(&NX,         sizeof(int), 1, file) != 1 ||
        fread(&NY,         sizeof(int), 1, file) != 1 ||
        fread(&NUM_Points, sizeof(int), 1, file) != 1 ||
        fread(&Maxiter,    sizeof(int), 1, file) != 1) {
        if (rank == 0) printf("Error reading header\n");
        fclose(file);
#ifdef USE_MPI
        MPI_Finalize();
#endif
        return 1;
    }

    GRID_X = NX + 1;
    GRID_Y = NY + 1;
    dx     = 1.0 / NX;
    dy     = 1.0 / NY;

    if (rank == 0) {
        printf("Grid: %dx%d | Particles: %d | Iterations: %d\n",
               NX, NY, NUM_Points, Maxiter);
#ifdef USE_MPI
        printf("MPI ranks: %d\n", size);
#else
        printf("MPI ranks: 1 (serial baseline)\n");
#endif
    }

    double *mesh_value = (double *)calloc((size_t)GRID_X * (size_t)GRID_Y, sizeof(double));

    int point_capacity = NUM_Points;
#ifdef USE_MPI
    {
        int base = NUM_Points / size;
        int rem  = NUM_Points % size;
        point_capacity = base + (rank < rem ? 1 : 0);
    }
#endif
    if (point_capacity < 1) point_capacity = 1;

    Points *points = (Points *)malloc((size_t)point_capacity * sizeof(Points));
    if (!mesh_value || !points) {
        if (rank == 0) printf("Memory allocation failed\n");
        fclose(file);
#ifdef USE_MPI
        MPI_Finalize();
#endif
        return 1;
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
    long long total_voids = void_count(points);

    if (rank == 0) {
        printf("Total Interpolation Time   = %.6f seconds\n", total_int_time);
        printf("Total Normalization Time   = %.6f seconds\n", total_norm_time);
        printf("Total Mover Time           = %.6f seconds\n", total_move_time);
        printf("Total Denormalization Time = %.6f seconds\n", total_denorm_time);
        printf("Total Algorithm Time       = %.6f seconds\n",
               total_int_time + total_norm_time + total_move_time + total_denorm_time);
        printf("Total Number of Voids      = %lld\n", total_voids);
    }

    free(mesh_value);
    free(points);

#ifdef USE_MPI
    MPI_Finalize();
#endif
    return 0;
}
