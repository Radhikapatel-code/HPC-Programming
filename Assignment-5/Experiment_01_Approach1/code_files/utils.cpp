/*
 * utils.cpp  –  Assignment 05
 *
 * Contains:
 *   - interpolation           (serial, same as Assignment 04)
 *   - mover_deferred_serial   (Approach 1, serial)
 *   - mover_deferred_parallel (Approach 1, OpenMP)
 *   - mover_immediate_serial  (Approach 2, serial)
 *   - mover_immediate_parallel(Approach 2, OpenMP)
 *   - mover_no_del_parallel   (Assignment 04 mover for speedup comparison)
 *   - save_mesh
 */

#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include "utils.h"

/* =========================================================================
   HELPER: generate a double in [0, 1) using a per-thread reentrant seed.
   ========================================================================= */
static inline double rand01(unsigned int *seed) {
    return (double)rand_r(seed) / (double)RAND_MAX;
}

/* =========================================================================
   INTERPOLATION  (serial bilinear scatter – unchanged from Assignment 04)
   ========================================================================= */
void interpolation(double *mesh_value, Points *points) {

    /* Zero the mesh */
    for (int ptr = 0; ptr < GRID_X * GRID_Y; ptr++)
        mesh_value[ptr] = 0.0;

    for (int p = 0; p < NUM_Points; p++) {

        double x = points[p].x;
        double y = points[p].y;

        int i = (int)(x / dx);
        int j = (int)(y / dy);

        if (i >= NX) i = NX - 1;
        if (j >= NY) j = NY - 1;

        double fx = (x - i * dx) / dx;
        double fy = (y - j * dy) / dy;

        double w00 = (1.0 - fx) * (1.0 - fy);
        double w10 =        fx  * (1.0 - fy);
        double w01 = (1.0 - fx) *        fy;
        double w11 =        fx  *        fy;

        mesh_value[ j      * GRID_X +  i   ] += w00;
        mesh_value[ j      * GRID_X + (i+1)] += w10;
        mesh_value[(j+1)   * GRID_X +  i   ] += w01;
        mesh_value[(j+1)   * GRID_X + (i+1)] += w11;
    }
}

/* =========================================================================
   APPROACH 1 – DEFERRED INSERTION  (serial)
   ─────────────────────────────────────────
   Phase 1: Move every particle.  If it leaves [0,1]x[0,1], mark it with
            sentinel value -2.0 and count the deletion.
   Phase 2: A single linear scan re-fills every sentinel slot with a new
            random position inside the domain.
   ========================================================================= */
void mover_deferred_serial(Points *points, double deltaX, double deltaY,
                           int *out_deleted)
{
    int deleted = 0;

    /* ── Phase 1: move & mark ─────────────────────────────────────────── */
    for (int i = 0; i < NUM_Points; i++) {

        double rand_dx = ((double)rand() / RAND_MAX) * 2.0 * deltaX - deltaX;
        double rand_dy = ((double)rand() / RAND_MAX) * 2.0 * deltaY - deltaY;

        double new_x = points[i].x + rand_dx;
        double new_y = points[i].y + rand_dy;

        if (new_x < 0.0 || new_x > 1.0 || new_y < 0.0 || new_y > 1.0) {
            points[i].x = -2.0;   /* sentinel = "void slot" */
            points[i].y = -2.0;
            deleted++;
        } else {
            points[i].x = new_x;
            points[i].y = new_y;
        }
    }

    /* ── Phase 2: insert new particles at void slots ─────────────────── */
    for (int i = 0; i < NUM_Points; i++) {
        if (points[i].x == -2.0) {
            points[i].x = (double)rand() / RAND_MAX;
            points[i].y = (double)rand() / RAND_MAX;
        }
    }

    *out_deleted = deleted;
}

/* =========================================================================
   APPROACH 1 – DEFERRED INSERTION  (parallel)
   ─────────────────────────────────────────────
   Phase 1 runs in parallel with OpenMP.  Each thread uses a private seed
   (rand_r) so there are no race conditions.  A reduction counts deletions.
   Phase 2 also runs in parallel – each thread handles its own chunk and
   only writes to its own indices, so no synchronization is needed.
   ========================================================================= */
