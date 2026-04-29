/*
 * functions_parallel.cpp - Hybrid MPI + OpenMP implementation.
 *
 * Particle ownership is distributed across MPI ranks. Each rank keeps only
 * its local particle chunk, while the mesh remains replicated so the final
 * interpolation field can be combined with MPI_Allreduce.
 *
 * Within each rank:
 *   - interpolation uses thread-private mesh buffers to avoid atomics
 *   - normalization, mover, denormalization, and void counting use OpenMP
 */

#include <float.h>
#include <math.h>
#include <mpi.h>
#include <omp.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "init.h"
#include "utils.h"

static double g_mesh_min = 0.0;
static double g_mesh_max = 1.0;

static int my_rank = -1;
static int my_size = -1;
static int local_start = 0;
static int local_count = -1;

static void init_mpi_runtime(void)
{
    if (my_rank == -1) {
        MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
        MPI_Comm_size(MPI_COMM_WORLD, &my_size);
    }
}

static void init_partition(void)
{
    init_mpi_runtime();
    if (local_count != -1) return;

    int base = NUM_Points / my_size;
    int rem  = NUM_Points % my_size;

    if (my_rank < rem) {
        local_count = base + 1;
        local_start = my_rank * (base + 1);
    } else {
        local_count = base;
        local_start = rem * (base + 1) + (my_rank - rem) * base;
    }
}

