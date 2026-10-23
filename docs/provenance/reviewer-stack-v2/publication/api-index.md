The top-level README combines setup, output contracts, all optional families and research links in one dense page.

For example:

```text
#include <ffmt/base.hpp>
ffmt::println("value = {:04x}", 42);
// Follow API/build/backend/conformance guides for the corresponding detail.
```

Keep one short entry page and move detailed output/customization/configuration contracts into a linked API guide. Feature guides remain with their implementations; build and conformance pages use the actual split test names. Readers follow focused pages for detail. Documentation describes supported contracts and sampled tests rather than implying universal backend or fmt conformance.

Read in this order:

- [README.md](https://github.com/nscottnichols/ffmt/blob/77df1adccd0448a46e73af6be2af9c5a2efbc1ee/README.md)
- [docs/API.md](https://github.com/nscottnichols/ffmt/blob/77df1adccd0448a46e73af6be2af9c5a2efbc1ee/docs/API.md)
- [docs/BUILD.md](https://github.com/nscottnichols/ffmt/blob/77df1adccd0448a46e73af6be2af9c5a2efbc1ee/docs/BUILD.md)
- [docs/BACKENDS.md](https://github.com/nscottnichols/ffmt/blob/77df1adccd0448a46e73af6be2af9c5a2efbc1ee/docs/BACKENDS.md)
- [docs/CONFORMANCE.md](https://github.com/nscottnichols/ffmt/blob/77df1adccd0448a46e73af6be2af9c5a2efbc1ee/docs/CONFORMANCE.md)

Validated this exact commit on allocated CPU node `skylake10` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 7 recorded steps passed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
python3 "$FFMT_CHECKOUT"/../ffmt-evaluation/tools/review_stack/check_links.py .
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 13; it remains draft until prerequisite human review.

Base: [`review-v2/base-api-index`](https://github.com/nscottnichols/ffmt/tree/review-v2/base-api-index); 9 logical prerequisites. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
