#ifndef INIT_H
#define INIT_H

#include <stdio.h>

// ─── Particle structure ────────────────────────────────────────────────────
typedef struct {
    double x, y;
} Points;

// ─── Global simulation parameters (defined in main) ───────────────────────
extern int    GRID_X, GRID_Y, NX, NY;
extern int    NUM_Points, Maxiter;
extern double dx, dy;

// ─── Initialization ────────────────────────────────────────────────────────
void initializepoints(Points *points);

#endif