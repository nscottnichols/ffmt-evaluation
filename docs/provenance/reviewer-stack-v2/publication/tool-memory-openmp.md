OpenMP stdout can succeed while numeric conversion or bounded output counts in accelerator memory are wrong.

For example:

```text
omp_is_initial_device() must be false
map(to: input[0:count]) + map(from: output[0:count])
-> format_record on the target -> serialize copied records
```

Require non-initial-device execution, map input encodings to the target and output records from it, then format each record in a target teams distribute parallel for region. Runtime execution remains hardware-dependent; source-generation and host record tests validate structure but do not establish accelerator execution.

Read in this order:

- [tools/backend_openmp.py](https://github.com/nscottnichols/ffmt/blob/a0d74e7370ddf6aa612fd5c368c0a86d46ae30f3/tools/backend_openmp.py) — numeric_launcher
- [test/conformance/numeric_memory.cpp.in](https://github.com/nscottnichols/ffmt/blob/a0d74e7370ddf6aa612fd5c368c0a86d46ae30f3/test/conformance/numeric_memory.cpp.in)
- [test/conformance/test_memory_openmp.py](https://github.com/nscottnichols/ffmt/blob/a0d74e7370ddf6aa612fd5c368c0a86d46ae30f3/test/conformance/test_memory_openmp.py)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 7 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_memory_openmp.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. These portable tests inspect adapter generation and launch contracts; they do not qualify accelerator execution. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 11; it remains draft until prerequisite human review.

Base: [`review-v2/base-tool-memory-openmp`](https://github.com/nscottnichols/ffmt/tree/review-v2/base-tool-memory-openmp); 2 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
