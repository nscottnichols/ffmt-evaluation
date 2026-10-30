Compiler drivers can spawn children that outlive a timeout; text decoding can erase output distinctions.

For example:

```text
compare_bytes(b"value\n", b"value") reports a mismatch; an embedded NUL remains observable.
```

Keep byte capture, process lifetime and evidence-path handling in one small reusable module; save both streams before returning. Timeout cleanup uses POSIX process groups; its regression is explicitly skipped where killpg is unavailable.

Read in this order:

- [tools/process_evidence.py](https://github.com/nscottnichols/ffmt/blob/575165ea7f1623a5b06b9d666a769676d3e21c07/tools/process_evidence.py) — run
- [tools/process_evidence.py](https://github.com/nscottnichols/ffmt/blob/575165ea7f1623a5b06b9d666a769676d3e21c07/tools/process_evidence.py) — compare_bytes
- [test/conformance/test_process.py](https://github.com/nscottnichols/ffmt/blob/575165ea7f1623a5b06b9d666a769676d3e21c07/test/conformance/test_process.py)
- [test/conformance/test_output.py](https://github.com/nscottnichols/ffmt/blob/575165ea7f1623a5b06b9d666a769676d3e21c07/test/conformance/test_output.py)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 6 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_process.py
python3 -m unittest discover -s test/conformance -p test_output.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 3; it remains draft until prerequisite human review.

Base: [`review-v2/build-registration`](https://github.com/nscottnichols/ffmt/tree/review-v2/build-registration); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
