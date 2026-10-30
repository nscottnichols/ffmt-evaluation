#include <hip/hip_runtime.h>
#define HD __host__ __device__
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

__global__ void kernel(int index) { execute_case(index); }
int main(int argc, char **argv) {
  if (argc != 2)
    return 2;
  int count = 0;
  if (hipGetDeviceCount(&count) != hipSuccess || count == 0)
    return 77;
  hipDeviceProp_t properties{};
  if (hipGetDeviceProperties(&properties, 0) != hipSuccess)
    return 78;
  std::fprintf(stderr, "FFMT_DEVICE hip name=%s arch=%d.%d\n", properties.name,
               properties.major, properties.minor);
  hipLaunchKernelGGL(kernel, dim3(1), dim3(1), 0, 0, std::atoi(argv[1]));
  if (hipGetLastError() != hipSuccess)
    return 79;
  if (hipDeviceSynchronize() != hipSuccess)
    return 80;
  return 0;
}
