CXX      = g++
CXXFLAGS = -O2 -fopenmp
TARGET   = exp1

SRCS = main_exp1.cpp init.cpp utils.cpp

$(TARGET): $(SRCS)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRCS)

clean:
	rm -f $(TARGET) Mesh.out *.txt
