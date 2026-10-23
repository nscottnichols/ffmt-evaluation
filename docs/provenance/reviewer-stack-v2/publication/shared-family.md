Optional formatters need consistent nested alignment without buffering or replaying mutations.

For example:

```text
// Internal support, used by optional formatter headers:
return ffmt::detail::family_padded(ctx, spec, [&](auto& body) {
  ffmt::detail::family_ascii(body, "body");
}, /* replayable = */ false);
```

Extend bounded sink iterators with padding marks/reordering and delegate hooks, then share family outer parsing and one-pass accounting. Streaming destinations explicitly require replayable values for right/center alignment. The internal helpers share outer alignment parsing, display-column accounting,
debug defaults and nested formatting. Left-aligned output renders once on any
iterator. Bounded writable pointer buffers also support right/center alignment
in one pass by inserting padding while retaining the exact truncated prefix.
Other iterators require replayable values for right/center alignment; unknown
custom formatters and consuming ranges return `unsupported_type` before invoking
the formatter. These helpers are implementation details, not a public extension
API. Optional formatters should document which input operations are device callable.

Read in this order:

- [include/ffmt/detail/output.hpp](https://github.com/nscottnichols/ffmt/blob/c325e8408f512f38861f56983a7ec9b748290118/include/ffmt/detail/output.hpp) — bounded padding and sink delegation hooks
- [include/ffmt/detail/family.hpp](https://github.com/nscottnichols/ffmt/blob/c325e8408f512f38861f56983a7ec9b748290118/include/ffmt/detail/family.hpp)
- [test/conformance/test_family_support.cpp](https://github.com/nscottnichols/ffmt/blob/c325e8408f512f38861f56983a7ec9b748290118/test/conformance/test_family_support.cpp)

Validated this exact commit on allocated CPU node `cpl00` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. The affected Make suites used the same compiler profiles. 10 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
make -j2 build/cap_family_support CXX="$CXX" FMT_DIR="$FMT_DIR" HOST_OPT="$HOST_OPT" EXTRA_CXXFLAGS="$EXTRA_CXXFLAGS"
./build/cap_family_support
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 7; it remains draft until prerequisite human review.

Base: [`review-v2/migration`](https://github.com/nscottnichols/ffmt/tree/review-v2/migration); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
