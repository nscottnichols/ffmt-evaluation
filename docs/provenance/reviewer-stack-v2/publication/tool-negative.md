Treating every failed compilation as a rejected format lets missing headers and compiler crashes pass.

For example:

```text
A consteval invalid-format diagnostic passes; "fmt/format.h: No such file or directory" is an infrastructure failure.
```

Compile a positive control and syntax-only fixture before testing both ffmt paths and fmt. Classify diagnostics independently of the differential runner. Compiler diagnostic recognition is a conservative heuristic, not a compiler-independent proof; unfamiliar wording fails visibly.

Read in this order:

- [tools/compile_diagnostics.py](https://github.com/nscottnichols/ffmt/blob/c5b81a4d5288e7be393d83ea28332510285b765e/tools/compile_diagnostics.py)
- [tools/negative.py](https://github.com/nscottnichols/ffmt/blob/c5b81a4d5288e7be393d83ea28332510285b765e/tools/negative.py)
- [test/conformance/test_negative_driver.py](https://github.com/nscottnichols/ffmt/blob/c5b81a4d5288e7be393d83ea28332510285b765e/test/conformance/test_negative_driver.py)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 6 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
python3 -m unittest discover -s test/conformance -p test_negative_driver.py
make -j2 test-negative CXX="$CXX" FMT_DIR="$FMT_DIR"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 3; it remains draft until prerequisite human review.

Base: [`review-v2/tool-process`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-process); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