void mover_deferred_parallel(Points *points, double deltaX, double deltaY,
                             int *out_deleted)
{
    int deleted = 0;

    /* ── Phase 1: parallel move & mark ───────────────────────────────── */
    #pragma omp parallel for reduction(+:deleted) schedule(static)
    for (int i = 0; i < NUM_Points; i++) {

        unsigned int seed = (unsigned int)(omp_get_thread_num() * 999983 + i);

        double rand_dx = rand01(&seed) * 2.0 * deltaX - deltaX;
        double rand_dy = rand01(&seed) * 2.0 * deltaY - deltaY;

        double new_x = points[i].x + rand_dx;
        double new_y = points[i].y + rand_dy;

        if (new_x < 0.0 || new_x > 1.0 || new_y < 0.0 || new_y > 1.0) {
            points[i].x = -2.0;
            points[i].y = -2.0;
            deleted++;
        } else {
            points[i].x = new_x;
            points[i].y = new_y;
        }
    }

    /* ── Phase 2: parallel re-insertion at void slots ────────────────── */
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < NUM_Points; i++) {
        if (points[i].x == -2.0) {
            /* unique seed per slot so different threads produce different positions */
            unsigned int seed = (unsigned int)(omp_get_thread_num() * 999983
                                               + i + 777777);
            points[i].x = rand01(&seed);
            points[i].y = rand01(&seed);
        }
    }

    *out_deleted = deleted;
}

/* =========================================================================
   APPROACH 2 – IMMEDIATE REPLACEMENT  (serial)
   ──────────────────────────────────────────────
   If a particle leaves the domain it is replaced on the spot with a
   freshly drawn random position.  No deferred bookkeeping needed.
   ========================================================================= */
void mover_immediate_serial(Points *points, double deltaX, double deltaY,
                            int *out_deleted)
{
    int deleted = 0;

    for (int i = 0; i < NUM_Points; i++) {

        double rand_dx = ((double)rand() / RAND_MAX) * 2.0 * deltaX - deltaX;
        double rand_dy = ((double)rand() / RAND_MAX) * 2.0 * deltaY - deltaY;

        double new_x = points[i].x + rand_dx;
        double new_y = points[i].y + rand_dy;

        if (new_x < 0.0 || new_x > 1.0 || new_y < 0.0 || new_y > 1.0) {
            /* Immediately insert a replacement particle */
            points[i].x = (double)rand() / RAND_MAX;
            points[i].y = (double)rand() / RAND_MAX;
            deleted++;
        } else {
            points[i].x = new_x;
            points[i].y = new_y;
        }
    }

    *out_deleted = deleted;
}

/* =========================================================================
   APPROACH 2 – IMMEDIATE REPLACEMENT  (parallel)
   ────────────────────────────────────────────────
   Perfectly parallel: each thread only reads/writes points[i] for its own
   i.  No atomics, no synchronisation, no false sharing issues.
   ========================================================================= */
void mover_immediate_parallel(Points *points, double deltaX, double deltaY,
                              int *out_deleted)
{
    int deleted = 0;

    #pragma omp parallel for reduction(+:deleted) schedule(static)
    for (int i = 0; i < NUM_Points; i++) {

        unsigned int seed = (unsigned int)(omp_get_thread_num() * 999983 + i);

        double rand_dx = rand01(&seed) * 2.0 * deltaX - deltaX;
        double rand_dy = rand01(&seed) * 2.0 * deltaY - deltaY;

        double new_x = points[i].x + rand_dx;
        double new_y = points[i].y + rand_dy;

        if (new_x < 0.0 || new_x > 1.0 || new_y < 0.0 || new_y > 1.0) {
            unsigned int seed2 = seed + 424242;
            points[i].x = rand01(&seed2);
            points[i].y = rand01(&seed2);
            deleted++;
        } else {
            points[i].x = new_x;
            points[i].y = new_y;
        }
    }

    *out_deleted = deleted;
}

/* =========================================================================
   ASSIGNMENT 04 MOVER  (no insertion/deletion)
   Used in Experiment 02 to draw the "without ins/del" speedup curve.
   ========================================================================= */
void mover_no_del_parallel(Points *points, double deltaX, double deltaY) {

    #pragma omp parallel for schedule(static)
    for (int i = 0; i < NUM_Points; i++) {

        unsigned int seed = (unsigned int)(omp_get_thread_num() + i);
        double new_x, new_y;

        do {
            double rand_dx = rand01(&seed) * 2.0 * deltaX - deltaX;
            double rand_dy = rand01(&seed) * 2.0 * deltaY - deltaY;
            new_x = points[i].x + rand_dx;
            new_y = points[i].y + rand_dy;
        } while (new_x < 0.0 || new_x > 1.0 || new_y < 0.0 || new_y > 1.0);

        points[i].x = new_x;
        points[i].y = new_y;
    }
}

/* =========================================================================
   SAVE MESH
   ========================================================================= */
void save_mesh(double *mesh_value) {
    FILE *fd = fopen("Mesh.out", "w");
    if (!fd) { printf("Error creating Mesh.out\n"); return; }

    for (int i = 0; i < GRID_Y; i++) {
        for (int j = 0; j < GRID_X; j++)
            fprintf(fd, "%lf ", mesh_value[i * GRID_X + j]);
        fprintf(fd, "\n");
    }
    fclose(fd);
}
