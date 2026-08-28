CXX ?= g++

tests: pcapsipdump_strlib_unittest
	./pcapsipdump_strlib_unittest
	@echo "unit tests OK"

pcapsipdump_strlib_unittest: pcapsipdump_strlib_unittest.cpp \
		../../pcapsipdump_strlib.cpp ../../pcapsipdump_strlib.h
	$(CXX) $(CXXFLAGS) $(LDFLAGS) -Wall -ggdb \
	pcapsipdump_strlib_unittest.cpp ../../pcapsipdump_strlib.cpp \
	-o ./pcapsipdump_strlib_unittest

clean:
	rm -f pcapsipdump_strlib_unittest

.PHONY: tests clean
