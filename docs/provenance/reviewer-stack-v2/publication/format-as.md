Small wrappers should reuse primitive formatting without a full formatter specialization.

For example:

```text
#include <ffmt/detail/checked.hpp>
struct status { unsigned code; };
constexpr auto format_as(status value) { return value.code; }
// ffmt::format_to(buffer, "{:#x}", status{42}) writes "0x2a".
// The same mapped value can supply a dynamic integer width.
```

ADL mapping participates in parsing, output and dynamic width validation. Values retain references until mapping occurs. Mappings terminate at primitive representations; they are not a recursive serialization interface.

Read in this order:

- [include/ffmt/detail/type_traits.hpp](https://github.com/nscottnichols/ffmt/blob/e3c863ca8ee6e46a90b65d8e8b93c7789c67b240/include/ffmt/detail/type_traits.hpp)
- [test/conformance/test_core_format_as.cpp](https://github.com/nscottnichols/ffmt/blob/e3c863ca8ee6e46a90b65d8e8b93c7789c67b240/test/conformance/test_core_format_as.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 10 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_core_format_as CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_core_format_as
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 5; it remains draft until prerequisite human review.

Base: [`review-v2/formatter-compatibility`](https://github.com/nscottnichols/ffmt/tree/review-v2/formatter-compatibility); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
