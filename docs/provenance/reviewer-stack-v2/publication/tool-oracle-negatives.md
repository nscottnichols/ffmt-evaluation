Matching valid output does not establish that an implementation rejects malformed or type-incompatible format literals.

For example:

```text
The unclosed "{" fixture must produce an intended format diagnostic in both the target compiler and the host fmt oracle.
```

Reuse the diagnostic classifier for revisioned negative fixture modules and preserve both compiler diagnostics separately. This adds compile-time rejection parity, not runtime parser exception parity. The baseline fixture registry has no new negative cases until engine migration.

Read in this order:

- [tools/conformance.py](https://github.com/nscottnichols/ffmt/blob/661db66d492a18c308ae55358a59372bd7bf541e/tools/conformance.py) — negatives
- [tools/compile_diagnostics.py](https://github.com/nscottnichols/ffmt/blob/661db66d492a18c308ae55358a59372bd7bf541e/tools/compile_diagnostics.py)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 -m unittest discover -s test/conformance -p test_negative_driver.py
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 5; it remains draft until prerequisite human review.

Base: [`review-v2/tool-isolation`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-isolation); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
