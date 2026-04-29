# Makefile for HPC Assignment 08 on the GICS cluster

CC         = gcc
CXX_SERIAL = g++
CXX_MPI    = /usr/mpi/gcc/openmpi-1.8.8/bin/mpicxx
MPIRUN     = /usr/mpi/gcc/openmpi-1.8.8/bin/mpirun

COMMON_FLAGS = -O3 -march=native -funroll-loops -Wall -Wextra -Wno-unused-result
OMP_FLAGS    = -fopenmp
MPI_DEFS     = -DUSE_MPI

.PHONY: all serial parallel maker clean test_cluster

all: serial parallel maker

serial: main.cpp functions.cpp init.h utils.h
	$(CXX_SERIAL) $(COMMON_FLAGS) $(OMP_FLAGS) -o serial main.cpp functions.cpp -lm
	@echo "Built: ./serial"

parallel: main.cpp functions_parallel.cpp init.h utils.h
	$(CXX_MPI) $(COMMON_FLAGS) $(OMP_FLAGS) $(MPI_DEFS) -o parallel main.cpp functions_parallel.cpp -lm
	@echo "Built: ./parallel (hybrid MPI + OpenMP)"

maker: inputFileMaker.c
	$(CC) $(COMMON_FLAGS) -o inputFileMaker inputFileMaker.c -lm
	@echo "Built: ./inputFileMaker"

test_cluster: serial parallel maker
	mkdir -p data_cluster inputs
	./inputFileMaker 10 10 1000 1 inputs/correctness_test.bin
	./serial inputs/correctness_test.bin > data_cluster/serial_correctness_stdout.txt
	mv output.txt data_cluster/serial_correctness_output.txt
	OMP_NUM_THREADS=1 $(MPIRUN) -np 4 ./parallel inputs/correctness_test.bin > data_cluster/parallel_correctness_stdout.txt
	mv output.txt data_cluster/parallel_correctness_output.txt
	python3 -c "\
s=[float(x) for x in open('data_cluster/serial_correctness_output.txt').read().split()];\
p=[float(x) for x in open('data_cluster/parallel_correctness_output.txt').read().split()];\
d=max(abs(a-b) for a,b in zip(s,p));\
open('data_cluster/correctness_check.txt','w').write('PASS: max diff = %0.12e\n' % d if d < 1e-10 else 'FAIL: max diff = %0.12e\n' % d);\
print(open('data_cluster/correctness_check.txt').read().strip())"

clean:
	rm -f serial parallel inputFileMaker output.txt
	@echo "Cleaned build artifacts."
