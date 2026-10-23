Expose enum underlying values without globally accepting every enum.

For example:

```text
#include <ffmt/enum.hpp>
namespace status_example {
using ffmt::enums::format_as;
enum class status : int { warning = -3 };
}
ffmt::println("{:+05}", status_example::status::warning); // -0003
```

Small ADL opt-in shares the integer parser and avoids symbolic-name reflection. `ffmt::underlying(value)` explicitly exposes an enum's underlying integer.
Opting into `ffmt::enums::format_as` in the enum's namespace enables ADL mapping
with the integer formatter's specifications. This prints integer values rather
than discovering symbolic names. The opt-in avoids globally making every enum
formattable.

Read in this order:

- [include/ffmt/enum.hpp](https://github.com/nscottnichols/ffmt/blob/bdcea2b2afb856a364e14b7578af9e4199bb7745/include/ffmt/enum.hpp)
- [test/conformance/test_enum.cpp](https://github.com/nscottnichols/ffmt/blob/bdcea2b2afb856a364e14b7578af9e4199bb7745/test/conformance/test_enum.cpp)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 10 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_enum CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_enum
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 7; it remains draft until prerequisite human review.

Base: [`review-v2/migration`](https://github.com/nscottnichols/ffmt/tree/review-v2/migration); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
