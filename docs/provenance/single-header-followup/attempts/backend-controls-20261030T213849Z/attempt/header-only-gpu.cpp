#if !defined(__CUDACC__) && !defined(__HIPCC__)
#error Expected native CUDA or HIP compiler mode
#endif
#include <ffmt/base.hpp>
__global__ void only_header(char *output) {
  (void)ffmt::format_to_n(output, 8, "{}", 42);
  ffmt::print("{}", 42);
}
