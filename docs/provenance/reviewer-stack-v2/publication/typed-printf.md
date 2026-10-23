Support percent formatting without unsafe C varargs or the writing conversion %n.

For example:

```text
#include <ffmt/printf.hpp>
char out[32];
auto result = ffmt::printf_to_n(out, sizeof out, "%#08x %.3f", 42u, 1.25);
// out contains "0x00002a 1.250".
```

A separate typed grammar shares primitive conversion and bounded sinks, but does not implement %n. The percent parser uses typed arguments rather than C varargs and shares the
bounded output/error contract of brace formatting. It supports positional
arguments, dynamic width/precision, integer length modifiers and narrow/wide
output. Invalid conversions report errors; `%n` is rejected and never writes
through a pointer. Floating arguments follow printf's float-to-double promotion.
This parser is intentionally separate from brace parsing so each grammar can be
reviewed and tested independently.

Read in this order:

- [include/ffmt/printf.hpp](https://github.com/nscottnichols/ffmt/blob/aa36d84aaa2a050e56fbca8d7df5085e92040e48/include/ffmt/printf.hpp) — family_printf_value
- [include/ffmt/printf.hpp](https://github.com/nscottnichols/ffmt/blob/aa36d84aaa2a050e56fbca8d7df5085e92040e48/include/ffmt/printf.hpp) — family_printf
- [test/conformance/test_printf.cpp](https://github.com/nscottnichols/ffmt/blob/aa36d84aaa2a050e56fbca8d7df5085e92040e48/test/conformance/test_printf.cpp) — dynamic_and_positional_fields
- [test/conformance/test_printf.cpp](https://github.com/nscottnichols/ffmt/blob/aa36d84aaa2a050e56fbca8d7df5085e92040e48/test/conformance/test_printf.cpp) — invalid_conversions_do_not_write

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 11 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_BUFFER='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_SPECIFIERS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_printf CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_printf
python3 tools/conformance.py --route host-buffer --opt 2 --no-memory --no-negative --fmt-dir "$FMT_DIR" --host-cxx "$CXX"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 8; it remains draft until prerequisite human review.

Base: [`review-v2/shared-family`](https://github.com/nscottnichols/ffmt/tree/review-v2/shared-family); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
