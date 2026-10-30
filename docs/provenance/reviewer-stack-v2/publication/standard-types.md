Format common standard wrappers through existing contained-value formatters.

For example:

```text
#include <ffmt/std.hpp>
ffmt::println("{}", std::optional<int>{42});  // optional(42)
ffmt::println("{:.2f}", std::complex<double>{1, -2.2}); // (1.00-2.20i)
```

Explicit adapters avoid streams and RTTI; each standard operation must be available on the target. Optional and variant values use debug presentation for contained text; bitsets,
bytes, reference wrappers, atomics, complex numbers, source locations and pointer
views have explicit adapters. `ffmt::ptr` makes a raw/smart pointer printable
without dereferencing it. Atomic formatting loads the current value; a format
call is not an atomic snapshot across multiple arguments. These adapters do not
supply filesystem, streams, RTTI, thread-ID or exception-traversal services.
Standard-library types and their operations must themselves be device callable.

Read in this order:

- [include/ffmt/std.hpp](https://github.com/nscottnichols/ffmt/blob/98a1c1e67fba095bd678e0a1769a2ab89efa5084/include/ffmt/std.hpp)
- [test/conformance/test_std.cpp](https://github.com/nscottnichols/ffmt/blob/98a1c1e67fba095bd678e0a1769a2ab89efa5084/test/conformance/test_std.cpp)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 11 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_BUFFER='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_SPECIFIERS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_std CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_std
python3 tools/conformance.py --route host-buffer --opt 2 --no-memory --no-negative --fmt-dir "$FMT_DIR" --host-cxx "$CXX"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 8; it remains draft until prerequisite human review.

Base: [`review-v2/shared-family`](https://github.com/nscottnichols/ffmt/tree/review-v2/shared-family); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
