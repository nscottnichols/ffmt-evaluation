Header movement and template instantiation alter the coverage denominator, so aggregate percentage decreases can block a behavior-preserving change.

For example:

```text
Before: a 0.02 percentage-point drop fails CI. After: valid per-file base/head JSON is uploaded and the same drop is visible but does not block merging.
```

Keep invalid or empty measurement blocking, report region/line/branch metrics across all library headers, and make per-file regression assessment a human review decision. This deliberately loses automatic detection of real percentage regressions. Passing CI no longer guarantees nondecreasing coverage; correctness and sanitizer checks remain independent blocking checks.

Read in this order:

- [docs/contributing/COVERAGE.md](https://github.com/nscottnichols/ffmt/blob/124eb4a049b3e08070e75e674d22290c982697c5/docs/contributing/COVERAGE.md)
- [.github/workflows/host.yml](https://github.com/nscottnichols/ffmt/blob/124eb4a049b3e08070e75e674d22290c982697c5/.github/workflows/host.yml) — coverage
- [Makefile](https://github.com/nscottnichols/ffmt/blob/124eb4a049b3e08070e75e674d22290c982697c5/Makefile) — coverage

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes and affected C++ Make suites used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded checks passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, and `OUT` is a fresh evidence directory):

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT=-O0 coverage
```

The immutable evidence retains the complete argv, flags, header probes, raw logs, source hashes and results. ASan/UBSan applies to the affected C++ Make suites and header probes above. Standalone differential, benchmark, CMake and compiler-rejection commands use their separately recorded flags; this does not claim sanitizer coverage for every command. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Ready for the first review wave.

Base: [`review-v2/coverage-metrics`](https://github.com/nscottnichols/ffmt/tree/review-v2/coverage-metrics); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
