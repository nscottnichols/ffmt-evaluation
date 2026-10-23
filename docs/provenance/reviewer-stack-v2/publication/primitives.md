The old print-only interface cannot safely target caller-owned memory or report the full required size.

For example:

```text
#include <ffmt/detail/checked.hpp> // public base.hpp migrates later
char buffer[2];
auto result = ffmt::format_to_n(buffer, sizeof buffer, "{:04x}", 42);
// buffer == {'0', '0'}; result.written == 2; result.required == 4
```

Builtin formatters share one parser and counted sink. Signs, base prefixes, padding and digits have separate output responsibilities. Floating, Unicode display rules and customization protocols are introduced separately.

Read in this order:

- [include/ffmt/detail/integer.hpp](https://github.com/nscottnichols/ffmt/blob/5d7e0af475a3da5b8217842a02998229f7dc8536/include/ffmt/detail/integer.hpp)
- [include/ffmt/detail/memory.hpp](https://github.com/nscottnichols/ffmt/blob/5d7e0af475a3da5b8217842a02998229f7dc8536/include/ffmt/detail/memory.hpp)
- [include/ffmt/detail/execution.hpp](https://github.com/nscottnichols/ffmt/blob/5d7e0af475a3da5b8217842a02998229f7dc8536/include/ffmt/detail/execution.hpp)
- [test/conformance/test_core_primitives.cpp](https://github.com/nscottnichols/ffmt/blob/5d7e0af475a3da5b8217842a02998229f7dc8536/test/conformance/test_core_primitives.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 10 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_core_primitives CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_core_primitives
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 3; it remains draft until prerequisite human review.

Base: [`review-v2/parsing`](https://github.com/nscottnichols/ffmt/tree/review-v2/parsing); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
