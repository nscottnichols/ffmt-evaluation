The replacement engine needs independent qualification while current callers remain usable.

For example:

```text
#include <ffmt/base.hpp> // still selects the original implementation
```

The legacy header is copied byte for byte from upstream 3fe258a; the public wrapper only selects it. The temporary extra include is removed once migration is validated.

Read in this order:

- [include/ffmt/base.hpp](https://github.com/nscottnichols/ffmt/blob/99bc52ec468208a16956aa19a5d1e00819ebfefe/include/ffmt/base.hpp)
- [include/ffmt/detail/legacy_base.hpp](https://github.com/nscottnichols/ffmt/blob/99bc52ec468208a16956aa19a5d1e00819ebfefe/include/ffmt/detail/legacy_base.hpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 5 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 test-host CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT=-O0 'EXTRA_CXXFLAGS=-fsanitize=address,undefined -fno-omit-frame-pointer'
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 2; it remains draft until prerequisite human review.

Base: [`review-v2/build-registration`](https://github.com/nscottnichols/ffmt/tree/review-v2/build-registration); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
