Applications need a reusable CMake target and an installed package without inheriting oracle or test dependencies.

For example:

```text
find_package(ffmt CONFIG REQUIRED)
target_link_libraries(my_program PRIVATE ffmt::ffmt)
```

An INTERFACE target carries headers and C++20 requirements. Standard package helpers export relocatable target metadata; a small independent consumer checks the installed contract. The target does not configure accelerator runtimes or backend flags. CMake 3.20 is required; direct header consumers do not need CMake.

Read in this order:

- [CMakeLists.txt](https://github.com/nscottnichols/ffmt/blob/58472a3e12d68fd7941be8998456916d1fffd412/CMakeLists.txt)
- [cmake/ffmtConfig.cmake.in](https://github.com/nscottnichols/ffmt/blob/58472a3e12d68fd7941be8998456916d1fffd412/cmake/ffmtConfig.cmake.in)
- [examples/cmake-consumer/main.cpp](https://github.com/nscottnichols/ffmt/blob/58472a3e12d68fd7941be8998456916d1fffd412/examples/cmake-consumer/main.cpp)
- [docs/BUILD.md](https://github.com/nscottnichols/ffmt/blob/58472a3e12d68fd7941be8998456916d1fffd412/docs/BUILD.md)

Validated this exact commit on allocated CPU node `skylake10` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 11 recorded steps passed.

Some command output contains skip markers, including build-system probes. The evidence retains the exact text; unsupported conformance is counted separately when a declared optional capability returns 77.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
cmake -S . -B "$OUT"/package -DCMAKE_CXX_COMPILER="$CXX" -DCMAKE_INSTALL_PREFIX="$OUT"/install -DCMAKE_DISABLE_FIND_PACKAGE_Python3=ON -DFFMT_FMT_DIR=/unavailable
cmake --install "$OUT"/package
cmake -S examples/cmake-consumer -B "$OUT"/consumer -DCMAKE_CXX_COMPILER="$CXX" -DCMAKE_PREFIX_PATH="$OUT"/install
cmake --build "$OUT"/consumer -j2
"$OUT"/consumer/ffmt_consumer
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 7; it remains draft until prerequisite human review.

Base: [`review-v2/obsolete-deletion`](https://github.com/nscottnichols/ffmt/tree/review-v2/obsolete-deletion); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
