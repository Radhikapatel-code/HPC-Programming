#ifndef UTILS_H
#define UTILS_H

#include "init.h"

// Serial
void interpolation(double *mesh_value, Points *points);

// Parallel v1 — atomic
void interpolation_parallel_atomic(double *mesh_value, Points *points, int num_threads);

// Parallel v2 — private mesh + serial critical reduction
void interpolation_parallel_private(double *mesh_value, Points *points, int num_threads);

// Parallel v3 — private mesh + PARALLEL reduction (recommended: fastest)
void interpolation_parallel_private_v2(double *mesh_value, Points *points, int num_threads);

// Stubs (compatibility with older headers)
void mover_deferred_serial (Points *points, double deltaX, double deltaY, int *out_deleted);
void mover_deferred_parallel(Points *points, double deltaX, double deltaY, int *out_deleted);
void mover_immediate_serial (Points *points, double deltaX, double deltaY, int *out_deleted);
void mover_immediate_parallel(Points *points, double deltaX, double deltaY, int *out_deleted);
void mover_no_del_parallel(Points *points, double deltaX, double deltaY);
void save_mesh(double *mesh_value);

#endif
