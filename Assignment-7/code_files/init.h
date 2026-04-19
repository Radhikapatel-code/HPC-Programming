#ifndef INIT_H
#define INIT_H

#include <stdio.h>

// ─────────────────────────────────────────────────────────────
//  Global variables (defined in main.cpp, extern everywhere else)
// ─────────────────────────────────────────────────────────────
extern int GRID_X, GRID_Y, NX, NY;
extern int NUM_Points, Maxiter;
extern double dx, dy;

// ─────────────────────────────────────────────────────────────
//  Particle / Point data structure
// ─────────────────────────────────────────────────────────────
typedef struct {
    double x;       // x-coordinate
    double y;       // y-coordinate
    double f;       // function value (always 1.0 for this assignment)
    int    active;  // 1 = active, 0 = inactive (moved outside domain)
} Points;

// ─────────────────────────────────────────────────────────────
//  Function declarations
// ─────────────────────────────────────────────────────────────

/* Read scattered points from already-opened binary file */
void read_points(FILE *file, Points *points);

/* Scatter interpolation: particles → mesh  (with atomic/reduction) */
void interpolation(double *mesh_value, Points *points);

/* Normalize mesh values to [-1, 1] */
void normalization(double *mesh_value);

/* Reverse interpolation (gather): mesh → particles, then move */
void mover(double *mesh_value, Points *points);

/* Denormalize mesh values back to original range */
void denormalization(double *mesh_value);

/* Write mesh to output file */
void save_mesh(double *mesh_value);

/* Count inactive (void) particles */
long long void_count(Points *points);

#endif /* INIT_H */