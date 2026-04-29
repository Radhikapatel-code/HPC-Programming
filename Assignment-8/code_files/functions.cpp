/*
 * functions.cpp  –  Serial implementation
 *
 * Contains:
 *   read_points()     – load particles from binary file
 *   interpolation()   – scatter: particle → grid  (bilinear)
 *   normalization()   – normalize grid to [-1, 1]
 *   mover()           – gather: grid → particle, then update positions
 *   denormalization() – restore grid to original range
 *   save_mesh()       – write grid to output file
 *   void_count()      – count inactive particles
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <math.h>
#include "init.h"
#include "utils.h"

/* ─── module-level state for norm / denorm ─────────────────────────── */
static double g_mesh_min = 0.0;
static double g_mesh_max = 1.0;

/* ─────────────────────────────────────────────────────────────────────
 * read_points
 * Binary layout (from inputFileMaker.c):
 *   NX  NY  NUM_Points  Maxiter   (4 × int, read in main)
 *   then NUM_Points × { x, y, f } (3 × double each)
 * ──────────────────────────────────────────────────────────────────── */
void read_points(FILE *file, Points *points)
{
    for (int i = 0; i < NUM_Points; i++) {
        fread(&points[i].x, sizeof(double), 1, file);
        fread(&points[i].y, sizeof(double), 1, file);
        fread(&points[i].f, sizeof(double), 1, file);
        points[i].active = 1;
    }
}

/* ─────────────────────────────────────────────────────────────────────
 * interpolation  (scatter: particle → grid)
 *
 * For each active particle, compute the four bilinear weights and
 * accumulate  f_i × w  onto the four surrounding grid nodes.
 * ──────────────────────────────────────────────────────────────────── */
void interpolation(double *mesh_value, Points *points)
{
    /* Reset grid */
    memset(mesh_value, 0, GRID_X * GRID_Y * sizeof(double));

    for (int p = 0; p < NUM_Points; p++) {
        if (!points[p].active) continue;

        int ci, cj;
        double w00, w10, w01, w11;
        compute_weights(points[p].x, points[p].y,
                        &ci, &cj,
                        &w00, &w10, &w01, &w11);

        double fi = points[p].f;

        mesh_value[IDX(ci,     cj    )] += w00 * fi;
        mesh_value[IDX(ci + 1, cj    )] += w10 * fi;
        mesh_value[IDX(ci,     cj + 1)] += w01 * fi;
        mesh_value[IDX(ci + 1, cj + 1)] += w11 * fi;
    }
}

/* ─────────────────────────────────────────────────────────────────────
 * normalization
 *
 * Scale grid values linearly so that they lie in [-1, 1].
 * Saves min/max for denormalization.
 * ──────────────────────────────────────────────────────────────────── */
void normalization(double *mesh_value)
{
    int N = GRID_X * GRID_Y;

    double mn =  DBL_MAX;
    double mx = -DBL_MAX;
    for (int i = 0; i < N; i++) {
        if (mesh_value[i] < mn) mn = mesh_value[i];
        if (mesh_value[i] > mx) mx = mesh_value[i];
    }
    g_mesh_min = mn;
    g_mesh_max = mx;

    double range = mx - mn;
    if (range < 1e-15) range = 1.0;   /* avoid division by zero */

    for (int i = 0; i < N; i++) {
        mesh_value[i] = 2.0 * (mesh_value[i] - mn) / range - 1.0;
    }
}

/* ─────────────────────────────────────────────────────────────────────
 * mover  (gather: grid → particle  +  position update)
 *
 * For each active particle:
 *   1. Recompute bilinear weights (same cell as scatter).
 *   2. Gather field value F_i from four grid nodes.
 *   3. Update position:  x += F_i * dx,  y += F_i * dy
 *   4. If particle leaves [0, 1) × [0, 1): mark inactive.
 * ──────────────────────────────────────────────────────────────────── */
void mover(double *mesh_value, Points *points)
{
    for (int p = 0; p < NUM_Points; p++) {
        if (!points[p].active) continue;

        int ci, cj;
        double w00, w10, w01, w11;
        compute_weights(points[p].x, points[p].y,
                        &ci, &cj,
                        &w00, &w10, &w01, &w11);

        /* gather field at particle location */
        double Fi = w00 * mesh_value[IDX(ci,     cj    )]
                  + w10 * mesh_value[IDX(ci + 1, cj    )]
                  + w01 * mesh_value[IDX(ci,     cj + 1)]
                  + w11 * mesh_value[IDX(ci + 1, cj + 1)];

        /* update position */
        points[p].x += Fi * dx;
        points[p].y += Fi * dy;

        /* deactivate if outside domain [0, 1] */
        if (points[p].x < 0.0 || points[p].x > 1.0 ||
            points[p].y < 0.0 || points[p].y > 1.0) {
            points[p].active = 0;
        }
    }
}

/* ─────────────────────────────────────────────────────────────────────
 * denormalization
 *
 * Reverse the normalization step using the saved min/max.
 * ──────────────────────────────────────────────────────────────────── */
void denormalization(double *mesh_value)
{
    int N = GRID_X * GRID_Y;
    double range = g_mesh_max - g_mesh_min;
    if (range < 1e-15) range = 1.0;

    for (int i = 0; i < N; i++) {
        mesh_value[i] = (mesh_value[i] + 1.0) * 0.5 * range + g_mesh_min;
    }
}

/* ─────────────────────────────────────────────────────────────────────
 * save_mesh
 *
 * Write the final grid values to "output.txt" (one value per line).
 * ──────────────────────────────────────────────────────────────────── */
void save_mesh(double *mesh_value)
{
    FILE *fp = fopen("output.txt", "w");
    if (!fp) {
        printf("Error: cannot create output.txt\n");
        return;
    }

    for (int j = 0; j < GRID_Y; j++) {           // y - rows
        for (int i = 0; i < GRID_X; i++) {       // x - columns
            fprintf(fp, "%.6f", mesh_value[j * GRID_X + i]);
            if (i < GRID_X - 1)
                fprintf(fp, " ");
            else
                fprintf(fp, "\n");
        }
    }
    fclose(fp);
    printf("✅ Mesh saved to output.txt  (%d x %d grid)\n", GRID_X, GRID_Y);
}
/* ─────────────────────────────────────────────────────────────────────
 * void_count
 *
 * Return the number of inactive (void) particles.
 * ──────────────────────────────────────────────────────────────────── */
long long void_count(Points *points)
{
    long long count = 0;
    for (int i = 0; i < NUM_Points; i++) {
        if (!points[i].active) count++;
    }
    return count;
}