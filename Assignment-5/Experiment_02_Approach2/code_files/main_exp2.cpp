/*
 * main_exp2.cpp  –  Assignment 05  |  Experiment 02
 *
 * Purpose:
 *   Study the parallel scalability of the Mover operation.
 *   Fix NUM_Points = 14,000,000.  Run with 2, 4, 8, 16 threads.
 *   Compare:
 *     (a) Parallel Mover WITH insertion/deletion  (both approaches)
 *     (b) Parallel Mover WITHOUT insertion/deletion  (Assignment 04 baseline)
 *
 * Output:
 *   CSV table:  NX,NY,Approach,Threads,Total_Interp,Total_Mover,
 *               Total_Runtime,Speedup  (relative to 2-thread run)
 *
 * Compile:
 *   g++ -O2 -fopenmp -o exp2 main_exp2.cpp init.cpp utils.cpp
 *
 * Run:
 *   ./exp2
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

#include "init.h"
#include "utils.h"

/* ── Global simulation parameters ───────────────────────────────────────── */
int    GRID_X, GRID_Y, NX, NY;
int    NUM_Points, Maxiter;
double dx, dy;

/* ── Experiment settings ─────────────────────────────────────────────────── */
static const int N_CONFIGS     = 3;
static const int configs[3][2] = { {250,100}, {500,200}, {1000,400} };
static const int FIXED_PARTICLES = 14000000;   /* 14 million */
static const int THREAD_COUNTS[] = { 2, 4, 8, 16 };
static const int N_THREADS     = 4;

/* =========================================================================
   run_experiment
   Runs Maxiter iterations with a specified approach and thread count.
   Returns total mover time (sum over all iterations).
   ========================================================================= */
static double run_experiment(Points *points, double *mesh,
                             int approach,   /* 0=no_del, 1=deferred, 2=immediate */
                             int nthreads,
                             double *out_total_interp)
{
    omp_set_num_threads(nthreads);

    /* Re-initialise particles from a fixed seed before every run so results
       are comparable across thread counts. */
    srand(42);
    initializepoints(points);

    double total_interp = 0.0;
    double total_mover  = 0.0;

    for (int iter = 0; iter < Maxiter; iter++) {

        /* Interpolation (serial) */
        memset(mesh, 0, GRID_X * GRID_Y * sizeof(double));
        double t0 = omp_get_wtime();
        interpolation(mesh, points);
        total_interp += omp_get_wtime() - t0;

        /* Mover */
        int deleted = 0;
        t0 = omp_get_wtime();
        switch (approach) {
            case 0: mover_no_del_parallel  (points, dx, dy);                break;
            case 1: mover_deferred_parallel (points, dx, dy, &deleted);     break;
            case 2: mover_immediate_parallel(points, dx, dy, &deleted);     break;
        }
        total_mover += omp_get_wtime() - t0;
    }

    *out_total_interp = total_interp;
    return total_mover;
}

/* =========================================================================
   MAIN
   ========================================================================= */
int main() {

    NUM_Points = FIXED_PARTICLES;
    Maxiter    = 10;

    printf("# Assignment 05 – Experiment 02  (Parallel Scalability)\n");
    printf("# NUM_Points=%d  Maxiter=%d\n", NUM_Points, Maxiter);
    printf("# NX,NY,Approach,Threads,Total_Interp,Total_Mover,Total_Runtime,Speedup\n\n");

    /* Allocate once – reuse across configs */
    Points *points = (Points *)malloc(NUM_Points * sizeof(Points));
    if (!points) { printf("Allocation failed!\n"); return 1; }

    for (int c = 0; c < N_CONFIGS; c++) {

        NX     = configs[c][0];
        NY     = configs[c][1];
        GRID_X = NX + 1;
        GRID_Y = NY + 1;
        dx     = 1.0 / NX;
        dy     = 1.0 / NY;

        double *mesh = (double *)calloc(GRID_X * GRID_Y, sizeof(double));
        if (!mesh) { printf("Mesh allocation failed!\n"); free(points); return 1; }

        printf("# ── CONFIG %d  NX=%d  NY=%d ─────────────────────────\n",
               c+1, NX, NY);

        /* approach names for printing */
        const char *approach_names[] = { "No_Del(A4)", "Deferred", "Immediate" };

        for (int a = 0; a < 3; a++) {

            /* Baseline mover time at 2 threads (for speedup calculation) */
            double baseline_mover = -1.0;

            for (int t = 0; t < N_THREADS; t++) {

                int nthreads = THREAD_COUNTS[t];

                double total_interp = 0.0;
                double total_mover  = run_experiment(points, mesh, a,
                                                     nthreads, &total_interp);
                double total_runtime = total_interp + total_mover;

                /* Speedup relative to the 2-thread run of the same approach */
                if (t == 0) baseline_mover = total_mover;
                double speedup = (baseline_mover > 0.0)
                                 ? baseline_mover / total_mover : 1.0;

                printf("%d,%d,%s,%d,%.6f,%.6f,%.6f,%.4f\n",
                       NX, NY, approach_names[a], nthreads,
                       total_interp, total_mover, total_runtime, speedup);
                fflush(stdout);
            }
            printf("\n");
        }

        free(mesh);
    }

    free(points);
    printf("# Done.\n");
    return 0;
}
