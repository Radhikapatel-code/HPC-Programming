/*
* functions_parallel.cpp – Optimized OpenMP parallel implementation
*
* Bugs fixed vs. original:
* ─────────────────────────────────────────────────────────────────────
* BUG 1 (CRITICAL – wrong results): Private grid reset used
* #pragma omp for, which distributes indices [0..N) across threads.
* Thread T zeroed only the slice [T*N/nT .. (T+1)*N/nT) of ITS OWN
* private grid – leaving the rest dirty. Fixed: each thread calls
* memset on its entire private grid independently.
*
* BUG 2: save_mesh wrote one value per line instead of space-separated
* rows to match the reference output format.
*
* BUG 3: main.cpp used clock() (CPU time × threads) instead of
* omp_get_wtime() for wall-clock timing (fixed in main.cpp).
*
* Performance features retained / improved:
* ─────────────────────────────────────────────────────────────────────
* • Private grids allocated ONCE and reused (no per-call malloc/free).
* • NUMA first-touch: each thread initialises its own pages.
* • Reduction loop uses #pragma omp simd for SIMD vectorisation.
* • Particle-index compaction: active indices packed before mover to
* eliminate branch mispredictions and improve load balance.
* • Normalization / denormalization: parallel min/max reduction.
*/

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <math.h>
#include <omp.h>
#include "init.h"
#include "utils.h"

/* ── Module-level persistent state ─────────────────────────────────── */
static double g_mesh_min = 0.0;
static double g_mesh_max = 1.0;
static double **g_private_grids = NULL; /* allocated once, reused */
static int g_nthreads = 0;

/* ── One-time allocation with NUMA first-touch ─────────────────────── */
static void init_private_grids(void)
{
    if (g_private_grids != NULL) return; /* already done */

    int N = GRID_X * GRID_Y;

#pragma omp parallel
    {
#pragma omp single
        {
            g_nthreads = omp_get_num_threads();
            g_private_grids = (double **)malloc(g_nthreads * sizeof(double *));
            for (int t = 0; t < g_nthreads; t++)
                g_private_grids[t] = (double *)malloc(N * sizeof(double));
        }

        /*
         * NUMA first-touch: each thread writes its OWN entire private
         * grid so the OS places those pages on the local NUMA node.
         */
        int tid = omp_get_thread_num();
        memset(g_private_grids[tid], 0, N * sizeof(double));
    }
}

/* ── read_points (serial bulk I/O) ──────────────────────────────────── */
void read_points(FILE *file, Points *points)
{
    for (int i = 0; i < NUM_Points; i++) {
        (void)fread(&points[i].x, sizeof(double), 1, file);
        (void)fread(&points[i].y, sizeof(double), 1, file);
        (void)fread(&points[i].f, sizeof(double), 1, file);
        points[i].active = 1;
    }
}

/* ── interpolation (scatter: particle → grid) ───────────────────────── */
/*
 * Strategy: private-grid approach.
 * 1. Each thread zeros its ENTIRE private grid (no partial-zero bug).
 * 2. Each thread scatters its particle chunk into its private grid
 *    (zero contention – no atomics needed).
 * 3. A parallel reduction folds all private grids into mesh_value.
 */
void interpolation(double *mesh_value, Points *points)
{
    init_private_grids();

    int N = GRID_X * GRID_Y;
    int nthreads = g_nthreads;

#pragma omp parallel
    {
        int tid = omp_get_thread_num();
        double *lg = g_private_grids[tid];

        /* ── Step 1: zero THIS thread's entire private grid (BUG FIX) ── */
        memset(lg, 0, N * sizeof(double));
        /* No barrier needed: each thread only wrote to its own grid */

        /* ── Step 2: scatter particles into private grid ─────────────── */
#pragma omp for schedule(static) nowait
        for (int p = 0; p < NUM_Points; p++) {
            if (!points[p].active) continue;

            int ci, cj;
            double w00, w10, w01, w11;
            compute_weights(points[p].x, points[p].y,
                            &ci, &cj, &w00, &w10, &w01, &w11);

            double fi = points[p].f;
            lg[IDX(ci, cj )]     += w00 * fi;
            lg[IDX(ci + 1, cj )] += w10 * fi;
            lg[IDX(ci, cj + 1)]  += w01 * fi;
            lg[IDX(ci + 1, cj + 1)] += w11 * fi;
        }
    } /* implicit barrier – all threads done scattering */

    /* ── Step 3: parallel reduction across private grids ─────────────
     * Outer loop = grid index (sequential writes to mesh_value → no
     * false sharing among threads). Inner loop = threads (sequential
     * read → cache-friendly). SIMD on inner loop when T ≤ vector width.
     */
#pragma omp parallel for schedule(static)
    for (int i = 0; i < N; i++) {
        double sum = 0.0;
#pragma omp simd reduction(+:sum)
        for (int t = 0; t < nthreads; t++)
            sum += g_private_grids[t][i];
        mesh_value[i] = sum;
    }
}

