Represent expected values and errors when the standard library supports C++23.

For example:

```text
#include <ffmt/std23.hpp>
ffmt::println("{}", std::expected<int, int>{42}); // expected(42)
```

Keep expected/unexpected adapters in an opt-in header. Make excludes suites declaring c++23 from its default capability target and exposes test-cxx23 explicitly; CMake retains its independent opt-in option. `std23.hpp` adds `std::expected` and `std::unexpected` adapters when the selected
standard library exposes C++23 expected support. C++20 users can omit the header.
The contained value and error must be formattable. Optional tests report skip
(exit 77) when the standard library lacks the feature; that skip is not evidence
of conformance. Enable the suite with a C++23 compiler mode.

Read in this order:

- [include/ffmt/std23.hpp](https://github.com/nscottnichols/ffmt/blob/3a07a5f9e3aebd120ffb193a0723ba409ee3cfe3/include/ffmt/std23.hpp)
- [test/conformance/test_std23.cpp](https://github.com/nscottnichols/ffmt/blob/3a07a5f9e3aebd120ffb193a0723ba409ee3cfe3/test/conformance/test_std23.cpp)
- [mk/portable-tests.mk](https://github.com/nscottnichols/ffmt/blob/3a07a5f9e3aebd120ffb193a0723ba409ee3cfe3/mk/portable-tests.mk) — declared-standard selection
- [test/conformance/test_cxx23_opt_in.py](https://github.com/nscottnichols/ffmt/blob/3a07a5f9e3aebd120ffb193a0723ba409ee3cfe3/test/conformance/test_cxx23_opt_in.py)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 11 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_std23 CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_std23
python3 -m unittest discover -s test/conformance -p test_cxx23_opt_in.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 9; it remains draft until prerequisite human review.

Base: [`review-v2/standard-types`](https://github.com/nscottnichols/ffmt/tree/review-v2/standard-types); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
