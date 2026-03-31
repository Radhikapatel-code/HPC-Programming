/*
 * main_exp1.cpp  –  Assignment 05  |  Experiment 01
 *
 * Purpose:
 *   Measure how serial mover execution time (with insertion/deletion) scales
 *   with the number of particles, for three grid configurations.
 *
 * Output:
 *   Prints a CSV-style table:  NX, NY, NUM_Points, Total_Interp_Time,
 *   Total_Mover_Deferred_Time, Total_Mover_Immediate_Time, Deletions_per_iter
 *
 *   Results are printed for BOTH approaches so they can be plotted together.
 *
 * Compile:
 *   g++ -O2 -fopenmp -o exp1 main_exp1.cpp init.cpp utils.cpp
 *
 * Run:
 *   ./exp1
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

#include "init.h"
#include "utils.h"

/* ── Global simulation parameters (extern in init.h / utils.h) ─────────── */
int    GRID_X, GRID_Y, NX, NY;
int    NUM_Points, Maxiter;
double dx, dy;

/* ── Grid configurations ─────────────────────────────────────────────────── */
static const int N_CONFIGS   = 3;
static const int configs[3][2] = { {250,100}, {500,200}, {1000,400} };

/* ── Particle counts ─────────────────────────────────────────────────────── */
static const int N_SIZES     = 5;
static const long particle_sizes[5] = { 100L, 10000L, 1000000L,
                                         100000000L, 1000000000L };

/* =========================================================================
   MAIN
   ========================================================================= */
int main() {

    Maxiter = 10;

    printf("# Assignment 05 – Experiment 01  (Serial Mover with Ins/Del)\n");
    printf("# NX,NY,NUM_Points,Total_Interp,Total_Deferred,Total_Immediate,"
           "Avg_Deletions_per_iter\n");

    for (int c = 0; c < N_CONFIGS; c++) {

        NX     = configs[c][0];
        NY     = configs[c][1];
        GRID_X = NX + 1;
        GRID_Y = NY + 1;
        dx     = 1.0 / NX;
        dy     = 1.0 / NY;

        printf("\n# ── CONFIG %d  NX=%d  NY=%d ─────────────────────\n",
               c+1, NX, NY);
        printf("# NX,NY,NUM_Points,Total_Interp,Total_Deferred,"
               "Total_Immediate,Avg_Deletions_per_iter\n");

        for (int p = 0; p < N_SIZES; p++) {

            NUM_Points = (int)particle_sizes[p];

            /* Memory estimate: 2 runs of points + mesh */
            long mem_needed = 2L * NUM_Points * sizeof(Points)
                            + (long)GRID_X * GRID_Y * sizeof(double);

            if (mem_needed > 14L * 1024 * 1024 * 1024) {   /* >14 GB – skip */
                printf("%d,%d,%ld,SKIP,SKIP,SKIP,SKIP  # not enough RAM\n",
                       NX, NY, particle_sizes[p]);
                fflush(stdout);
                continue;
            }

            /* ── allocate two independent point arrays (one per approach) ─ */
            Points *pts_def = (Points *)malloc(NUM_Points * sizeof(Points));
            Points *pts_imm = (Points *)malloc(NUM_Points * sizeof(Points));
            double *mesh    = (double *)calloc(GRID_X * GRID_Y, sizeof(double));

            if (!pts_def || !pts_imm || !mesh) {
                printf("%d,%d,%ld,ALLOC_FAIL,ALLOC_FAIL,ALLOC_FAIL,0\n",
                       NX, NY, particle_sizes[p]);
                free(pts_def); free(pts_imm); free(mesh);
                fflush(stdout);
                continue;
            }

            /* ── Initialise ONCE outside the iteration loop ──────────── */
            srand(42);
            initializepoints(pts_def);
            /* Copy same initial state to pts_imm for fair comparison */
            memcpy(pts_imm, pts_def, NUM_Points * sizeof(Points));

            /* ── Accumulate timings across Maxiter iterations ──────────  */
            double total_interp   = 0.0;
            double total_deferred = 0.0;
            double total_immediate= 0.0;
            long   total_deleted  = 0;

            for (int iter = 0; iter < Maxiter; iter++) {

                /* ── Interpolation (uses pts_def as representative) ──── */
                memset(mesh, 0, GRID_X * GRID_Y * sizeof(double));
                double t0 = omp_get_wtime();
                interpolation(mesh, pts_def);
                total_interp += omp_get_wtime() - t0;

                /* ── Deferred insertion mover ──────────────────────────  */
                int deleted_d = 0;
                t0 = omp_get_wtime();
                mover_deferred_serial(pts_def, dx, dy, &deleted_d);
                total_deferred += omp_get_wtime() - t0;
                total_deleted  += deleted_d;

                /* ── Immediate replacement mover ───────────────────────  */
                int deleted_i = 0;
                t0 = omp_get_wtime();
                mover_immediate_serial(pts_imm, dx, dy, &deleted_i);
                total_immediate += omp_get_wtime() - t0;
            }

            double avg_del = (double)total_deleted / Maxiter;

            printf("%d,%d,%ld,%.6f,%.6f,%.6f,%.1f\n",
                   NX, NY, particle_sizes[p],
                   total_interp, total_deferred, total_immediate, avg_del);
            fflush(stdout);

            free(pts_def);
            free(pts_imm);
            free(mesh);
        }
    }

    printf("\n# Done.\n");
    return 0;
}
