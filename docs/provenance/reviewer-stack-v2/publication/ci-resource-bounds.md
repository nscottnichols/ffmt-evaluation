Launching one compiler per hosted CPU can exhaust memory once formatting templates grow; stale runs consume the same runner quota.

For example:

```text
On a runner with many CPUs, make -j2 bounds compiler processes while a newer PR commit cancels the superseded workflow.
```

Set a consistent two-job compile bound and a workflow/PR concurrency key without reducing the compiler matrix. Less parallelism may increase wall time. Cancelled stale runs are incomplete evidence, not passing checks.

Read in this order:

- [.github/workflows/host.yml](https://github.com/nscottnichols/ffmt/blob/7974eb6762e6a15d67afba53a32b19996e3926e8/.github/workflows/host.yml) — concurrency and Make commands
- [.github/workflows/device.yml](https://github.com/nscottnichols/ffmt/blob/7974eb6762e6a15d67afba53a32b19996e3926e8/.github/workflows/device.yml) — concurrency and Make commands
- [docs/contributing/CI_RESOURCES.md](https://github.com/nscottnichols/ffmt/blob/7974eb6762e6a15d67afba53a32b19996e3926e8/docs/contributing/CI_RESOURCES.md)

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

Base: [`review-v2/ci-review-waves`](https://github.com/nscottnichols/ffmt/tree/review-v2/ci-review-waves); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
