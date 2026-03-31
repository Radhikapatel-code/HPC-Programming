#include <stdio.h>
#include <stdlib.h>
#include "init.h"

// Initialize all particle positions randomly inside the [0,1]x[0,1] domain.
void initializepoints(Points *points) {
    for (int i = 0; i < NUM_Points; i++) {
        points[i].x = (double)rand() / RAND_MAX;
        points[i].y = (double)rand() / RAND_MAX;
    }
}
