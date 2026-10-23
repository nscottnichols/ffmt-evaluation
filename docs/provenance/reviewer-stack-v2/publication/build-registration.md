Discovering test source files with a wildcard can silently omit a declared test when its file is missing.

For example:

```text
A registration naming test/conformance/test_output.cpp is a required Make prerequisite; deleting that source fails the build rather than shrinking the test suite.
```

Each capability adds a small explicit registration. A shared Make fragment provides compiler, reference-library, C++ standard and optional-extension handling. Registrations are additional build metadata, but independent feature branches add separate files and do not edit one combined test source or suite list.

Read in this order:

- [mk/portable-tests.mk](https://github.com/nscottnichols/ffmt/blob/d1e8f0e8e1eba7c47829d1d410362f8cc73041d1/mk/portable-tests.mk)
- [docs/contributing/TESTS.md](https://github.com/nscottnichols/ffmt/blob/d1e8f0e8e1eba7c47829d1d410362f8cc73041d1/docs/contributing/TESTS.md)
- [test/conformance/test_build_registration.py](https://github.com/nscottnichols/ffmt/blob/d1e8f0e8e1eba7c47829d1d410362f8cc73041d1/test/conformance/test_build_registration.py)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_build_registration.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Ready for the first review wave.

Base: [`review-v2/oracle-pin`](https://github.com/nscottnichols/ffmt/tree/review-v2/oracle-pin); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
