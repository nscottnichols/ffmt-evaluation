Formatting into memory and printing have different costs; a reusable benchmark must preserve that distinction.

For example:

```text
Integer memory mode formats value={:+012d} into a bounded buffer; print mode emits the same presentation through the selected transport.
```

Keep the callable primitive, single-process sampling harness and optional second translation unit directly reviewable as handwritten C++. These primitives define workloads, not hardware conclusions. Five warmups and thirty samples do not make first invocation a cold-JIT measurement.

Read in this order:

- [test/conformance/benchmark_calls.hpp](https://github.com/nscottnichols/ffmt/blob/75353cc601c85b52dc066f724bfd4a56fbf37a6e/test/conformance/benchmark_calls.hpp)
- [test/conformance/benchmark.cpp](https://github.com/nscottnichols/ffmt/blob/75353cc601c85b52dc066f724bfd4a56fbf37a6e/test/conformance/benchmark.cpp)
- [test/conformance/benchmark_extra.cpp](https://github.com/nscottnichols/ffmt/blob/75353cc601c85b52dc066f724bfd4a56fbf37a6e/test/conformance/benchmark_extra.cpp)

Validated this exact commit on allocated CPU node `skylake10` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 8 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
"$CXX" -std=c++20 -O2 -fno-fast-math -Iinclude test/conformance/benchmark.cpp -o "$OUT"/benchmark-smoke
"$OUT"/benchmark-smoke 0 0 0 1 8 1
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 12; it remains draft until prerequisite human review.

Base: [`review-v2/migration`](https://github.com/nscottnichols/ffmt/tree/review-v2/migration); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
