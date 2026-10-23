One-header region percentages omit new headers and cannot describe executable-line or branch-edge coverage.

For example:

```text
Two headers with a region at the same coordinates remain two regions; an unexecuted branch side stays uncovered.
```

Include source filenames in union keys, preserve any-instantiation coverage, and read executable lines from LLVM LCOV export rather than estimating spans. Only instantiated runtime code is measured. Device-only code, compile-time evaluation and uninstantiated templates remain outside the denominator. This PR preserves the blocking policy.

Read in this order:

- [.github/scripts/coverage_union.py](https://github.com/nscottnichols/ffmt/blob/5739add3e1f03dff8deca692a0a75675be2c806f/.github/scripts/coverage_union.py) — regions
- [.github/scripts/coverage_union.py](https://github.com/nscottnichols/ffmt/blob/5739add3e1f03dff8deca692a0a75675be2c806f/.github/scripts/coverage_union.py) — metrics
- [test/conformance/test_coverage_metrics.py](https://github.com/nscottnichols/ffmt/blob/5739add3e1f03dff8deca692a0a75675be2c806f/test/conformance/test_coverage_metrics.py)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 6 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
python3 -m unittest discover -s test/conformance -p test_coverage_metrics.py
make -j2 CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT=-O0 coverage
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 2; it remains draft until prerequisite human review.

Base: [`review-v2/build-registration`](https://github.com/nscottnichols/ffmt/tree/review-v2/build-registration); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
