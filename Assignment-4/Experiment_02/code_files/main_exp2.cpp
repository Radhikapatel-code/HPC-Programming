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

    NUM_Points = 100000000;   // 1e8
    Maxiter = 10;

    printf("ProblemIndex\tTotal_Interp_Time\n");

    for (int c = 0; c < 3; c++) {

        NX = configs[c][0];
        NY = configs[c][1];

        GRID_X = NX + 1;
        GRID_Y = NY + 1;

        dx = 1.0 / NX;
        dy = 1.0 / NY;

        double *mesh_value = (double*)calloc(GRID_X*GRID_Y, sizeof(double));
        Points *points = (Points*)calloc(NUM_Points, sizeof(Points));

        if (!mesh_value || !points) {
            printf("Memory allocation failed\n");
            return 1;
        }

        // Initialize ONLY ONCE
        initializepoints(points);

        double total_interp = 0.0;

        for (int iter = 0; iter < Maxiter; iter++) {

            memset(mesh_value, 0, GRID_X*GRID_Y*sizeof(double));

            double start = omp_get_wtime();
            interpolation(mesh_value, points);
            double t = omp_get_wtime() - start;

            total_interp += t;
        }

        printf("%d\t%lf\n", c+1, total_interp);

        free(mesh_value);
        free(points);
    }

    return 0;
}
