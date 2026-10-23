Floating fields need correct rounding even when requested precision exceeds stored output.

For example:

```text
#include <ffmt/detail/checked.hpp>
char buffer[2];
auto result = ffmt::format_to_n(buffer, sizeof buffer, "{:.2000f}", 0.125);
// Stores "0."; result.written == 2; result.required == 2002.
```

Shortest formatting uses Dragonbox normally and integer interval conversion for fast-math and SPIR-V. Requested trailing zeros stream through counted sinks. The oracle stays strictly compiled. Host fast-math tests use separately established expected strings and do not qualify device runtimes.

Read in this order:

- [include/ffmt/detail/numeric.hpp](https://github.com/nscottnichols/ffmt/blob/509dbd5a28fcd0b8b549876a317c0a254cc4ccc8/include/ffmt/detail/numeric.hpp)
- [test/conformance/test_core_floating.cpp](https://github.com/nscottnichols/ffmt/blob/509dbd5a28fcd0b8b549876a317c0a254cc4ccc8/test/conformance/test_core_floating.cpp)
- [test/conformance/test_engine_fast_math.cpp](https://github.com/nscottnichols/ffmt/blob/509dbd5a28fcd0b8b549876a317c0a254cc4ccc8/test/conformance/test_engine_fast_math.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 18 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_core_floating build/cap_engine_fast_math build/cap_core_floating_portable CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_core_floating
./build/cap_engine_fast_math
./build/cap_core_floating_portable
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 4; it remains draft until prerequisite human review.

Base: [`review-v2/floating-conversion`](https://github.com/nscottnichols/ffmt/tree/review-v2/floating-conversion); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
