#include <ffmt/base.hpp>
void only_header(sycl::queue &queue, char *output) {
  queue.single_task([=] {
    (void)ffmt::format_to_n(output, 8, "{}", 42);
    ffmt::print("{}", 42);
  });
}
