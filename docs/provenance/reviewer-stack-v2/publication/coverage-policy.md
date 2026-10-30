Header movement and template instantiation alter the coverage denominator, so aggregate percentage decreases can block a behavior-preserving change.

For example:

```text
Before: a 0.02 percentage-point drop fails CI. After: valid per-file base/head JSON is uploaded and the same drop is visible but does not block merging.
```

Keep invalid or empty measurement blocking, report region/line/branch metrics across all library headers, and make per-file regression assessment a human review decision. This deliberately loses automatic detection of real percentage regressions. Passing CI no longer guarantees nondecreasing coverage; correctness and sanitizer checks remain independent blocking checks.

Read in this order:

- [docs/contributing/COVERAGE.md](https://github.com/nscottnichols/ffmt/blob/465cc67d7769713b36e3789919edafb86a0c0d71/docs/contributing/COVERAGE.md)
- [.github/workflows/host.yml](https://github.com/nscottnichols/ffmt/blob/465cc67d7769713b36e3789919edafb86a0c0d71/.github/workflows/host.yml) — coverage
- [Makefile](https://github.com/nscottnichols/ffmt/blob/465cc67d7769713b36e3789919edafb86a0c0d71/Makefile) — coverage

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT=-O0 coverage
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 2; it remains draft until prerequisite human review.

Base: [`review-v2/coverage-metrics`](https://github.com/nscottnichols/ffmt/tree/review-v2/coverage-metrics); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
