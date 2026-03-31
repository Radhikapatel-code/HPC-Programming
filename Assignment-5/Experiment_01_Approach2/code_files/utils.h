#ifndef UTILS_H
#define UTILS_H

#include "init.h"

// ─── Interpolation ─────────────────────────────────────────────────────────
void interpolation(double *mesh_value, Points *points);

// ─── Mover: DEFERRED INSERTION approach ────────────────────────────────────
//   Phase 1 – Move all particles; particles leaving domain are marked deleted.
//   Phase 2 – New random particles are inserted at the freed memory slots.
void mover_deferred_serial  (Points *points, double deltaX, double deltaY, int *out_deleted);
void mover_deferred_parallel(Points *points, double deltaX, double deltaY, int *out_deleted);

// ─── Mover: IMMEDIATE REPLACEMENT approach ─────────────────────────────────
//   For every particle that exits the domain it is instantly replaced with a
//   new random particle at the same memory index.
void mover_immediate_serial  (Points *points, double deltaX, double deltaY, int *out_deleted);
void mover_immediate_parallel(Points *points, double deltaX, double deltaY, int *out_deleted);

// ─── Mover from Assignment 04 (no insertion/deletion) – used for comparison ──
void mover_no_del_parallel(Points *points, double deltaX, double deltaY);

// ─── I/O ───────────────────────────────────────────────────────────────────
void save_mesh(double *mesh_value);

#endif
