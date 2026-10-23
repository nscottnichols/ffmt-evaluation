Format chrono values without host locale, timezone-database or strftime services.

For example:

```text
#include <ffmt/chrono.hpp>
ffmt::println("{:%T}", std::chrono::milliseconds{-123456}); // -00:02:03.456
ffmt::println("{:%G-W%V-%u}", std::chrono::year{2021}/1/1); // 2020-W53-5
```

Civil-date arithmetic and explicit tokens preserve device callability; locale/timezone queries remain unsupported. The header supports durations, C++20 calendar values, `std::tm`, system time
points and local time points using civil-date arithmetic and explicit tokens.
Fractional precision, negative timestamps and ISO week years follow the pinned
fmt reference. This implementation provides locale-independent formatting; it
does not query clocks, a timezone database or locale services. Local time points
therefore reject zone/offset tokens. Device use requires the involved standard
chrono operations to be available on that device.

Read in this order:

- [include/ffmt/chrono.hpp](https://github.com/nscottnichols/ffmt/blob/862369f1856e7174106cacace253671be59e7271/include/ffmt/chrono.hpp)
- [test/conformance/test_chrono.cpp](https://github.com/nscottnichols/ffmt/blob/862369f1856e7174106cacace253671be59e7271/test/conformance/test_chrono.cpp)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 11 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_BUFFER='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_SPECIFIERS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_chrono CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_chrono
python3 tools/conformance.py --route host-buffer --opt 2 --no-memory --no-negative --fmt-dir "$FMT_DIR" --host-cxx "$CXX"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 8; it remains draft until prerequisite human review.

Base: [`review-v2/shared-family`](https://github.com/nscottnichols/ffmt/tree/review-v2/shared-family); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
