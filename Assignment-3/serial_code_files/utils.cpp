#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "utils.h"

// Serial interpolation 
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