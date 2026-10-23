Byte counts alone misalign multibyte text, and decoding must respect counted boundaries.

For example:

```text
#include <ffmt/detail/checked.hpp>
char buffer[32];
auto result = ffmt::format_to(buffer, "{:─^9}", "é");
// Bytes encode "────é────": display width 9, rather than padding by UTF-8 byte count.
```

Counted UTF-8 decoding, display-width tables and printability tables govern fill, alignment, precision and debug escapes. Wide output follows code-unit semantics. These are qualified fmt semantics, not terminal-specific grapheme measurement. Unicode can still be disabled explicitly.

Read in this order:

- [include/ffmt/detail/parse.hpp](https://github.com/nscottnichols/ffmt/blob/e285726a33a1d1fc0e3870a6e58589f25cd53c83/include/ffmt/detail/parse.hpp)
- [include/ffmt/detail/unicode_width.hpp](https://github.com/nscottnichols/ffmt/blob/e285726a33a1d1fc0e3870a6e58589f25cd53c83/include/ffmt/detail/unicode_width.hpp)
- [include/ffmt/detail/text.hpp](https://github.com/nscottnichols/ffmt/blob/e285726a33a1d1fc0e3870a6e58589f25cd53c83/include/ffmt/detail/text.hpp)
- [test/conformance/test_core_unicode.cpp](https://github.com/nscottnichols/ffmt/blob/e285726a33a1d1fc0e3870a6e58589f25cd53c83/test/conformance/test_core_unicode.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 10 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_core_unicode CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_core_unicode
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 4; it remains draft until prerequisite human review.

Base: [`review-v2/primitives`](https://github.com/nscottnichols/ffmt/tree/review-v2/primitives); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