/* ── normalization ───────────────────────────────────────────────────── */
void normalization(double *mesh_value)
{
    int N = GRID_X * GRID_Y;
    double mn = DBL_MAX;
    double mx = -DBL_MAX;

#pragma omp parallel for schedule(static) \
    reduction(min:mn) reduction(max:mx)
    for (int i = 0; i < N; i++) {
        if (mesh_value[i] < mn) mn = mesh_value[i];
        if (mesh_value[i] > mx) mx = mesh_value[i];
    }
    g_mesh_min = mn;
    g_mesh_max = mx;

    double range = mx - mn;
    if (range < 1e-15) range = 1.0;
    double inv_range = 2.0 / range;

#pragma omp parallel for schedule(static)
    for (int i = 0; i < N; i++)
        mesh_value[i] = (mesh_value[i] - mn) * inv_range - 1.0;
}

/* ── mover (gather: grid → particle + position update) ──────────────── */
/*
 * Grid is READ-ONLY → zero contention, embarrassingly parallel.
 *
 * Optimization: pack active particle indices first so the inner loop
 * has no branches and maintains sequential memory access.
 */
void mover(double *mesh_value, Points *points)
{
    /* Count active particles */
    int n_active = 0;
#pragma omp parallel for schedule(static) reduction(+:n_active)
    for (int p = 0; p < NUM_Points; p++)
        if (points[p].active) n_active++;

    /* Allocate and fill compact index array */
    int *active_idx = (int *)malloc(n_active * sizeof(int));
    int k = 0;
    for (int p = 0; p < NUM_Points; p++)
        if (points[p].active) active_idx[k++] = p;

    /* Embarrassingly parallel gather + update */
#pragma omp parallel for schedule(static)
    for (int a = 0; a < n_active; a++) {
        int p = active_idx[a];

        int ci, cj;
        double w00, w10, w01, w11;
        compute_weights(points[p].x, points[p].y,
                        &ci, &cj, &w00, &w10, &w01, &w11);

        double Fi = w00 * mesh_value[IDX(ci, cj )]
                  + w10 * mesh_value[IDX(ci + 1, cj )]
                  + w01 * mesh_value[IDX(ci, cj + 1)]
                  + w11 * mesh_value[IDX(ci + 1, cj + 1)];

        points[p].x += Fi * dx;
        points[p].y += Fi * dy;

        if (points[p].x < 0.0 || points[p].x > 1.0 ||
            points[p].y < 0.0 || points[p].y > 1.0)
            points[p].active = 0;
    }

    free(active_idx);
}

/* ── denormalization ─────────────────────────────────────────────────── */
void denormalization(double *mesh_value)
{
    int N = GRID_X * GRID_Y;
    double range = g_mesh_max - g_mesh_min;
    if (range < 1e-15) range = 1.0;
    double half_range = 0.5 * range;

#pragma omp parallel for schedule(static)
    for (int i = 0; i < N; i++)
        mesh_value[i] = (mesh_value[i] + 1.0) * half_range + g_mesh_min;
}

/* ── save_mesh ───────────────────────────────────────────────────────── */
/* BUG FIX: write space-separated values per row (matches reference fmt) */
void save_mesh(double *mesh_value)
{
    FILE *fp = fopen("output.txt", "w");
    if (!fp) { printf("Error opening output.txt\n"); return; }

    for (int j = 0; j < GRID_Y; j++) {
        for (int i = 0; i < GRID_X; i++) {
            fprintf(fp, "%.6f", mesh_value[IDX(i, j)]);
            if (i < GRID_X - 1) fputc(' ', fp);
        }
        fputc('\n', fp);
    }
    fclose(fp);
    printf("Mesh saved to output.txt (%d x %d grid)\n", GRID_X, GRID_Y);
}

/* ── void_count ──────────────────────────────────────────────────────── */
long long void_count(Points *points)
{
    long long count = 0;
#pragma omp parallel for schedule(static) reduction(+:count)
    for (int i = 0; i < NUM_Points; i++)
        if (!points[i].active) count++;
    return count;
}