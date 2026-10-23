Request ANSI styling explicitly around an existing formattable value.

For example:

```text
#include <ffmt/color.hpp>
ffmt::println("{}", ffmt::styled(42, ffmt::fg(ffmt::rgb(255,20,30)) | ffmt::emphasis::bold));
```

Typed composition emits deterministic bytes without terminal detection. Styles explicitly emit ANSI escape bytes around the formatted value and reset
when a nonempty style ends. There is no terminal detection; captured output also
contains those bytes. RGB, terminal palette colors and emphasis flags compose
with `operator|`. Incompatible repeated terminal colors report `invalid_format`.
The wrapped formatter still owns ordinary value parsing and width semantics.

Read in this order:

- [include/ffmt/color.hpp](https://github.com/nscottnichols/ffmt/blob/ad9f041e98a32f730a9bd5e4e47e2aa496b826fb/include/ffmt/color.hpp)
- [test/conformance/test_style.cpp](https://github.com/nscottnichols/ffmt/blob/ad9f041e98a32f730a9bd5e4e47e2aa496b826fb/test/conformance/test_style.cpp)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 11 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_BUFFER='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_SPECIFIERS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_style CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_style
python3 tools/conformance.py --route host-buffer --opt 2 --no-memory --no-negative --fmt-dir "$FMT_DIR" --host-cxx "$CXX"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 8; it remains draft until prerequisite human review.

Base: [`review-v2/shared-family`](https://github.com/nscottnichols/ffmt/tree/review-v2/shared-family); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
