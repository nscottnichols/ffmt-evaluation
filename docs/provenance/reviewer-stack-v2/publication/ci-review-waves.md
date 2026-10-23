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

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 4 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
printf '#include <ffmt/base.hpp>\n' > base-header-probe.cpp
"$CXX" -std=c++20 "$HOST_OPT" -fno-fast-math -Wall -Werror -Iinclude $EXTRA_CXXFLAGS -c base-header-probe.cpp -o base-header-probe.o
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. Hosted workflow execution is not established by these local checks. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Ready for the first review wave.

Base: [`main`](https://github.com/nscottnichols/ffmt/tree/main); 0 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
