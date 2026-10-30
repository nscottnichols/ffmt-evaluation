#include <ffmt/base.hpp>
void only_header(char *output) {
#pragma omp target map(from:output[0:8])
  {
    (void)ffmt::format_to_n(output, 8, "{}", 42);
    ffmt::print("{}", 42);
  }
}
