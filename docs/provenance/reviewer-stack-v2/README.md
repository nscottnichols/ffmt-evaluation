# Review stack evidence and archival inputs

The [single stack overview](../reviewer-stack-v2.md) describes the review graph and old-to-new revision mapping. This directory preserves validation attempts, including failures and a queued cancellation, without assigning historical hardware measurements to new commits.

| Attempt | Cobalt job | Outcome | Stage results |
| --- | --- | --- | --- |
| [Foundation capture](attempts/foundations-1011365/README.md) | 1011365 | Passed | 6 passed |
| [Intermediate capture](attempts/intermediates-1011366/README.md) | 1011366 | Failed | 45 passed, 1 passed with optional skips, 2 failed, 6 not selected |
| [Cancelled follow-up](attempts/cancelled-1011368/README.md) | 1011368 | Cancelled while queued | No execution or validation result |
| [Cpl release capture](attempts/release-cpl-1011376/README.md) | 1011376 | Passed | 22 passed, 43 not selected |
| [Rome release capture](attempts/release-rome-1011375/README.md) | 1011375 | Passed with optional skips | 11 passed, 1 passed with skips, 53 not selected |
| [Skylake release capture](attempts/release-skylake-1011377/README.md) | 1011377 | Passed with optional skips | 11 passed, 3 passed with skips, 51 not selected |

The intermediate migration and obsolete-deletion failures exposed qualified legacy fixtures that had been left at the upstream baseline during decomposition. Their raw diagnostics and original commits remain captured. The cancelled follow-up froze a snapshot already known to need these repairs. Cancellation is not a passing check. Later release qualification is captured only after its manifest records completion; the qualification summary selects exact passing stage commits independently. The [supplemental release source audit](release-source-audit/release-source-preservation.json) verifies all eight restored legacy regression files, original ignore patterns and all 54 positive/9 negative logical fixture dictionaries against final release `471627c31cd1e09a2d4587c0369ec662251f7356`; the earlier pending source audit remains unchanged.

## What is preserved

Each capture has an exhaustive `capture.json` inventory: original absolute path, capture-relative path, storage location, byte count and SHA-256 for every included file. The [capture index](capture-inventory.json) records those inventories and archive hashes. Absolute paths inside frozen manifests are unchanged; inventory entries map them into this repository.

Manifests, immutable stage indices, scheduler submission/cancellation receipts, runner and wrapper scripts, and nested result manifests are visible files. [Audits](audits/) remain visible JSON records. [Archival inputs](archival-inputs/) preserve handwritten source/fixture exports, stage notes, planning helpers (including `prepare-plan.py` and `export-build-repairs.py`), frozen indices and workflow scripts. These handwritten inputs are not designated generated material or hidden in a log archive. [Original PR metadata](original-pr-metadata.json) is retained byte for byte with its [capture hash](original-pr-metadata-capture.json).

Only raw stdout/stderr, scheduler output, resource reports and generated probe/case sources go into each `raw-logs.tar.gz`. Archive members use `validation/` or `submission/` plus their original relative path. The uncompressed bytes are preserved, including embedded NULs, trailing whitespace and failure diagnostics. Generated-source hashes already recorded by the runners remain unchanged and the capture inventory adds hashes of the actual source files.

Disposable checkout worktrees, compiler objects/libraries/executables, profiling products and CMake build directories are excluded. Their recorded source hashes and commands remain in the visible manifests. Existing ignored evidence and local installations are never moved or deleted. Library/fmt/evaluation pins are unchanged. These CPU checks do not repeat or relabel historical GPU/Arm campaigns.

The [reviewed capture helper and safety tests](capture-tool-review/) are preserved visibly alongside its independent audit. Both portable safety tests pass; the independent raw-reference audit confirms every one of the 1,104 foundation/intermediate stdout/stderr references and hashes.

## Capture and verification

The reusable standard-library helper rejects an active validation attempt, a submission without an explicit cancellation receipt, and an existing destination. It copies into a temporary sibling and exposes the final directory only after a complete capture. It never changes Git refs, submits work, invokes a compiler or writes to original inputs.

```sh
python3 tools/review_stack/capture.py \
  --validation /original/completed-validation \
  --submission /original/frozen-submission \
  --output docs/provenance/reviewer-stack-v2/attempts/new-attempt
python3 tools/review_stack/capture.py \
  --output docs/provenance/reviewer-stack-v2/attempts/new-attempt --verify
python3 -m unittest discover -s tools/review_stack -p test_capture.py
```

Use `--input LABEL=PATH` repeatedly for visible archival inputs. An input-only capture has status `inputs_only`, which is not validation. Preserve updated audits or helpers in a new capture rather than overwriting an earlier frozen copy.

The final [capture qualification audit](capture-qualification.json) independently finds exact passing evidence for all 64 PR stages plus the complete collection. The [selection inputs](release-selection-inputs/) preserve the original 65-stage summary, partition and handwritten collector; [final offline checks](evaluation-final-checks/) preserve the 17-test and historical provenance logs. The [independent publication preflight](publication-independent-review/) approves 4 ready and 60 draft descriptions without merging them.
