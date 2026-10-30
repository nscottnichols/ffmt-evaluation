# Backend compilation follow-up

All seven selected routes have genuine compilation results on source `f3170f07df7774fb086849b077422e3330166aec`; the independent fmt reference remains `0fc31633e7d53ac895ae0a688b83b7d44f0b0c1f`. No accelerator code was executed.

| Route | Result | Scope |
| --- | --- | --- |
| Clang22 CUDA | Pass | Original shared cases, compiler/link checks and isolated base.hpp-only device consumer. No device execution. |
| Intel2025 SYCL/SPIR-V | Pass | Original shared cases, compiler/link checks and isolated base.hpp-only device consumer. No device execution. |
| Intel2025 OpenMP/SPIR-V | Pass | Original shared cases, compiler/link checks and isolated base.hpp-only device consumer. No device execution. |
| LLVM22 OpenMP/NVPTX | Pass | Original shared cases, compiler/link checks and isolated base.hpp-only device consumer. No device execution. |
| Retained local Intel LLVM SYCL/SPIR-V | Pass | Original shared cases, compiler/link checks and isolated base.hpp-only device consumer. No device execution. |
| NVCC CUDA12.9.1 | Pass | Seven original shared-case translation units compiled with -x cu and -dc. No final executable link or device execution. NVCC annotation warnings remain captured. |
| ROCm7 native HIP | Pass | Full original shared cases compile at -O0 and -O2 for gfx942; base-only device consumer passes at -O0, controlled runtime-first probe also passes at -O2. No device execution. |

The native HIP full shared corpus passes at explicit `-O2` for `gfx942`. Controlled baseline471/finalf317 probes match: `gfx90a -O2` fails in both, while `gfx90a -O0` and both `gfx942` modes pass. Raw failures and a plain printf control are preserved.

Initial NVCC invocations omitted `-x cu` and compiled the host path. Those exit-zero records are explicitly excluded from CUDA qualification. The corrected attempt compiles all seven shared units and the isolated one-header consumer with CUDA language forced.

GCC13 benchmark relocation verification passed single/multiple translation units and twelve byte comparisons against pinned fmt. Verification ran one batch per process; this was not a timing campaign.

See [the exact backend summary](backend-validation.json) for exact manifests, commands, hashes, preserved failures and limitations.
