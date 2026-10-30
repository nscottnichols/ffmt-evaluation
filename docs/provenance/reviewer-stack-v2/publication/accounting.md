Truncation must retain the complete required length without writing beyond caller capacity.

For example:

```text
#include <ffmt/detail/checked.hpp> // internal engine during staged introduction
char bytes[2];
ffmt::detail::iterator_sink<char*, char> sink{bytes, 2};
sink.repeat('x', 7); // bytes == {'x', 'x'}; written == 2; required == 7
```

All iterator copies share a sink. Required-length overflow is detected before arithmetic wraps. Counts describe code units, not display columns; family alignment hooks arrive with shared family support.

Read in this order:

- [include/ffmt/detail/result.hpp](https://github.com/nscottnichols/ffmt/blob/5e9a2cc28f453419f2555b49894ff347c80a8670/include/ffmt/detail/result.hpp)
- [include/ffmt/detail/output.hpp](https://github.com/nscottnichols/ffmt/blob/5e9a2cc28f453419f2555b49894ff347c80a8670/include/ffmt/detail/output.hpp)
- [test/conformance/test_core_accounting.cpp](https://github.com/nscottnichols/ffmt/blob/5e9a2cc28f453419f2555b49894ff347c80a8670/test/conformance/test_core_accounting.cpp)

Validated this exact commit on allocated CPU node `rome00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 10 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_core_accounting CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_core_accounting
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 2; it remains draft until prerequisite human review.

Base: [`review-v2/checked-config`](https://github.com/nscottnichols/ffmt/tree/review-v2/checked-config); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
