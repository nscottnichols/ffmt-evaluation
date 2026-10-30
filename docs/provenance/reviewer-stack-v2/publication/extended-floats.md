Passing extended values through double loses range and precision before formatting.

For example:

```text
#include <ffmt/detail/checked.hpp>
char buffer[64];
auto result = ffmt::format_to(buffer, "{:.21g}", 1.234567890123456789L);
// Conversion uses the native long-double representation; it does not narrow to double.
```

Native 80-bit and 128-bit decomposition feeds the same exact decimal algorithm. Formatting does not require quadmath conversion. Layouts and availability are target dependent. Unsupported representations return a checked status.

Read in this order:

- [include/ffmt/detail/floating.hpp](https://github.com/nscottnichols/ffmt/blob/e44145c128c8cafcc061ada1de8553fcbb79e179/include/ffmt/detail/floating.hpp)
- [include/ffmt/detail/extended.hpp](https://github.com/nscottnichols/ffmt/blob/e44145c128c8cafcc061ada1de8553fcbb79e179/include/ffmt/detail/extended.hpp)
- [test/conformance/test_engine_extended.cpp](https://github.com/nscottnichols/ffmt/blob/e44145c128c8cafcc061ada1de8553fcbb79e179/test/conformance/test_engine_extended.cpp)
- [test/conformance/test_engine_quad.cpp](https://github.com/nscottnichols/ffmt/blob/e44145c128c8cafcc061ada1de8553fcbb79e179/test/conformance/test_engine_quad.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 14 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_engine_extended build/cap_engine_quad CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_engine_extended
./build/cap_engine_quad
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 4; it remains draft until prerequisite human review.

Base: [`review-v2/base-extended-floats`](https://github.com/nscottnichols/ffmt/tree/review-v2/base-extended-floats); 2 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
