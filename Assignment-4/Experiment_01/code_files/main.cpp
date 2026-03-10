#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

#include "init.h"
#include "utils.h"

// Global variables
int GRID_X, GRID_Y, NX, NY;
int NUM_Points, Maxiter;
double dx, dy;

int main() {

    // ===== Experiment 03 Parameters =====
    NX = 1000;
    NY = 400;
    NUM_Points = 14000000;   // 14 million
    Maxiter = 10;

    GRID_X = NX + 1;
    GRID_Y = NY + 1;

    dx = 1.0 / NX;
    dy = 1.0 / NY;

    // Allocate memory
    double *mesh_value = (double *) calloc(GRID_X * GRID_Y, sizeof(double));
    Points *points = (Points *) calloc(NUM_Points, sizeof(Points));

    if (!mesh_value || !points) {
        printf("Memory allocation failed!\n");
        return 1;
    }

    // Initialize particles ONLY ONCE (as required)
    initializepoints(points);

    printf("Iter\tInterp\t\tMover\t\tTotal\n");
    omp_set_num_threads(4);


    for (int iter = 0; iter < Maxiter; iter++) {

        // Clear mesh every iteration
        memset(mesh_value, 0, GRID_X * GRID_Y * sizeof(double));

      // ===== Interpolation Timing =====
double start_interp = omp_get_wtime();
interpolation(mesh_value, points);
double interp_time = omp_get_wtime() - start_interp;

// Prevent compiler optimization
volatile double checksum = 0.0;
for (long i = 0; i < GRID_X * GRID_Y; i++)
    checksum += mesh_value[i];

// ===== Mover Timing =====
double start_move = omp_get_wtime();
mover_parallel(points, dx, dy);

double move_time = omp_get_wtime() - start_move;

double total = interp_time + move_time;

printf("%d\t%lf\t%lf\t%lf\tChecksum=%lf\n",
       iter + 1, interp_time, move_time, total, checksum);

    }

    free(mesh_value);
    free(points);

    return 0;
}
