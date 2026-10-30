The standalone checked engine needs the same compiler and backend configuration as the qualified implementation.

For example:

```text
#include <ffmt/detail/config.hpp>
```

Compiler macros and standard includes are copied without changes from aeff043. The extraction hash records the exact body. This header is internal; callers continue including base.hpp. It does not activate the replacement engine.

Read in this order:

- [include/ffmt/detail/config.hpp](https://github.com/nscottnichols/ffmt/blob/954454c422b816fd8296074cd7852dc923396f6c/include/ffmt/detail/config.hpp)

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

Base: [`review-v2/core-prepare`](https://github.com/nscottnichols/ffmt/tree/review-v2/core-prepare); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
