Production formatting is spread across 38 headers, while a second generated-program runner duplicates the original test harness. Maintain the implementation directly in one self-contained `<ffmt/base.hpp>` and extend the original shared-case harness instead.

A consumer can now copy **only `base.hpp`**, including its notices, and use the format families from that file:

```cpp
#include <ffmt/base.hpp>
int values[] = {1, 2};
char output[4];
auto result = ffmt::format_to_n(output, sizeof output, "{}", values);
// Stores "[1, "; written == 4, required == 6. No terminator is appended.
```

The 37 older include paths remain thin compatibility wrappers. There is no amalgamation generator or second canonical source. The mechanical consolidation preserves the 35 original implementation blocks; subsequent backend fixes explicitly include HIP's device printf declarations and full SYCL type declarations before use. Formatting algorithms and tables are unchanged. The tradeoff is a larger standard-library parse surface in exchange for one implementation to edit and distribute. C++20 remains the minimum; C++23 expected adapters keep their language/library guards.

Tests build on the existing pinned host fmt object, shared host/device case bodies, capture/diff reporter, negative corpus, backend builds and Make/CI. All 54 added fixtures move into that harness: 40 shared cases and 14 host-only feature cases. Nine added rejection fixtures reuse the original corpus. All 33 meaningful direct C++ regression bodies and 34 variants remain for required size, truncation, canaries, errors, iterator/formatter state and numeric sweeps. One explicit inventory serves Make and CMake, with small comparison helpers and visible optional skips. CUDA/HIP share launching; backend failures, asynchronous errors and host fallback cannot silently pass.

Campaign runners, backend campaign adapters, source snapshots and evidence collection move to the companion evaluation repository with exact old file hashes. Handwritten benchmark primitives remain in `benchmarks/`. The [maintenance inventory](https://github.com/nscottnichols/ffmt/blob/3649622374b8beb29f2a1a1086031aba6a07c3e4/docs/MAINTENANCE.md) explains each retained component and each removal/relocation.

Read in this order:

1. `include/ffmt/base.hpp`: dependency-ordered sections and backend prerequisites; old headers are wrappers.
2. `test/test_reference_body.inc`, `test/capture.hpp`, and the original backend bodies: shared oracle, exact bytes and failure handling.
3. `test/test_features.cpp`, `test/reference.hpp`, `test/direct/tests.mk`: migrated fixtures and preserved state/numeric regressions.
4. `Makefile`, `cmake/ffmtTests.cmake`, `test/test_infrastructure.py`: one inventory, original runner, rebuild/negative/skip contracts.
5. `docs/MAINTENANCE.md` and `docs/CONFORMANCE.md`: ongoing maintenance and commands.

Validation on allocated x86_64 Linux nodes:

- Final `make -j2 test-portable test-cxx23 CXX=...`: Clang22 `-O0` strict ASan/UBSan passes 39 binaries; GCC13 `-O2` passes 38 with one explicit BitInt skip. Each compiler passes 123 expected rejection variants plus valid/syntax controls and 16 infrastructure checks. Both run the isolated single-header consumer without wrappers or fmt.
- CMake/CTest passes **41/41**, installation and an independent installed consumer. This qualified revision `0111b73`; CMake wiring is unchanged. Final Make checks qualify `b0f82ee`; the PR head changes only a documentation URL afterward.
- Seven backend routes pass shared-case compilation and isolated one-header device consumers: CUDA Clang, corrected NVCC, native HIP, Intel SYCL/OpenMP SPIR-V, LLVM OpenMP NVPTX and retained local Intel LLVM SYCL. These are compile checks, not accelerator execution. Warning exceptions and exact flags remain visible.
- The evaluation-owned smoke passes two stdout cases and 26 numeric records with five presentations each. Moved benchmark primitives pass 12 byte comparisons; 76 evaluation regressions pass.

Initial failures remain captured. In particular, early NVCC host-language invocations are invalidated and replaced by forced-CUDA checks. ROCm7's optimized gfx90a failure reproduces on both old and new headers; gfx942 passes at `-O0` and `-O2`. No GPU/Arm or timing campaign was repeated, and historical pins/measurements are unchanged. Independent agents reviewed simplicity, readability, coverage retention and buildability. This sample does not establish exhaustive fmt or backend compatibility.

---
Base: [`review-v2/complete` at `471627c`](https://github.com/nscottnichols/ffmt/tree/review-v2/complete); existing PR history is unchanged. Draft pending prerequisite stack review; leave unmerged. [Evaluation companion #2](https://github.com/nscottnichols/ffmt-evaluation/pull/2). [Source mapping, exact commands, independent reviews and preserved evidence](https://github.com/nscottnichols/ffmt-evaluation/blob/provenance/single-header-20261030/docs/provenance/single-header-followup.md).
