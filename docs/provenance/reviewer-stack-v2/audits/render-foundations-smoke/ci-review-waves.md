Publishing many complete draft prerequisites can launch every expensive compiler matrix simultaneously.

For example:

```text
A draft PR keeps its captured local validation; marking it ready triggers the host and device compiler jobs through ready_for_review.
```

Keep normal push and PR checks, but skip compiler jobs while the PR is draft and explicitly listen for ready_for_review. Drafts have no hosted compiler result; skipped jobs must not be described as passing. Local intermediate checks remain required before publication.

Read in this order:

- [.github/workflows/host.yml](https://github.com/nscottnichols/ffmt/blob/0ed1cb08f13eaeabfcba22ab078bed28a46eed5a/.github/workflows/host.yml) — pull_request and job conditions
- [.github/workflows/device.yml](https://github.com/nscottnichols/ffmt/blob/0ed1cb08f13eaeabfcba22ab078bed28a46eed5a/.github/workflows/device.yml) — pull_request and job conditions
- [docs/contributing/CI.md](https://github.com/nscottnichols/ffmt/blob/0ed1cb08f13eaeabfcba22ab078bed28a46eed5a/docs/contributing/CI.md)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes and affected C++ Make suites used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 4 recorded checks passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, and `OUT` is a fresh evidence directory):

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
printf '#include <ffmt/base.hpp>\n' > base-header-probe.cpp
"$CXX" -std=c++20 "$HOST_OPT" -fno-fast-math -Wall -Werror -Iinclude $EXTRA_CXXFLAGS -c base-header-probe.cpp -o base-header-probe.o
```

The immutable evidence retains the complete argv, flags, header probes, raw logs, source hashes and results. ASan/UBSan applies to the affected C++ Make suites and header probes above. Standalone differential, benchmark, CMake and compiler-rejection commands use their separately recorded flags; this does not claim sanitizer coverage for every command. Hosted workflow execution is not established by these local checks. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Ready for the first review wave.

Base: [`main`](https://github.com/nscottnichols/ffmt/tree/main); 0 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
