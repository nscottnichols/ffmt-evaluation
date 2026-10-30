#include <hip/hip_runtime.h>
#define HD __host__ __device__
#include <Kokkos_Core.hpp>
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

#include <cstring>
int main(int argc, char **argv) {
  if (argc != 2)
    return 2;
  Kokkos::initialize(argc, argv);
  if (std::strcmp(Kokkos::DefaultExecutionSpace::name(), "HIP") != 0) {
    Kokkos::finalize();
    return 77;
  }

  int device_id = 0;
  hipDeviceProp_t properties{};
  if (hipGetDevice(&device_id) != hipSuccess ||
      hipGetDeviceProperties(&properties, device_id) != hipSuccess) {
    Kokkos::finalize();
    return 78;
  }
  std::fprintf(stderr, "FFMT_DEVICE kokkos space=HIP name=%s arch=%d.%d\n",
               properties.name, properties.major, properties.minor);

  int index = std::atoi(argv[1]);
  Kokkos::parallel_for(
      "ffmt-case", Kokkos::RangePolicy<>(0, 1),
      KOKKOS_LAMBDA(int) { execute_case(index); });
  Kokkos::fence();
  Kokkos::finalize();
  return 0;
}
