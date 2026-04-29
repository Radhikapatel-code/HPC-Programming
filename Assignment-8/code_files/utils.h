#ifndef UTILS_H
#define UTILS_H

#include "init.h"
#include <math.h>

// ─────────────────────────────────────────────────────────────
//  Bilinear weight helpers
//  Given a particle at (px, py), compute the four corner indices
//  and the four weights for bilinear (area-weighted) interpolation.
//
//  Grid cell:
//    (ci,   cj+1) ─── (ci+1, cj+1)
//        |                |
//    (ci,   cj  ) ─── (ci+1, cj  )
//
//  Weights are proportional to the *opposite* rectangular area:
//    w_ij      = (dx - lx) * (dy - ly)
//    w_(i+1)j  = lx        * (dy - ly)
//    w_i(j+1)  = (dx - lx) * ly
//    w_(i+1)(j+1) = lx     * ly
// ─────────────────────────────────────────────────────────────

static inline void compute_weights(double px, double py,
                                   int *ci, int *cj,
                                   double *w00, double *w10,
                                   double *w01, double *w11)
{
    /* cell indices */
    *ci = (int)(px / dx);
    *cj = (int)(py / dy);

    /* clamp to valid cell range */
    if (*ci >= NX) *ci = NX - 1;
    if (*cj >= NY) *cj = NY - 1;
    if (*ci < 0)   *ci = 0;
    if (*cj < 0)   *cj = 0;

    /* fractional distances from lower-left corner of cell */
    double lx = px - (*ci) * dx;
    double ly = py - (*cj) * dy;

    *w00 = (dx - lx) * (dy - ly);   /* (ci,   cj  ) */
    *w10 = lx        * (dy - ly);   /* (ci+1, cj  ) */
    *w01 = (dx - lx) * ly;          /* (ci,   cj+1) */
    *w11 = lx        * ly;          /* (ci+1, cj+1) */
}


/* 2-D index helper: row = cj, col = ci  (row-major, GRID_X columns) */
static inline int IDX(int ci, int cj)
{
    return cj * GRID_X + ci;
}

#endif /* UTILS_H */