#include <cstdio>

template <class F> static void run_in_lambda(F&& f) { f(); }

#define RUN(stmt) do {           \
  _Pragma("omp target")          \
  { stmt; }                      \
} while (0)

int main() {
  run_in_lambda([]() {
    RUN(printf("hello\n"));
  });
  return 0;
}
