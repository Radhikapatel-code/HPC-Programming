/*
 * inputFileMaker.c
 *
 * Generates a binary input file for the interpolation assignment.
 *
 * Binary format:
 *   int NX
 *   int NY
 *   int NUM_Points
 *   int Maxiter
 *   then NUM_Points × { double x, double y, double f }
 *
 * Usage:
 *   ./inputFileMaker <NX> <NY> <NUM_Points> <Maxiter> <output_file>
 *
 * Example:
 *   ./inputFileMaker 250 100 900000 10 input.bin
 */

#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(int argc, char **argv)
{
    if (argc != 6) {
        printf("Usage: %s <NX> <NY> <NUM_Points> <Maxiter> <output_file>\n", argv[0]);
        return 1;
    }

    int NX        = atoi(argv[1]);
    int NY        = atoi(argv[2]);
    int NUM_Points = atoi(argv[3]);
    int Maxiter   = atoi(argv[4]);
    const char *filename = argv[5];

    FILE *file = fopen(filename, "wb");
    if (!file) {
        printf("Error opening file %s for writing\n", filename);
        return 1;
    }

    /* Write header */
    fwrite(&NX,         sizeof(int), 1, file);
    fwrite(&NY,         sizeof(int), 1, file);
    fwrite(&NUM_Points, sizeof(int), 1, file);
    fwrite(&Maxiter,    sizeof(int), 1, file);

    /* Write particle data: x, y in [0, 1], f = 1.0 */
    srand((unsigned int)time(NULL));

    double f = 1.0;
    for (int i = 0; i < NUM_Points; i++) {
        double x = (double)rand() / RAND_MAX;
        double y = (double)rand() / RAND_MAX;
        fwrite(&x, sizeof(double), 1, file);
        fwrite(&y, sizeof(double), 1, file);
        fwrite(&f, sizeof(double), 1, file);
    }

    fclose(file);
    printf("Generated %s: NX=%d NY=%d Points=%d Maxiter=%d\n",
           filename, NX, NY, NUM_Points, Maxiter);
    return 0;
}