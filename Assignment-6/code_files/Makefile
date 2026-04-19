CXX = g++
CXXFLAGS = -O3 -march=native -fopenmp -std=c++11 -Wall -Wextra
TARGET = interp

all: $(TARGET) input_fileMaker

$(TARGET): main.cpp utils.cpp
	$(CXX) $(CXXFLAGS) -o $(TARGET) main.cpp utils.cpp

input_fileMaker: input_fileMaker.c
	gcc -O3 -std=c99 -o input_fileMaker input_fileMaker.c -lm

clean:
	rm -f $(TARGET) input_fileMaker *.bin *.txt

.PHONY: all clean