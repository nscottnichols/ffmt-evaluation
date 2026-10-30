Portable runner output, profile data and local installations must not be added accidentally when editing the library.

For example:

```text
python3 tools/conformance.py ... # artifacts/ stays untracked
```

Restore the narrow directory and suffix ignores from the retained library snapshot. Ignored output must be captured deliberately by an evaluation workflow when it serves as evidence.

Read in this order:

- [.gitignore](https://github.com/nscottnichols/ffmt/blob/c90c80e02ea7e070211693d329a7aaed21f7c089/.gitignore)
- [docs/contributing/LOCAL_OUTPUTS.md](https://github.com/nscottnichols/ffmt/blob/c90c80e02ea7e070211693d329a7aaed21f7c089/docs/contributing/LOCAL_OUTPUTS.md)

Validated this exact commit on allocated CPU node `skylake10` (`x86_64`). Header probes used Clang 22 at `-O0` with ASan/UBSan; GCC 13 at `-O2`. 4 recorded steps passed; 2 probes were inapplicable before their header existed.

Representative validation commands (`CXX` is the selected compiler, `FMT_DIR` is the clean pinned oracle, `OUT` is a fresh evidence directory, and `FFMT_CHECKOUT` is this library checkout). The commands show the Clang row; the evidence also retains the GCC probes and affected suites:

```sh
export CXX=/soft/compilers/llvm/release-22.1.8/bin/clang++
export HOST_OPT=-O0
export EXTRA_CXXFLAGS='-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer'
printf '#include <ffmt/base.hpp>\n' > base-header-probe.cpp
"$CXX" -std=c++20 "$HOST_OPT" -fno-fast-math -Wall -Werror -Iinclude $EXTRA_CXXFLAGS -c base-header-probe.cpp -o base-header-probe.o
```

The linked evidence retains complete argv, flags, source hashes and raw results. Standalone drivers and CMake use their own recorded flags; sanitizer coverage above applies to header probes and affected Make suites. This is representative host validation, not exhaustive fmt compatibility. Preserved hardware measurements retain their original revisions; no hardware campaign was repeated.

---
Draft review wave 2; it remains draft until prerequisite human review.

Base: [`review-v2/build-registration`](https://github.com/nscottnichols/ffmt/tree/review-v2/build-registration); 1 logical prerequisite. [Stack overview, evidence and old→new snapshot mapping](https://github.com/nscottnichols/ffmt-evaluation/blob/evaluation-campaign/docs/provenance/reviewer-stack-v2.md).
