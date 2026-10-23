Verify cross-feature composition without making optional adapters depend on each other.

For example:

```text
#include <ffmt/args.hpp>
#include <ffmt/ranges.hpp>
std::array<int, 3> values{1, -2, 33};
ffmt::println("{values:*>{width}:03}", ffmt::arg("values", values), ffmt::arg("width", 25));
```

Integration-only fixtures sit above independent feature branches. Named argument wrappers preserve the referenced family's mutability and provide
runtime names for outer width fields. The interaction tests combine names with
ranges and standard-type adapters. Each family and named arguments also has an
independent test suite, so this integration adds no prerequisite between those
features.

Read in this order:

- [test/conformance/test_feature_integration.cpp](https://github.com/nscottnichols/ffmt/blob/dd407fc38b596fcda23152a122f12bf69829c18d/test/conformance/test_feature_integration.cpp)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 10 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_feature_integration CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_feature_integration
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 9; it remains draft until prerequisite human review.

Base: [`review-v2/base-feature-integration`](https://github.com/nscottnichols/ffmt/tree/review-v2/base-feature-integration); 3 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
