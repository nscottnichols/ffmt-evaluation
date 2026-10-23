Device environments cannot consistently provide host conversion services.

For example:

```text
#include <ffmt/detail/checked.hpp>
char buffer[64];
auto size = ffmt::detail::portable_shortest(
    buffer, std::numeric_limits<double>::denorm_min());
// buffer[0..size) is "5e-324", matching the independent fmt oracle.
```

Representation bits drive classification and exact interval comparisons. Bounded integer limbs hold decimal expansions without output-capacity limits. Integer interval conversion uses more code and bounded working storage than forwarding to libc, while avoiding locale and allocation services. Internal conversion renders supported finite magnitudes; the formatting layer handles signs and nonfinite spellings. The documented 1100/16520-digit bounds cover exact IEEE expansions and interval endpoints, rather than limiting requested output precision. Direct oracle tests cover adjacent powers of two, subnormal/normal transitions, maximum finite values, rounding ties and carries.

Read in this order:

- [include/ffmt/detail/floating.hpp](https://github.com/nscottnichols/ffmt/blob/dbd0b9f5fb1bf00982317161abdc7c66aa85aa17/include/ffmt/detail/floating.hpp)
- [test/conformance/test_core_conversion.cpp](https://github.com/nscottnichols/ffmt/blob/dbd0b9f5fb1bf00982317161abdc7c66aa85aa17/test/conformance/test_core_conversion.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 10 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_core_conversion CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_core_conversion
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 4; it remains draft until prerequisite human review.

Base: [`review-v2/conversion-preparation`](https://github.com/nscottnichols/ffmt/tree/review-v2/conversion-preparation); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
