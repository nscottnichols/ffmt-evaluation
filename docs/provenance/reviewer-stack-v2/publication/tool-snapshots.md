Re-running a comparison against a moving worktree can silently change the source under test.

For example:

```text
--source-root ../ffmt --revision COMMIT snapshots that commit even when its working headers have subsequent edits.
```

Snapshot include/ through git archive for pinned revisions, or copy current headers for WORKTREE; identify runner checkout separately from library checkout. Only headers belong to the library snapshot. Exact runner/fixture hashes and compiler commands remain separate evidence, not an assertion of a clean worktree.

Read in this order:

- [tools/conformance.py](https://github.com/nscottnichols/ffmt/blob/4436d6208ed94795ee5ba9376aa76b0d00b5fe11/tools/conformance.py) — snapshot
- [tools/conformance.py](https://github.com/nscottnichols/ffmt/blob/4436d6208ed94795ee5ba9376aa76b0d00b5fe11/tools/conformance.py) — Campaign.__init__
- [test/conformance/test_snapshots.py](https://github.com/nscottnichols/ffmt/blob/4436d6208ed94795ee5ba9376aa76b0d00b5fe11/test/conformance/test_snapshots.py)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 6 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export FFMT_FLAGS_HOST_BUFFER='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_SPECIFIERS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
python3 -m unittest discover -s test/conformance -p test_snapshots.py
python3 tools/conformance.py --revision HEAD --case literal --route host-buffer --opt 2 --no-memory --no-negative --fmt-dir "$FMT_DIR" --host-cxx "$CXX"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 5; it remains draft until prerequisite human review.

Base: [`review-v2/tool-host-oracle`](https://github.com/nscottnichols/ffmt/tree/review-v2/tool-host-oracle); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
