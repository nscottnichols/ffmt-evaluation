Legacy test rules watched only base.hpp, so changing an internal header could silently rerun a stale binary.

For example:

```text
touch include/ffmt/detail/parse.hpp
make test-host # recompiles affected objects
```

Use the complete installed header list in the existing shared prerequisite variable; exercise an unchanged object and a subsequent internal-header edit with real Make timestamp decisions. This conservative dependency list rebuilds some tests that do not instantiate the edited header, in exchange for reliable incremental checks.

Read in this order:

- [Makefile](https://github.com/nscottnichols/ffmt/blob/9fa6e8fa26c13f78962ad4ff0447a60a3f5cafa5/Makefile) — FFMT_HDRS and DEPS
- [test/conformance/test_make_header_dependencies.py](https://github.com/nscottnichols/ffmt/blob/9fa6e8fa26c13f78962ad4ff0447a60a3f5cafa5/test/conformance/test_make_header_dependencies.py)

Validated this exact commit on allocated CPU node `skylake10` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_make_header_dependencies.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 2; it remains draft until prerequisite human review.

Base: [`review-v2/build-registration`](https://github.com/nscottnichols/ffmt/tree/review-v2/build-registration); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
