Fast timing numbers are meaningless if the candidate truncates output or executes a different workload.

For example:

```text
Before measuring integer memory formatting, compare its emitted verification bytes with a separate pinned fmt executable.
```

Snapshot sources and benchmark primitives, require a clean pinned fmt oracle, compare output before timing, validate sample counts and checksums, and retain exact commands and source hashes. Host wall timing includes launch and synchronization for accelerators. Verification process time and first batch are recorded separately; neither is a cold-JIT claim.

Read in this order:

- [tools/benchmark.py](https://github.com/nscottnichols/ffmt/blob/d50fe860d0424ceb002ab69cef6a9e5b4c65e83d/tools/benchmark.py) — main and verification before timing
- [tools/benchmark.py](https://github.com/nscottnichols/ffmt/blob/d50fe860d0424ceb002ab69cef6a9e5b4c65e83d/tools/benchmark.py) — build and metrics
- [tools/oracle.py](https://github.com/nscottnichols/ffmt/blob/d50fe860d0424ceb002ab69cef6a9e5b4c65e83d/tools/oracle.py) — oracle_identity
- [test/conformance/test_benchmark.py](https://github.com/nscottnichols/ffmt/blob/d50fe860d0424ceb002ab69cef6a9e5b4c65e83d/test/conformance/test_benchmark.py)

Validated this exact commit on allocated CPU node `skylake10` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 8 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_benchmark.py
python3 tools/benchmark.py --route host-buffer --family integer --mode memory --capacity 128 --memory-iterations 128 --fmt-dir "$FMT_DIR"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 12; it remains draft until prerequisite human review.

Base: [`review-v2/benchmark-primitives`](https://github.com/nscottnichols/ffmt/tree/review-v2/benchmark-primitives); 2 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
