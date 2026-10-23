Long output and percent signs must reach stdout without reinterpretation as format syntax.

For example:

```text
#include <ffmt/detail/checked.hpp> // base.hpp switches in the migration PR
auto result = ffmt::try_print("a{}b", char(0));
// The default host counted transport emits all three bytes: a, NUL, b.
// A transport without counted-byte support reports its limitation.
```

A bounded sink emits counted chunks. Backend printf uses fixed conversion formats; compatibility hooks receive safe escaped pieces. Some backend or legacy transports cannot preserve embedded NULs and report errors. Host captures validate contracts, not accelerator runtime behavior.

Read in this order:

- [include/ffmt/detail/transport.hpp](https://github.com/nscottnichols/ffmt/blob/105c853df03ef06ff29b6de819e78f6b23dd4dcb/include/ffmt/detail/transport.hpp)
- [include/ffmt/detail/legacy_emit.hpp](https://github.com/nscottnichols/ffmt/blob/105c853df03ef06ff29b6de819e78f6b23dd4dcb/include/ffmt/detail/legacy_emit.hpp)
- [test/conformance/test_engine_transport.cpp](https://github.com/nscottnichols/ffmt/blob/105c853df03ef06ff29b6de819e78f6b23dd4dcb/test/conformance/test_engine_transport.cpp)
- [test/conformance/test_engine_legacy_hook.cpp](https://github.com/nscottnichols/ffmt/blob/105c853df03ef06ff29b6de819e78f6b23dd4dcb/test/conformance/test_engine_legacy_hook.cpp)
- [test/capture.hpp](https://github.com/nscottnichols/ffmt/blob/105c853df03ef06ff29b6de819e78f6b23dd4dcb/test/capture.hpp) — raw stream equality after parsed diagnostics
- [test/conformance/test_transport_forwarding.cpp](https://github.com/nscottnichols/ffmt/blob/105c853df03ef06ff29b6de819e78f6b23dd4dcb/test/conformance/test_transport_forwarding.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 19 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_engine_legacy_hook build/cap_engine_transport build/cap_transport_forwarding CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_engine_legacy_hook
./build/cap_engine_transport
./build/cap_transport_forwarding
make -j2 CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT=-O0 EXTRA_CXXFLAGS=-fsanitize=address,undefined test-host
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 5; it remains draft until prerequisite human review.

Base: [`review-v2/base-transport`](https://github.com/nscottnichols/ffmt/tree/review-v2/base-transport); 3 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
