#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

#include "init.h"
#include "utils.h"

int GRID_X, GRID_Y, NX, NY;
int NUM_Points, Maxiter;
double dx, dy;

int main() {

    int configs[3][2] = {
        {250, 100},
        {500, 200},
        {1000, 400}
    };

    long particle_list[5] = {
        100,
        10000,
        1000000,
        100000000,
        1000000000

    };

    Maxiter = 10;

    for (int c = 0; c < 3; c++) {

        NX = configs[c][0];
        NY = configs[c][1];

        GRID_X = NX + 1;
        GRID_Y = NY + 1;

        dx = 1.0 / NX;
        dy = 1.0 / NY;

        printf("\nCONFIG %d (NX=%d NY=%d)\n", c+1, NX, NY);
        printf("Particles\tTotal_Interp_Time\n");

        for (int p = 0; p < 5; p++) {

            NUM_Points = particle_list[p];

            double *mesh_value = (double*)calloc(GRID_X*GRID_Y, sizeof(double));
            Points *points = (Points*)calloc(NUM_Points, sizeof(Points));

            if (!mesh_value || !points) {
                printf("Memory fail at %ld particles\n", NUM_Points);
                continue;
            }

            double total_interp = 0.0;

            for (int iter = 0; iter < Maxiter; iter++) {

                initializepoints(points);
                memset(mesh_value, 0, GRID_X*GRID_Y*sizeof(double));

                double start = omp_get_wtime();
                interpolation(mesh_value, points);
                double t = omp_get_wtime() - start;

                total_interp += t;
            }

            printf("%ld\t%lf\n", NUM_Points, total_interp);

            free(mesh_value);
            free(points);
        }
    }

    return 0;
}
