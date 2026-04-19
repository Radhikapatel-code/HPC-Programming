# ─────────────────────────────────────────────────────────────
# Makefile for HPC Assignment 07 – Parallel Interpolation
# ─────────────────────────────────────────────────────────────

CC      = gcc
CXX     = g++
# -funroll-loops helps the bilinear weight computation and reduction inner loop
CFLAGS  = -O3 -march=native -funroll-loops -Wall -Wno-unused-result
OMPFLAG = -fopenmp

.PHONY: all serial parallel maker clean test

all: serial parallel maker

# Serial executable (uses functions.cpp)
serial: main.cpp functions.cpp init.h utils.h
	$(CXX) $(CFLAGS) -o serial main.cpp functions.cpp -lm
	@echo "Built: ./serial"

# Parallel executable (uses functions_parallel.cpp)
parallel: main.cpp functions_parallel.cpp init.h utils.h
	$(CXX) $(CFLAGS) $(OMPFLAG) -o parallel main.cpp functions_parallel.cpp -lm
	@echo "Built: ./parallel"

# Input file generator
maker: inputFileMaker.c
	$(CC) $(CFLAGS) -o inputFileMaker inputFileMaker.c -lm
	@echo "Built: ./inputFileMaker"

# Quick correctness test (NX=10, NY=10, 1000 pts, 1 iter)
test: serial parallel maker
	./inputFileMaker 10 10 1000 1 _test.bin
	./serial _test.bin && mv output.txt serial_test.txt
	OMP_NUM_THREADS=4 ./parallel _test.bin && mv output.txt parallel_test.txt
	python3 -c "\
s=[float(x) for x in open('serial_test.txt').read().split()];\
p=[float(x) for x in open('parallel_test.txt').read().split()];\
d=max(abs(a-b) for a,b in zip(s,p));\
print('PASS: max diff =',d) if d<1e-10 else print('FAIL: max diff =',d)"
	@rm -f _test.bin

clean:
	rm -f serial parallel inputFileMaker *.txt *.bin
	@echo "Cleaned."