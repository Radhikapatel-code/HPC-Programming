#include <stdio.h>
#include <stdlib.h>
#include <time.h>

int main(int argc, char** argv) {
    if (argc != 6) {
        printf("Usage: %s <NX> <NY> <NUM_POINTS> <MAXITER> <output.bin>\n", argv[0]);
        return 1;
    }

    int NX = atoi(argv[1]);
    int NY = atoi(argv[2]);
    int NUM_POINTS = atoi(argv[3]);
    int MAXITER = atoi(argv[4]);
    const char* filename = argv[5];

    FILE* fp = fopen(filename, "wb");
    if (!fp) {
        perror("Cannot create output.bin");
        return 1;
    }

    fwrite(&NX, sizeof(int), 1, fp);
    fwrite(&NY, sizeof(int), 1, fp);
    fwrite(&MAXITER, sizeof(int), 1, fp);
    fwrite(&NUM_POINTS, sizeof(int), 1, fp);

    srand(time(NULL));

    for (int iter = 0; iter < MAXITER; ++iter) {
        for (int p = 0; p < NUM_POINTS; ++p) {
            double x = (double)rand() / RAND_MAX;
            double y = (double)rand() / RAND_MAX;
            double f = 1.0;
            fwrite(&x, sizeof(double), 1, fp);
            fwrite(&y, sizeof(double), 1, fp);
            fwrite(&f, sizeof(double), 1, fp);
        }
    }

    fclose(fp);
    printf("Generated %s : NX=%d NY=%d Points=%d Maxiter=%d\n", filename, NX, NY, NUM_POINTS, MAXITER);
    return 0;
}