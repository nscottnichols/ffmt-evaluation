The public headers still select the old printf-based paths, so callers do not yet receive the component-tested engine’s shortest floating output, checked failures and counted transport.

For example:

```text
#include <ffmt/base.hpp>
ffmt::println("{}", 1152921504606846976.0);
// Old specifiers path: 1.15292e+18
// New public engine:  1.152921504606847e+18 (the fmt result)
```

Select the checked engine through the public wrapper while preserving macro spellings, static formatters and built-in SYCL formatters. The legacy oracle fixtures now compare full output and fmt shortest values; null strings compare against fmt rejection rather than glibc text. These fixtures are the retained qualified regressions, introduced here with the public behavior they require. Void compatibility calls discard checked status. Host checks do not replace preserved accelerator campaign evidence.

Read in this order:

- [include/ffmt/base.hpp](https://github.com/nscottnichols/ffmt/blob/f50f24930fb7875c6381e16cbb5db50ddec1eb1e/include/ffmt/base.hpp)
- [docs/api/migration.md](https://github.com/nscottnichols/ffmt/blob/f50f24930fb7875c6381e16cbb5db50ddec1eb1e/docs/api/migration.md)
- [test/test_body_host.inc](https://github.com/nscottnichols/ffmt/blob/f50f24930fb7875c6381e16cbb5db50ddec1eb1e/test/test_body_host.inc)
- [test/test_floats.cpp](https://github.com/nscottnichols/ffmt/blob/f50f24930fb7875c6381e16cbb5db50ddec1eb1e/test/test_floats.cpp)
- [test/test_buffer_path.cpp](https://github.com/nscottnichols/ffmt/blob/f50f24930fb7875c6381e16cbb5db50ddec1eb1e/test/test_buffer_path.cpp)
- [test/conformance/test_core_migration.cpp](https://github.com/nscottnichols/ffmt/blob/f50f24930fb7875c6381e16cbb5db50ddec1eb1e/test/conformance/test_core_migration.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 98 recorded steps passed; 1 optional capability checks returned 77 (unsupported).

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_BUFFER='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_SPECIFIERS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_core_migration CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_core_migration
python3 tools/conformance.py --route host-buffer --route host-specifiers --opt 2 --no-memory --fmt-dir "$FMT_DIR" --host-cxx "$CXX"
make -j2 CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT=-O0 EXTRA_CXXFLAGS=-fsanitize=address,undefined test-host test-fast-math
make -j2 test-fast-math CXX="$CXX" FMT_DIR="$FMT_DIR"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 6; it remains draft until prerequisite human review.

Base: [`review-v2/base-migration`](https://github.com/nscottnichols/ffmt/tree/review-v2/base-migration); 3 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
