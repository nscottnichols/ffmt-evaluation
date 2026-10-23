#include <cuda_runtime.h>
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
  int n = 0;
  if (cudaGetDeviceCount(&n) != cudaSuccess || n == 0)
    return 77;
  cudaDeviceProp p{};
  if (cudaGetDeviceProperties(&p, 0) != cudaSuccess)
    return 78;
  std::fprintf(stderr, "FFMT_DEVICE cuda name=%s arch=%d.%d\n", p.name, p.major,
               p.minor);
  kernel<<<1, 1>>>(std::atoi(argv[1]));
  if (cudaGetLastError() != cudaSuccess)
    return 79;
  if (cudaDeviceSynchronize() != cudaSuccess)
    return 80;
  return 0;
}
