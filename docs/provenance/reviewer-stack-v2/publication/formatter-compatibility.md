User-defined values need to consume specs and write into the caller context.

For example:

```text
#include <ffmt/detail/checked.hpp>
struct point { int value; };
template <class Char>
struct ffmt::formatter<point, Char> : ffmt::formatter<int, Char> {
  template <class Context>
  auto format(const point& p, Context& ctx) const {
    return ffmt::formatter<int, Char>::format(p.value, ctx);
  }
};
// Formatting point{42} with "{:04x}" now writes "002a".
// Inherited parse() checks the same specs as the integer formatter.
```

Eligibility checks inspect the cv-qualified reference accepted by format. Shared sink iterators preserve nested counts without copying user objects. The protocol is template based with checked statuses; it does not provide exception services or type-erased stores.

Read in this order:

- [include/ffmt/detail/formatters.hpp](https://github.com/nscottnichols/ffmt/blob/7ee21c2a808b38744643cbeaad9517436f6281a2/include/ffmt/detail/formatters.hpp)
- [include/ffmt/detail/context.hpp](https://github.com/nscottnichols/ffmt/blob/7ee21c2a808b38744643cbeaad9517436f6281a2/include/ffmt/detail/context.hpp)
- [test/conformance/test_core_formatters.cpp](https://github.com/nscottnichols/ffmt/blob/7ee21c2a808b38744643cbeaad9517436f6281a2/test/conformance/test_core_formatters.cpp)
- [test/conformance/test_core_forwarding.cpp](https://github.com/nscottnichols/ffmt/blob/7ee21c2a808b38744643cbeaad9517436f6281a2/test/conformance/test_core_forwarding.cpp)
- [test/conformance/test_formatter_composition.cpp](https://github.com/nscottnichols/ffmt/blob/7ee21c2a808b38744643cbeaad9517436f6281a2/test/conformance/test_formatter_composition.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 18 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_core_formatters build/cap_core_forwarding build/cap_formatter_composition CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_core_formatters
./build/cap_core_forwarding
./build/cap_formatter_composition
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 5; it remains draft until prerequisite human review.

Base: [`review-v2/primitives`](https://github.com/nscottnichols/ffmt/tree/review-v2/primitives); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
