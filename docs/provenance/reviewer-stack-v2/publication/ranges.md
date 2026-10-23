Format structured containers using element formatters while preserving iterator semantics.

For example:

```text
#include <ffmt/ranges.hpp>
std::array<int, 3> values{1, -2, 33};
ffmt::println("{::03}", values);  // [001, -02, 033]
ffmt::println("{:02x}", ffmt::join(values, ","));
```

Range detection and constrained formatter specializations; standard operations remain device-dependent. Ranges select sequence, set, map, string or debug-string presentation. Tuples
and container adaptors have explicit adapters; nested specifications follow the
second colon, while `n` removes delimiters. `range_format_kind` customizes string
versus debug-string treatment. Joins hold iterator/delimiter views; keep their
underlying objects alive. Mutable and move-only input iterators are preserved.
Right/center alignment on streaming iterators requires repeatable element
formatters and forward ranges; bounded writable buffers handle consuming ranges
without replay. The standard-library operations used by the range must be
callable on the selected device.

Read in this order:

- [include/ffmt/ranges.hpp](https://github.com/nscottnichols/ffmt/blob/241df53a29ac8cf096aacd20542c87b33540c0bf/include/ffmt/ranges.hpp)
- [test/conformance/test_ranges.cpp](https://github.com/nscottnichols/ffmt/blob/241df53a29ac8cf096aacd20542c87b33540c0bf/test/conformance/test_ranges.cpp)
- [test/conformance/test_ranges_iterators.cpp](https://github.com/nscottnichols/ffmt/blob/241df53a29ac8cf096aacd20542c87b33540c0bf/test/conformance/test_ranges_iterators.cpp)
- [test/conformance/test_ranges_forwarding.cpp](https://github.com/nscottnichols/ffmt/blob/241df53a29ac8cf096aacd20542c87b33540c0bf/test/conformance/test_ranges_forwarding.cpp)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 19 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_BUFFER='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_SPECIFIERS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_ranges build/cap_ranges_forwarding build/cap_ranges_iterators CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_ranges
./build/cap_ranges_forwarding
./build/cap_ranges_iterators
python3 tools/conformance.py --route host-buffer --opt 2 --no-memory --no-negative --fmt-dir "$FMT_DIR" --host-cxx "$CXX"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 8; it remains draft until prerequisite human review.

Base: [`review-v2/shared-family`](https://github.com/nscottnichols/ffmt/tree/review-v2/shared-family); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
