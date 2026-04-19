#include <cstdlib>
#include <cstdio>
#include "init.h"
#include "utils.h"
#include <chrono>

int GRID_X, GRID_Y, NX, NY;
int NUM_Points, Maxiter;
double dx, dy;

void read_binary_input(const char* filename, Points** all_points,
                       int& nx, int& ny, int& maxiter, int& numpoints) {
    FILE* fp = fopen(filename, "rb");
    if (!fp) { perror("Cannot open input.bin"); exit(1); }

    fread(&nx,       sizeof(int), 1, fp);
    fread(&ny,       sizeof(int), 1, fp);
    fread(&maxiter,  sizeof(int), 1, fp);
    fread(&numpoints,sizeof(int), 1, fp);

    GRID_X = nx; GRID_Y = ny; NX = nx; NY = ny;
    NUM_Points = numpoints; Maxiter = maxiter;
    dx = 1.0 / NX; dy = 1.0 / NY;

    *all_points = (Points*)malloc((size_t)Maxiter * NUM_Points * sizeof(Points));
    for (int iter = 0; iter < Maxiter; ++iter) {
        for (int p = 0; p < NUM_Points; ++p) {
            double x, y, f;
            fread(&x, sizeof(double), 1, fp);
            fread(&y, sizeof(double), 1, fp);
            fread(&f, sizeof(double), 1, fp);
            (*all_points)[iter * NUM_Points + p].x = x;
            (*all_points)[iter * NUM_Points + p].y = y;
        }
    }
    fclose(fp);
}

int main(int argc, char* argv[]) {
    if (argc < 4) {
        printf("Usage: %s <input.bin> <output.txt> <num_threads>\n", argv[0]);
        return 1;
    }

    Points* all_points = nullptr;
    int nx, ny, maxiter, numpoints;
    read_binary_input(argv[1], &all_points, nx, ny, maxiter, numpoints);

    int num_threads = atoi(argv[3]);
    int mesh_size   = (GRID_X + 1) * (GRID_Y + 1);
    double* mesh_value = (double*)calloc(mesh_size, sizeof(double));

    auto t0 = std::chrono::high_resolution_clock::now();

    for (int iter = 0; iter < Maxiter; ++iter) {
        Points* cur = all_points + iter * NUM_Points;
        if (num_threads == 1)
            interpolation(mesh_value, cur);                     // pure serial
        else
            interpolation_parallel_private_v2(mesh_value, cur, num_threads); // fastest parallel
    }

    auto t1 = std::chrono::high_resolution_clock::now();
    double elapsed = std::chrono::duration<double>(t1 - t0).count();

    printf("Total time with %d threads: %.6f seconds\n", num_threads, elapsed);

    FILE* fp = fopen(argv[2], "w");
    if (fp) {
        for (int i = 0; i <= GRID_X; ++i)
            for (int j = 0; j <= GRID_Y; ++j)
                fprintf(fp, "%.10f\n", mesh_value[i * (GRID_Y+1) + j]);
        fclose(fp);
    }

    free(mesh_value);
    free(all_points);
    return 0;
}
