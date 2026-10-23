Runtime execution and literal validation need a single grammar.

For example:

```text
Given the handler in test_core_parsing.cpp:
ffmt::detail::walk_format<char>("{{{:04x}}}", events);
// Receives two literal braces and one argument with width 4/type x.
// "{0} {}" instead returns invalid_format for mixed index modes.
```

A handler receives parsed fields; parse context tracks index modes and checks dynamic references without producing output. This prefix supports ASCII fill; counted Unicode decoding is introduced with its tests.

Read in this order:

- [include/ffmt/detail/parse.hpp](https://github.com/nscottnichols/ffmt/blob/11199fa8fd88f5278e8d17040b9313dee604290b/include/ffmt/detail/parse.hpp)
- [test/conformance/test_core_parsing.cpp](https://github.com/nscottnichols/ffmt/blob/11199fa8fd88f5278e8d17040b9313dee604290b/test/conformance/test_core_parsing.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 10 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_core_parsing CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_core_parsing
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 3; it remains draft until prerequisite human review.

Base: [`review-v2/accounting`](https://github.com/nscottnichols/ffmt/tree/review-v2/accounting); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
