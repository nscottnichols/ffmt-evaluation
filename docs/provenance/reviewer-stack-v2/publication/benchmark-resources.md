Object size, static compiler frame size, accelerator scratch and registers describe different resources and must not be conflated with measured runtime.

For example:

```text
--resources-only compiles one- and two-call probes and preserves the compiler report without claiming device execution.
```

Keep raw tool output, object hashes and backend image metadata beside parsed resource fields; distinguish compile-only probe outcomes from timing rows. Tool availability and diagnostic wording vary. Static frame reports exclude cumulative call depth; linked-image and conversion-table sizes are separate measurements.

Read in this order:

- [test/conformance/benchmark_resource.cpp](https://github.com/nscottnichols/ffmt/blob/cf70347b467f436447b41ea74a493e74cdc2a3e7/test/conformance/benchmark_resource.cpp)
- [tools/benchmark.py](https://github.com/nscottnichols/ffmt/blob/cf70347b467f436447b41ea74a493e74cdc2a3e7/tools/benchmark.py) — resources
- [tools/benchmark.py](https://github.com/nscottnichols/ffmt/blob/cf70347b467f436447b41ea74a493e74cdc2a3e7/tools/benchmark.py) — image_tables

Validated this exact commit on allocated CPU node `skylake10` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 8 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_benchmark.py
python3 tools/benchmark.py --route host-buffer --resources-only --family integer --mode memory --capacity 128 --fmt-dir "$FMT_DIR"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 12; it remains draft until prerequisite human review.

Base: [`review-v2/benchmark-driver`](https://github.com/nscottnichols/ffmt/tree/review-v2/benchmark-driver); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
