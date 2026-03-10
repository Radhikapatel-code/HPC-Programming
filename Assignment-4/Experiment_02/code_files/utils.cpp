#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>
#include "utils.h"

// Interpolation (Serial Code)
void interpolation(double *mesh_value, Points *points) {


    int i, j;
    double x, y;
    double fx, fy;
    double w00, w10, w01, w11;
    for(int ptr=0 ; ptr<(GRID_X*GRID_Y) ; ptr++){
        mesh_value[ptr] = 0.00;
    }

    for (int p = 0; p < NUM_Points; p++) {

        x = points[p].x;
        y = points[p].y;

        // find which cell particle lies in
        i = (int)(x / dx);
        j = (int)(y / dy);

        // handle boundary case
        if (i >= NX) i = NX - 1;
        if (j >= NY) j = NY - 1;

        // local coordinates inside cell
        fx = (x - i * dx) / dx;
        fy = (y - j * dy) / dy;

        // bilinear weights
        w00 = (1 - fx) * (1 - fy);
        w10 = fx * (1 - fy);
        w01 = (1 - fx) * fy;
        w11 = fx * fy;

        // update mesh (1D flattened indexing)
        mesh_value[j * GRID_X + i] += w00;
        mesh_value[j * GRID_X + (i+1)] += w10;
        mesh_value[(j+1) * GRID_X + i] += w01;
        mesh_value[(j+1) * GRID_X + (i+1)] += w11;
    }
}

// Stochastic Mover (Serial Code) 
void mover_serial(Points *points, double deltaX, double deltaY) {

    for(long i = 0; i < NUM_Points; i++) {

        double new_x, new_y;
        double rand_dx, rand_dy;

        do {
            rand_dx = ((double)rand() / RAND_MAX) * 2.0 * deltaX - deltaX;
            rand_dy = ((double)rand() / RAND_MAX) * 2.0 * deltaY - deltaY;

            new_x = points[i].x + rand_dx;
            new_y = points[i].y + rand_dy;

        } while (new_x < 0.0 || new_x > 1.0 ||
                 new_y < 0.0 || new_y > 1.0);

        points[i].x = new_x;
        points[i].y = new_y;
    }
}


// Stochastic Mover (Parallel Code) 
void mover_parallel(Points *points, double deltaX, double deltaY) {

    #pragma omp parallel for
    for(long i = 0; i < NUM_Points; i++) {

        unsigned int seed = omp_get_thread_num() + i;

        double new_x, new_y;
        double rand_dx, rand_dy;

        do {
            rand_dx = ((double)rand_r(&seed) / RAND_MAX) * 2.0 * deltaX - deltaX;
            rand_dy = ((double)rand_r(&seed) / RAND_MAX) * 2.0 * deltaY - deltaY;

            new_x = points[i].x + rand_dx;
            new_y = points[i].y + rand_dy;

        } while (new_x < 0.0 || new_x > 1.0 ||
                 new_y < 0.0 || new_y > 1.0);

        points[i].x = new_x;
        points[i].y = new_y;
    }
}


// Write mesh to file
void save_mesh(double *mesh_value) {

    FILE *fd = fopen("Mesh.out", "w");
    if (!fd) {
        printf("Error creating Mesh.out\n");
        exit(1);
    }

    for (int i = 0; i < GRID_Y; i++) {
        for (int j = 0; j < GRID_X; j++) {
            fprintf(fd, "%lf ", mesh_value[i * GRID_X + j]);
        }
        fprintf(fd, "\n");
    }

    fclose(fd);
}