void read_points(FILE *file, Points *points)
{
    init_partition();

    const long long header_bytes = 4LL * (long long)sizeof(int);
    const long long point_bytes  = 3LL * (long long)sizeof(double);
    const long long offset = header_bytes + (long long)local_start * point_bytes;

    if (fseek(file, offset, SEEK_SET) != 0) {
        fprintf(stderr, "Rank %d: failed to seek to particle block\n", my_rank);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    for (int i = 0; i < local_count; i++) {
        if (fread(&points[i].x, sizeof(double), 1, file) != 1 ||
            fread(&points[i].y, sizeof(double), 1, file) != 1 ||
            fread(&points[i].f, sizeof(double), 1, file) != 1) {
            fprintf(stderr, "Rank %d: failed to read particle %d\n", my_rank, i);
            MPI_Abort(MPI_COMM_WORLD, 1);
        }
        points[i].active = 1;
    }
}

void interpolation(double *mesh_value, Points *points)
{
    init_partition();

    const int nmesh = GRID_X * GRID_Y;
    memset(mesh_value, 0, (size_t)nmesh * sizeof(double));

    int nthreads = omp_get_max_threads();
    double *thread_mesh = (double *)calloc((size_t)nthreads * (size_t)nmesh, sizeof(double));
    if (!thread_mesh) {
        fprintf(stderr, "Rank %d: failed to allocate thread-private mesh buffers\n", my_rank);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

#pragma omp parallel
    {
        const int tid = omp_get_thread_num();
        double *local_mesh = thread_mesh + (size_t)tid * (size_t)nmesh;

#pragma omp for schedule(static)
        for (int p = 0; p < local_count; p++) {
            if (!points[p].active) continue;

            int ci, cj;
            double w00, w10, w01, w11;
            compute_weights(points[p].x, points[p].y, &ci, &cj, &w00, &w10, &w01, &w11);

            const double fi = points[p].f;
            local_mesh[IDX(ci,     cj    )] += w00 * fi;
            local_mesh[IDX(ci + 1, cj    )] += w10 * fi;
            local_mesh[IDX(ci,     cj + 1)] += w01 * fi;
            local_mesh[IDX(ci + 1, cj + 1)] += w11 * fi;
        }
    }

#pragma omp parallel for schedule(static)
    for (int idx = 0; idx < nmesh; idx++) {
        double sum = 0.0;
        for (int tid = 0; tid < nthreads; tid++) {
            sum += thread_mesh[(size_t)tid * (size_t)nmesh + (size_t)idx];
        }
        mesh_value[idx] = sum;
    }

    free(thread_mesh);
    MPI_Allreduce(MPI_IN_PLACE, mesh_value, nmesh, MPI_DOUBLE, MPI_SUM, MPI_COMM_WORLD);
}

void normalization(double *mesh_value)
{
    init_mpi_runtime();

    const int nmesh = GRID_X * GRID_Y;
    double local_min = DBL_MAX;
    double local_max = -DBL_MAX;

#pragma omp parallel for reduction(min : local_min) reduction(max : local_max) schedule(static)
    for (int i = 0; i < nmesh; i++) {
        const double value = mesh_value[i];
        if (value < local_min) local_min = value;
        if (value > local_max) local_max = value;
    }

    MPI_Allreduce(&local_min, &g_mesh_min, 1, MPI_DOUBLE, MPI_MIN, MPI_COMM_WORLD);
    MPI_Allreduce(&local_max, &g_mesh_max, 1, MPI_DOUBLE, MPI_MAX, MPI_COMM_WORLD);

    double range = g_mesh_max - g_mesh_min;
    if (range < 1e-15) range = 1.0;
    const double scale = 2.0 / range;

#pragma omp parallel for schedule(static)
    for (int i = 0; i < nmesh; i++) {
        mesh_value[i] = (mesh_value[i] - g_mesh_min) * scale - 1.0;
    }
}

void mover(double *mesh_value, Points *points)
{
    init_partition();

#pragma omp parallel for schedule(static)
    for (int p = 0; p < local_count; p++) {
        if (!points[p].active) continue;

        int ci, cj;
        double w00, w10, w01, w11;
        compute_weights(points[p].x, points[p].y, &ci, &cj, &w00, &w10, &w01, &w11);

        const double Fi = w00 * mesh_value[IDX(ci,     cj    )]
                        + w10 * mesh_value[IDX(ci + 1, cj    )]
                        + w01 * mesh_value[IDX(ci,     cj + 1)]
                        + w11 * mesh_value[IDX(ci + 1, cj + 1)];

        points[p].x += Fi * dx;
        points[p].y += Fi * dy;

        if (points[p].x < 0.0 || points[p].x > 1.0 ||
            points[p].y < 0.0 || points[p].y > 1.0) {
            points[p].active = 0;
        }
    }
}

void denormalization(double *mesh_value)
{
    init_mpi_runtime();

    const int nmesh = GRID_X * GRID_Y;
    double range = g_mesh_max - g_mesh_min;
    if (range < 1e-15) range = 1.0;

#pragma omp parallel for schedule(static)
    for (int i = 0; i < nmesh; i++) {
        mesh_value[i] = (mesh_value[i] + 1.0) * 0.5 * range + g_mesh_min;
    }
}

void save_mesh(double *mesh_value)
{
    init_mpi_runtime();
    if (my_rank != 0) return;

    FILE *fp = fopen("output.txt", "w");
    if (!fp) {
        printf("Error: cannot create output.txt\n");
        return;
    }

    for (int j = 0; j < GRID_Y; j++) {
        for (int i = 0; i < GRID_X; i++) {
            fprintf(fp, "%.6f", mesh_value[j * GRID_X + i]);
            if (i < GRID_X - 1) {
                fprintf(fp, " ");
            } else {
                fprintf(fp, "\n");
            }
        }
    }

    fclose(fp);
    printf("Mesh saved to output.txt  (%d x %d grid)\n", GRID_X, GRID_Y);
}

long long void_count(Points *points)
{
    init_partition();

    long long local_voids = 0;

#pragma omp parallel for reduction(+ : local_voids) schedule(static)
    for (int p = 0; p < local_count; p++) {
        if (!points[p].active) local_voids++;
    }

    long long global_voids = 0;
    MPI_Allreduce(&local_voids, &global_voids, 1, MPI_LONG_LONG_INT, MPI_SUM, MPI_COMM_WORLD);
    return global_voids;
}
