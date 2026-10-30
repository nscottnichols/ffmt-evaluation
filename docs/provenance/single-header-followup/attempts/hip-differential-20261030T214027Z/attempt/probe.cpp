#if !defined(__HIPCC__)
#error Native HIP language is required
#endif
#include <hip/hip_runtime.h>
#include <ffmt/base.hpp>
__global__ void only_header(char *output) {
  (void)ffmt::format_to_n(output, 8, "{}", 42);
  ffmt::print("{}", 42);
}
