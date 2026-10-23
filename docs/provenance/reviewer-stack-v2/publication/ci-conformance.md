Focused regressions alone do not exercise the independently compiled output corpus and framed memory comparison in hosted CI.

For example:

```text
python3 tools/conformance.py --route host-buffer --route host-specifiers --opt 2 --host-cxx g++
```

Add one explicit differential step to each Linux compiler/optimization job and upload its complete evidence directory even after a failure. This increases hosted compile work; cases sample behavior rather than prove full fmt compatibility. The separate runner does not inherit Make sanitizer flags. Draft compiler jobs remain skipped.

Read in this order:

- [.github/workflows/host.yml](https://github.com/nscottnichols/ffmt/blob/493137b96467eaefe225f5c423dcc354db1dd4d4/.github/workflows/host.yml) — matrix conformance step and evidence upload
- [docs/contributing/CONFORMANCE_CI.md](https://github.com/nscottnichols/ffmt/blob/493137b96467eaefe225f5c423dcc354db1dd4d4/docs/contributing/CONFORMANCE_CI.md)

Validated this exact commit on allocated CPU node `skylake10` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 8 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export FFMT_FLAGS_HOST_BUFFER='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_SPECIFIERS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
python3 -m unittest discover -s test/conformance -p 'test_*.py'
python3 tools/conformance.py --route host-buffer --route host-specifiers --opt 2 --host-cxx "$CXX" --fmt-dir "$FMT_DIR"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. Hosted workflow execution is not established by these local checks. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 13; it remains draft until prerequisite human review.

Base: [`review-v2/base-ci-conformance`](https://github.com/nscottnichols/ffmt/tree/review-v2/base-ci-conformance); 11 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
