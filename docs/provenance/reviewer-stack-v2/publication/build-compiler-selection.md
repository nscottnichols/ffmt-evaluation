The AdaptiveCpp branch prepended a path from a developer machine and could select an unintended installation.

For example:

```text
PATH=/my/compiler/bin:$PATH make USE_ACPP=1 compile-omp
```

Remove the site-specific PATH assignment and retain the existing backend flags and explicit CXX override behavior. Callers must load or provide their own compiler environment; this check does not claim an AdaptiveCpp runtime result.

Read in this order:

- [Makefile](https://github.com/nscottnichols/ffmt/blob/91ebaec92fa783b997f07bebff0d19c9bfc56564/Makefile) — USE_ACPP
- [docs/contributing/COMPILER_SELECTION.md](https://github.com/nscottnichols/ffmt/blob/91ebaec92fa783b997f07bebff0d19c9bfc56564/docs/contributing/COMPILER_SELECTION.md)

Validated this exact commit on allocated CPU node `skylake10` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -n USE_ACPP=1 compile-omp CXX="$CXX" FMT_DIR="$FMT_DIR"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 2; it remains draft until prerequisite human review.

Base: [`review-v2/build-registration`](https://github.com/nscottnichols/ffmt/tree/review-v2/build-registration); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
