The public header no longer references the old implementation after migration.

For example:

```text
#include <ffmt/base.hpp> // unchanged for callers
```

Only the unused legacy implementation is deleted; archived snapshots retain it for comparison. The static formatter protocol and legacy emit-hook adapter remain supported by the new implementation.

Read in this order:

- [include/ffmt/base.hpp](https://github.com/nscottnichols/ffmt/blob/cd7fcfd406baf316271d8b88dc03f712fd157d6a/include/ffmt/base.hpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 7 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 test-host CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT=-O0 'EXTRA_CXXFLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer'
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 6; it remains draft until prerequisite human review.

Base: [`review-v2/migration`](https://github.com/nscottnichols/ffmt/tree/review-v2/migration); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
