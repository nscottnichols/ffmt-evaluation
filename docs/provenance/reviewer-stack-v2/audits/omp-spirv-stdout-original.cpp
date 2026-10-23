#include <omp.h>
#define HD
#include <ffmt/base.hpp>

#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
template <class T, class U> HD T bits(U v) { return __builtin_bit_cast(T, v); }

HD void execute_case(int index) {
  switch (index) {
  case 0: {
    FFMT_PRINT("{}", 42);
    break;
  }
  }
}

int main(int argc, char **argv) {
  if (argc != 2)
    return 2;
  int initial = 1;
#pragma omp target map(from : initial)
  {
    initial = omp_is_initial_device();
  }
  if (initial)
    return 77;
  std::fprintf(stderr, "FFMT_DEVICE openmp device=%d initial_device=false\n",
               omp_get_default_device());
  int index = std::atoi(argv[1]);
#pragma omp target firstprivate(index)
  {
    execute_case(index);
  }
  return 0;
}
