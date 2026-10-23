Intel SYCL and icpx OpenMP build targets still omitted buffer-specific regression cases after both API paths gained the shared engine.

For example:

```text
make USE_OMP_ICPX=1 compile-omp # includes test_buffer_path.cpp
```

Add BUFFER_TESTS to these two source lists only after migration makes their grammar valid. This increases accelerator compile work and does not establish accelerator runtime qualification.

Read in this order:

- [Makefile](https://github.com/nscottnichols/ffmt/blob/baaea496731052b4d53657b8498708a7848e0d80/Makefile) — USE_OMP_ICPX and default SYCL source lists
- [docs/contributing/INTEL_REGRESSIONS.md](https://github.com/nscottnichols/ffmt/blob/baaea496731052b4d53657b8498708a7848e0d80/docs/contributing/INTEL_REGRESSIONS.md)

Validated this exact commit on allocated CPU node `skylake10` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 7 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -n USE_OMP_ICPX=1 compile-omp CXX="$CXX" FMT_DIR="$FMT_DIR"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 7; it remains draft until prerequisite human review.

Base: [`review-v2/migration`](https://github.com/nscottnichols/ffmt/tree/review-v2/migration); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
