Resolve human-readable field names while retaining typed value references.

For example:

```text
#include <ffmt/args.hpp>
char out[16];
auto result = ffmt::format_to_n(out, sizeof out, "{value:04x}", ffmt::arg("value", 42));
// out contains "002a"; result.written == result.required == 4.
```

Name lookup is runtime; wrappers do not allocate or own their referents. `ffmt::arg(name, value)` stores a name view and a value reference. The name
characters and value must outlive use of the wrapper; temporary values remain
valid through the formatting expression. Names and named width/precision fields
are resolved at runtime. Literal parsing checks structural syntax, but cannot
fully validate a named field's type/specification because names are runtime data.
Use checked results to observe unresolved names or incompatible specifications.

Read in this order:

- [include/ffmt/args.hpp](https://github.com/nscottnichols/ffmt/blob/26f1a22c34b885d9b982a5856ae976ef8742510d/include/ffmt/args.hpp)
- [test/conformance/test_named_arguments.cpp](https://github.com/nscottnichols/ffmt/blob/26f1a22c34b885d9b982a5856ae976ef8742510d/test/conformance/test_named_arguments.cpp)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 11 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_BUFFER='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
export FFMT_FLAGS_HOST_SPECIFIERS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_named_arguments CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_named_arguments
python3 tools/conformance.py --route host-buffer --opt 2 --no-memory --no-negative --fmt-dir "$FMT_DIR" --host-cxx "$CXX"
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 7; it remains draft until prerequisite human review.

Base: [`review-v2/migration`](https://github.com/nscottnichols/ffmt/tree/review-v2/migration); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
