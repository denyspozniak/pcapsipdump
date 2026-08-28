LIBS ?= -lpcap -lstdc++
CXXFLAGS ?= --std=c++11

SRC = calltable_benchmark.cpp ../../calltable.cpp ../../trigger.cpp \
      ../../pcapsipdump_lib.cpp ../../pcapsipdump_strlib.cpp
DEPS = $(SRC) ../../calltable.h ../../trigger.h ../../pcapsipdump_lib.h

tests: calltable_benchmark
	./calltable_benchmark

calltable_benchmark: $(DEPS)
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $(DEFS) $(BSDSTR_DEFS) -ggdb \
	$(SRC) $(LIBS) $(BSDSTR_LIBS) \
	-o calltable_benchmark

clean:
	rm -f calltable_benchmark gmon.out

.PHONY: tests clean
