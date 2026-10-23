Standard type traits do not consistently recognize native extended integers.

For example:

```text
#include <ffmt/detail/checked.hpp>
using U = unsigned __int128; // when the compiler supplies this type
char buffer[64];
auto result = ffmt::format_to(buffer, "{:#x}", U(1) << 100);
// Writes the full native value, "0x10000000000000000000000000".
```

Explicit signed and unsigned traits preserve the native width. _BitInt support follows the oracle surface through 64 bits. Compiler extensions are conditional. Wider _BitInt values report unsupported rather than narrowing.

Read in this order:

- [include/ffmt/detail/arguments.hpp](https://github.com/nscottnichols/ffmt/blob/61c59c73c12bfaa9f413b71cb40596c98e3961ef/include/ffmt/detail/arguments.hpp)
- [test/conformance/test_core_int128.cpp](https://github.com/nscottnichols/ffmt/blob/61c59c73c12bfaa9f413b71cb40596c98e3961ef/test/conformance/test_core_int128.cpp)
- [test/conformance/test_engine_bitint.cpp](https://github.com/nscottnichols/ffmt/blob/61c59c73c12bfaa9f413b71cb40596c98e3961ef/test/conformance/test_engine_bitint.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 13 recorded steps passed; 1 optional capability checks returned 77 (unsupported).

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_core_int128 build/cap_engine_bitint CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_core_int128
./build/cap_engine_bitint
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 4; it remains draft until prerequisite human review.

Base: [`review-v2/primitives`](https://github.com/nscottnichols/ffmt/tree/review-v2/primitives); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
