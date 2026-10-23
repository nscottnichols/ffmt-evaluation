The legacy test harness can share assumptions with the implementation; expected bytes need an independent formatting implementation.

For example:

```text
A standalone fmt process formats INT64_MIN; a separate ffmt process must produce the identical bytes.
```

Compile fmt only into host reference executables, and compile ffmt targets without fmt headers. Require a clean checkout at the exact oracle pin without modifying it, and record format.h/format.cc hashes. Begin with four baseline cases supported before engine migration. Separate reference and target compilation reduces shared assumptions but costs compile time. Dirty or differently pinned oracle checkouts fail visibly. Accelerator routes and later feature cases arrive in independent changes.

Read in this order:

- [test/conformance/cases_baseline.py](https://github.com/nscottnichols/ffmt/blob/4f2b6d380f3b03e453bf0d80a7ab2d26ec480c46/test/conformance/cases_baseline.py)
- [tools/oracle.py](https://github.com/nscottnichols/ffmt/blob/4f2b6d380f3b03e453bf0d80a7ab2d26ec480c46/tools/oracle.py) — oracle_identity
- [tools/conformance.py](https://github.com/nscottnichols/ffmt/blob/4f2b6d380f3b03e453bf0d80a7ab2d26ec480c46/tools/conformance.py) — build_oracle and configuration
- [tools/backend_host.py](https://github.com/nscottnichols/ffmt/blob/4f2b6d380f3b03e453bf0d80a7ab2d26ec480c46/tools/backend_host.py)
- [test/conformance/test_oracle.py](https://github.com/nscottnichols/ffmt/blob/4f2b6d380f3b03e453bf0d80a7ab2d26ec480c46/test/conformance/test_oracle.py)
- [test/conformance/test_fixture_registry.py](https://github.com/nscottnichols/ffmt/blob/4f2b6d380f3b03e453bf0d80a7ab2d26ec480c46/test/conformance/test_fixture_registry.py)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 6 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export FFMT_FLAGS_HOST_BUFFER='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_SPECIFIERS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
python3 -m unittest discover -s test/conformance -p 'test_*.py'
python3 tools/conformance.py --route host-buffer --opt 2 --no-memory --no-negative --fmt-dir "$FMT_DIR" --host-cxx "$CXX"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 3; it remains draft until prerequisite human review.

Base: [`review-v2/tool-process`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-process); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
