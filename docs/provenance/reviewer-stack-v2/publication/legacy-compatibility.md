Existing ffmt formatters return a literal and a tuple from static format functions.

For example:

```text
Inside an existing ffmt::formatter<point> specialization:
static constexpr auto format(point p) {
  return ffmt::formatted<"({}, {})", int, int>{{p.x, p.y}};
}
// Formatting point{2, 7} with "{}" continues to write "(2, 7)".
// test_core_legacy.cpp checks the corresponding narrow and wide output.
```

Legacy values expand through the counted engine. Narrow nested literals are converted for wide destinations without allocating. Legacy custom formatters accept empty specs; modern parse/context formatters remain the spec-aware interface.

Read in this order:

- [include/ffmt/detail/execution.hpp](https://github.com/nscottnichols/ffmt/blob/083601f4aca62444539571ae9eac03ddde1545a0/include/ffmt/detail/execution.hpp)
- [test/conformance/test_core_legacy.cpp](https://github.com/nscottnichols/ffmt/blob/083601f4aca62444539571ae9eac03ddde1545a0/test/conformance/test_core_legacy.cpp)
- [test/conformance/test_legacy_forwarding.cpp](https://github.com/nscottnichols/ffmt/blob/083601f4aca62444539571ae9eac03ddde1545a0/test/conformance/test_legacy_forwarding.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 14 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_core_legacy build/cap_legacy_forwarding CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_core_legacy
./build/cap_legacy_forwarding
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 5; it remains draft until prerequisite human review.

Base: [`review-v2/format-as`](https://github.com/nscottnichols/ffmt/tree/review-v2/format-as); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
