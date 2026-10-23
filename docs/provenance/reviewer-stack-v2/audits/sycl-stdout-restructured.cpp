#include <sycl/sycl.hpp>
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

#include <exception>
int main(int argc, char **argv) {
  if (argc != 2)
    return 2;
  try {
    sycl::queue queue{sycl::gpu_selector_v};
    auto device = queue.get_device();
    auto name = device.get_info<sycl::info::device::name>();
    std::fprintf(stderr, "FFMT_DEVICE sycl name=%s fp64=%d\n", name.c_str(),
                 device.has(sycl::aspect::fp64));
    int index = std::atoi(argv[1]);
    queue.single_task([=] { execute_case(index); }).wait_and_throw();
    return 0;
  } catch (const std::exception &error) {
    std::fprintf(stderr, "%s\n", error.what());
    return 80;
  }
}
