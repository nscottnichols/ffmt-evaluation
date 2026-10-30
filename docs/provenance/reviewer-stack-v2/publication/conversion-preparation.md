The qualified conversion routines were embedded in the public base header.

For example:

```text
// Existing handwritten bodies move into detail/dragonbox.hpp and detail/exact_decimal.hpp.
```

Bodies are copied unchanged from aeff043. Only namespace and OpenMP-region wrappers are added; extraction hashes are recorded. The helpers are not activated until conversion integration. Handwritten logic remains explicitly handwritten.

Read in this order:

- [include/ffmt/detail/dragonbox.hpp](https://github.com/nscottnichols/ffmt/blob/543f6913b4ada63547df28004d7ca0273b617f09/include/ffmt/detail/dragonbox.hpp)
- [include/ffmt/detail/exact_decimal.hpp](https://github.com/nscottnichols/ffmt/blob/543f6913b4ada63547df28004d7ca0273b617f09/include/ffmt/detail/exact_decimal.hpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 6 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
printf '#include <ffmt/base.hpp>\n' > base-header-probe.cpp
"$CXX" -std=c++20 "$HOST_OPT" -fno-fast-math -Wall -Werror -Iinclude $EXTRA_CXXFLAGS -c base-header-probe.cpp -o base-header-probe.o
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 4; it remains draft until prerequisite human review.

Base: [`review-v2/primitives`](https://github.com/nscottnichols/ffmt/tree/review-v2/primitives); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
