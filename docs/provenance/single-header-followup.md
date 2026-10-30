# Single implementation header and original-harness follow-up

The [library follow-up PR81](https://github.com/nscottnichols/ffmt/pull/81) and
[evaluation companion PR2](https://github.com/nscottnichols/ffmt-evaluation/pull/2)
are draft and unmerged. The library follow-up is based on unchanged stack tip
`471627c31cd1e09a2d4587c0369ec662251f7356`. Its head is
`3649622374b8beb29f2a1a1086031aba6a07c3e4`; all prior PR branches and commit
objects remain intact. The [maintenance inventory](https://github.com/nscottnichols/ffmt/blob/3649622374b8beb29f2a1a1086031aba6a07c3e4/docs/MAINTENANCE.md)
explains each retained library component, its concrete purpose, and every removed
or relocated infrastructure category.

Maintain production code directly in `base.hpp`, with 37 thin compatibility
wrappers and no amalgamation generator. Extend the original pinned host fmt
object, shared host/device cases, capture/diff bodies, negative corpus, Make and
CI. All 54 added text fixtures were migrated: 40 shared cases and 14 host feature
cases. The nine additional rejection fixtures reuse the original corpus. All
33 direct C++ regression bodies and 34 build variants remain; those assertions
cover sizes, bounds, errors, conversion and iterator/formatter state. Make and
CMake build the same explicit inventory; shared cases retain the original
capture/diff bodies, and direct binaries run through Make or CTest.

Campaign runners, snapshot management, backend campaign adapters and evidence
collection are owned in `tools/campaign_runner`, not a library build dependency.
The [relocation inventory](../../tools/campaign_runner/relocation.json) retains
57 exact files from the old library tip. Historical component/runner notes remain
[byte-preserved here](../history/library-stack-tip-notes/README.md). Current
library tests use their original harness; evaluation keeps historical fixtures
so past captures retain their original identities.

## Source and history mapping

| Revision | Meaning |
| --- | --- |
| `471627c31cd1e09a2d4587c0369ec662251f7356` | Original 64-stage collection, unchanged base |
| `e725b2ad48c2e53a2eac448d6ba94aade74d91ac` | Mechanical header consolidation; 35 dependency-ordered implementation blocks preserved |
| `859bd2c2df3460212d08c1ed9444673349075921` | Original-harness migration and build/runner consolidation |
| `0111b73a1fc55b5ebbdade261b0c194d6c83a410` | Build-contract and backend failure checks; full CMake/CTest/install qualification |
| `f3170f07df7774fb086849b077422e3330166aec` | Explicit HIP runtime and full SYCL prerequisite includes; backend qualification |
| `40e16aab09366b0bcd59fcd597043acd6f4bad4e` | Direct regression for stdout restoration after callback exceptions |
| `b0f82ee8d3449cf7b46834d7d1bbaf85b4df9497` | Final portable qualification and evaluation smoke snapshot |
| `3649622374b8beb29f2a1a1086031aba6a07c3e4` | PR head; only changes the maintenance guide's evidence URL to an immutable tag after the qualified snapshot |

This is a source/layout/testing change, not merely a commit-ID rewrite. The
[source audit](single-header-followup/source-mapping.json) proves that the final
header differs from the mechanical consolidation only in the recorded backend
runtime include preamble. Formatting bodies and tables are unchanged. The
final PR head has identical production, test, build and tool files to the final
portable snapshot. All 38 headers and shared backend inputs are identical to
the backend-qualified snapshot. CMake wiring is unchanged since its qualified
revision. Assertions and tests are preserved separately from mechanical moves.

Evaluation PR1 has been merged as main
`b087713958bd469c4e5c7ae1b61ee7c9e14bb52e`, whose tree equals original import
head `341014c054cf80293a8490228fdb23eead121a64`. The companion follow-up merges
that current main without rebasing its new code commit `596c67243e5f9dc1eb886ef578c593e4acd0d955`.
An immutable `evaluation-campaign` tag at the original import head preserves the
old library PR provenance URLs after the merged branch was deleted. The new
`provenance/single-header-20261030` tag preserves this follow-up evidence after
branch cleanup. Existing qualified/archive refs and all source/runner pins are
unchanged; neither tag assigns a new qualification to historical measurements.

## Actual validation

The [machine summary](single-header-followup/summary.json),
[capture index](single-header-followup/capture-index.json), and
[backend command summary](single-header-followup/backend-validation.md) retain
exact revisions, commands, flags, hashes, stdout/stderr and scheduler receipts.
The original ignored outputs and installations remain in place. Captures do not
replace or edit them.

| Check | Actual result |
| --- | --- |
| Final Make `test-portable test-cxx23`, Clang22 `-O0` strict ASan/UBSan, job1012530 | 39 binaries pass, no optional skips; 123 expected rejection variants plus positive/syntax controls; 16 infrastructure checks pass |
| Final Make `test-portable test-cxx23`, GCC13 `-O2`, job1012531 | 38 binaries pass; BitInt explicitly unsupported (77); same 123 rejection variants and controls; 16 infrastructure checks pass |
| CMake/CTest, strict Clang22, job1012525 | 41/41 pass, no skips; installation and independent installed consumer pass at revision0111 |
| Isolated host single-header consumer | Only copied `base.hpp`, no wrappers/repository include path/fmt; named/range/chrono/std/style/printf/bounded/error APIs pass |
| Final evaluation-owned smoke, job1012531 | Exact new source `b0f82ee`; two stdout cases and 26 numeric input records with five presentations each pass |
| CUDA Clang22, corrected NVCC12.9, native HIP/ROCm7, Intel2025 SYCL/OpenMP SPIR-V, LLVM22 OpenMP NVPTX, retained local Intel LLVM SYCL | Seven selected routes pass original shared-case compilation and isolated base-only device consumer checks |
| Full native HIP shared corpus | `gfx942 -O0` and `-O2` compilation pass |
| Moved benchmark primitives | Single/multi-TU/reference/resource builds pass; 12 integer/float memory/stdout byte comparisons pass, no measurement campaign |
| Offline evaluation regressions | 76 pass, including owned/historical runner selection, explicit pin rejection, separate source bootstrap and historical-recipe preflight |
| Capture safety and historical provenance | Two capture tests pass; historical verifier passes 25 evidence files, two configs, 17 historical headers/corpus, five refs and 19 original commits |

Compiler checks are not accelerator execution. No hardware timing, GPU/Arm
campaign or performance measurement was repeated. Host validation is x86_64
Linux; it does not establish macOS/Arm or exhaustive fmt compatibility.
Clang CUDA/OpenMP commands explicitly retain warnings while allowing the known
unknown-CUDA-version/unused-toolchain warnings to be nonfatal. Exact flags are
visible rather than silently relaxed globally.

## Failures and limits remain visible

Three initial allocations failed in Cobalt's older SSH parser before any test
ran. The compatibility directive was temporary, privately backed up, and restored
to the user's exact original bytes after all allocations completed; no private
SSH contents are captured. These are infrastructure failures, not conformance.

Initial HIP/SYCL include-order failures motivated the explicit runtime includes
in the standalone header. Initial NVCC commands omitted forced CUDA language and
compiled host branches; those results are explicitly invalidated. Corrected
`-x cu` commands compiled all seven real CUDA shared units and the isolated
`__global__` consumer. Raw failures and the language correction remain preserved.

A controlled ROCm7 comparison compiles the same runtime-first probe against old
`471627c` and new `f3170f0`. Both pass at gfx90a `-O0`, both fail with the same
SGPR/VGPR code-generation diagnostic at gfx90a `-O2`, and both pass gfx942 at
`-O0` and `-O2`. A direct-printf control passes all four settings. This establishes
that the observed optimized gfx90a limitation predates consolidation; it does not
relabel older hardware campaigns or claim universal HIP support.

Independent agents assessed simplicity/readability, exact source/test movement,
coverage retention, build registration, runtime guards, and evaluation ownership.
Their raw audit attempts, corrected audit scope, findings and passing follow-ups
remain visible in the captures. There is no handwritten implementation hidden as
generated material, and the library needs none of these evaluation captures to
build or test.

[Publication metadata and exact PR bodies](single-header-followup/publication/record.json)
record the published heads/bases/readiness. The immutable evidence tag retains
the complete qualification snapshot; subsequent publication-only documentation
does not alter the qualified library or evaluator tools.
