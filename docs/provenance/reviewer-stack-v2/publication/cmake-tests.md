The previous test list used combined source files and existence guards, which can turn a missing regression into an apparently successful configure.

For example:

```text
cmake -S . -B build/cmake -DFFMT_BUILD_TESTS=ON
cmake --build build/cmake -j2
ctest --test-dir build/cmake --output-on-failure
```

Explicit source registrations preserve the decomposed suites, while Python discovers all capability unit tests. Configure verifies a clean pinned oracle; only tests discover Python and Git. Full tests require the complete feature checkout and independent oracle. Optional extension skips remain visible, and C++23 stays opt-in. This is host validation, not accelerator runtime qualification.

Read in this order:

- [cmake/ffmtTests.cmake](https://github.com/nscottnichols/ffmt/blob/6498c0c38449019200b962f978ef3dbef0511003/cmake/ffmtTests.cmake) — ffmt_add_regression and source list
- [cmake/ffmtTests.cmake](https://github.com/nscottnichols/ffmt/blob/6498c0c38449019200b962f978ef3dbef0511003/cmake/ffmtTests.cmake) — extension flags and Python discovery
- [CMakeLists.txt](https://github.com/nscottnichols/ffmt/blob/6498c0c38449019200b962f978ef3dbef0511003/CMakeLists.txt) — test options
- [docs/BUILD.md](https://github.com/nscottnichols/ffmt/blob/6498c0c38449019200b962f978ef3dbef0511003/docs/BUILD.md)

Validated this exact commit on allocated CPU node `skylake10` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 9 recorded steps passed.

Some command output contains skip markers, including build-system probes. The evidence retains the exact text; unsupported conformance is counted separately when a declared optional capability returns 77.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
cmake -S . -B "$OUT"/cmake -DFFMT_BUILD_TESTS=ON -DFFMT_BUILD_CXX23_TESTS=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER="$CXX" -DFFMT_FMT_DIR="$FMT_DIR"
cmake --build "$OUT"/cmake -j2
ctest --test-dir "$OUT"/cmake --output-on-failure --no-tests=error -j2
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 13; it remains draft until prerequisite human review.

Base: [`review-v2/base-cmake-tests`](https://github.com/nscottnichols/ffmt/tree/review-v2/base-cmake-tests); 12 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
