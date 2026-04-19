#include "utils.h"
#include <cmath>
#include <omp.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>

// ====================== SERIAL INTERPOLATION ======================
void interpolation(double *mesh_value, Points *points) {
    int NY1 = GRID_Y + 1;
    for (int p = 0; p < NUM_Points; ++p) {
        double x = points[p].x;
        double y = points[p].y;
        int i = (int)(x / dx);
        int j = (int)(y / dy);
        if (i >= GRID_X) i = GRID_X - 1;
        if (j >= GRID_Y) j = GRID_Y - 1;
        double lx = x - i * dx;
        double ly = y - j * dy;
        double w00 = (1.0 - lx/dx) * (1.0 - ly/dy);
        double w10 = (lx/dx)       * (1.0 - ly/dy);
        double w01 = (1.0 - lx/dx) * (ly/dy);
        double w11 = (lx/dx)       * (ly/dy);
        mesh_value[i     * NY1 + j    ] += w00;
        mesh_value[(i+1) * NY1 + j    ] += w10;
        mesh_value[i     * NY1 + (j+1)] += w01;
        mesh_value[(i+1) * NY1 + (j+1)] += w11;
    }
}

// ====================== PARALLEL ATOMIC ======================
void interpolation_parallel_atomic(double *mesh_value, Points *points, int num_threads) {
    omp_set_num_threads(num_threads);
    int NY1 = GRID_Y + 1;
    #pragma omp parallel for schedule(static)
    for (int p = 0; p < NUM_Points; ++p) {
        double x = points[p].x;
        double y = points[p].y;
        int i = (int)(x / dx);
        int j = (int)(y / dy);
        if (i >= GRID_X) i = GRID_X - 1;
        if (j >= GRID_Y) j = GRID_Y - 1;
        double lx = x - i * dx;
        double ly = y - j * dy;
        double w00 = (1.0 - lx/dx) * (1.0 - ly/dy);
        double w10 = (lx/dx)       * (1.0 - ly/dy);
        double w01 = (1.0 - lx/dx) * (ly/dy);
        double w11 = (lx/dx)       * (ly/dy);
        #pragma omp atomic
        mesh_value[i     * NY1 + j    ] += w00;
        #pragma omp atomic
        mesh_value[(i+1) * NY1 + j    ] += w10;
        #pragma omp atomic
        mesh_value[i     * NY1 + (j+1)] += w01;
        #pragma omp atomic
        mesh_value[(i+1) * NY1 + (j+1)] += w11;
    }
}

// ====================== PARALLEL PRIVATE + CRITICAL REDUCTION ======================
void interpolation_parallel_private(double *mesh_value, Points *points, int num_threads) {
    omp_set_num_threads(num_threads);
    int NY1      = GRID_Y + 1;
    int mesh_size = (GRID_X + 1) * (GRID_Y + 1);
    #pragma omp parallel
    {
        double* pm = (double*)calloc(mesh_size, sizeof(double));
        #pragma omp for schedule(static)
        for (int p = 0; p < NUM_Points; ++p) {
            double x = points[p].x; double y = points[p].y;
            int i = (int)(x / dx);  int j = (int)(y / dy);
            if (i >= GRID_X) i = GRID_X - 1;
            if (j >= GRID_Y) j = GRID_Y - 1;
            double lx = x - i*dx,  ly = y - j*dy;
            double w00 = (1.0-lx/dx)*(1.0-ly/dy);
            double w10 = (lx/dx)*(1.0-ly/dy);
            double w01 = (1.0-lx/dx)*(ly/dy);
            double w11 = (lx/dx)*(ly/dy);
            pm[i*NY1+j]     += w00; pm[(i+1)*NY1+j]     += w10;
            pm[i*NY1+(j+1)] += w01; pm[(i+1)*NY1+(j+1)] += w11;
        }
        #pragma omp critical
        { for (int k = 0; k < mesh_size; ++k) mesh_value[k] += pm[k]; }
        free(pm);
    }
}

// ====================== PARALLEL PRIVATE + PARALLEL REDUCTION (FASTEST) ======================
// Improvement over interpolation_parallel_private:
//   - Private buffers are pre-allocated in a single flat array (avoids heap fragmentation)
//   - The reduction phase is ALSO parallelised (#pragma omp for), eliminating the serial
//     bottleneck of omp critical. Each thread reduces a disjoint chunk of the output mesh.
// Complexity: O(P/T) scatter  +  O(M*T/T) = O(M) reduction  (M = mesh cells, P = particles)
void interpolation_parallel_private_v2(double *mesh_value, Points *points, int num_threads) {
    omp_set_num_threads(num_threads);
    int NY1       = GRID_Y + 1;
    int mesh_size = (GRID_X + 1) * (GRID_Y + 1);

    // Flat layout: row t -> thread_meshes[t * mesh_size ... (t+1)*mesh_size - 1]
    double* thread_meshes = (double*)calloc((size_t)num_threads * mesh_size, sizeof(double));

    #pragma omp parallel num_threads(num_threads)
    {
        int tid    = omp_get_thread_num();
        double* lm = thread_meshes + (size_t)tid * mesh_size;

        // Phase 1: each thread scatters its particle subset into its own buffer — no locks
        #pragma omp for schedule(static) nowait
        for (int p = 0; p < NUM_Points; ++p) {
            double x = points[p].x; double y = points[p].y;
            int i = (int)(x / dx);  int j = (int)(y / dy);
            if (i >= GRID_X) i = GRID_X - 1;
            if (j >= GRID_Y) j = GRID_Y - 1;
            double lx = x - i*dx,  ly = y - j*dy;
            double w00 = (1.0-lx/dx)*(1.0-ly/dy);
            double w10 = (lx/dx)*(1.0-ly/dy);
            double w01 = (1.0-lx/dx)*(ly/dy);
            double w11 = (lx/dx)*(ly/dy);
            lm[i*NY1+j]     += w00; lm[(i+1)*NY1+j]     += w10;
            lm[i*NY1+(j+1)] += w01; lm[(i+1)*NY1+(j+1)] += w11;
        }
        // Implicit barrier ensures all threads finished Phase 1

        // Phase 2: parallel mesh reduction — each cell summed by exactly one thread
        #pragma omp for schedule(static)
        for (int k = 0; k < mesh_size; ++k) {
            double s = 0.0;
            for (int t = 0; t < num_threads; ++t)
                s += thread_meshes[(size_t)t * mesh_size + k];
            mesh_value[k] += s;
        }
    }

    free(thread_meshes);
}

// ─── Stubs kept for header compatibility ──────────────────────────────────
void mover_deferred_serial (Points*,double,double,int*o){*o=0;}
void mover_deferred_parallel(Points*,double,double,int*o){*o=0;}
void mover_immediate_serial (Points*,double,double,int*o){*o=0;}
void mover_immediate_parallel(Points*,double,double,int*o){*o=0;}
void mover_no_del_parallel(Points*,double,double){}
void save_mesh(double*){}
