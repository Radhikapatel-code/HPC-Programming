#ifndef UTILS_H
#define UTILS_H
#include <time.h>

void vector_copy_operation(double *x, double *y, int Np);
void vector_scale_operation(double *x, double *y, int Np);
void vector_sum_operation(double *x, double *y, double *S, int Np);
void vector_triad_operation(double *x, double *y, double *v, double *S, int Np);
void energy_kernel_operation(double *v, double *E, int Np);
void dummy(int x);

#endif
